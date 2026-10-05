"""Deterministic wxDI evidence collection: never let chat rewrite query or payloads."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END


class Request(BaseModel):
    use_case_id: str


class Response(BaseModel):
    verification: Dict
    context: Dict
    glossary: Dict
    product: Dict
    contract: Dict


class AnyOutput(BaseModel):
    model_config = ConfigDict(extra='allow')


class ProductArgs(BaseModel):
    data_product_version_id: str


class ContractArgs(ProductArgs):
    data_product_state: str


class GlossaryArgs(BaseModel):
    auth_scope: str
    gs_query: str


class AssetArgs(BaseModel):
    asset: str
    catalog: str
    project: str = ''


class VerifyArgs(Request):
    live_product_details: Dict
    live_glossary_rows: List[Dict]
    live_asset_details: List[Dict]


@flow(name='verify_marketing_use_case_live', input_schema=Request, output_schema=Response,
      suppress_agent_summarization=False)
def verify_marketing_use_case_live(aflow: Flow) -> Flow:
    """Collect exact live product, contract, glossary and column assignments for a Marketing recipe and verify them. Use this metadata-only flow instead of manually calling or copying verification inputs. Never subscribes or runs SQL."""
    mapping = json.loads((Path(__file__).resolve().parents[2]/'context/marketing/mapping.json').read_text())
    context = aflow.tool('read_use_case_context', name='recipe_context', input_schema=Request, output_schema=AnyOutput)
    context.map_input('use_case_id', 'flow.input.use_case_id')
    product = aflow.tool('wxdi_consumer:get_data_product_details', name='product', input_schema=ProductArgs, output_schema=AnyOutput)
    product.map_input('data_product_version_id', 'flow.recipe_context.output.product.version_id')
    contract = aflow.tool('wxdi_consumer:get_data_product_contract', name='contract', input_schema=ContractArgs, output_schema=AnyOutput)
    contract.map_input('data_product_version_id', 'flow.recipe_context.output.product.version_id')
    contract.map_input('data_product_state', repr('available'))
    glossary = aflow.tool('wxdi_consumer:run_gs_query', name='glossary', input_schema=GlossaryArgs, output_schema=AnyOutput)
    glossary.map_input('auth_scope', 'flow.recipe_context.output.live_glossary_query_arguments.auth_scope')
    glossary.map_input('gs_query', 'flow.recipe_context.output.live_glossary_query_arguments.gs_query')
    assets = []
    for item in mapping['assignment_workaround']['assets']:
        node = aflow.tool('wxdi_consumer:get_asset_details', name='asset_'+item['name'], input_schema=AssetArgs, output_schema=AnyOutput)
        node.map_input('asset', repr(item['id']))
        node.map_input('catalog', repr(mapping['product']['catalog_id']))
        node.map_input('project', repr(''))
        assets.append(node)
    verify = aflow.tool('verify_use_case_context', name='verify', input_schema=VerifyArgs, output_schema=AnyOutput)
    verify.map_input('use_case_id', 'flow.input.use_case_id')
    verify.map_input('live_product_details', 'flow.product.output')
    verify.map_input('live_glossary_rows', 'flow.glossary.output.rows')
    verify.map_input('live_asset_details', '['+', '.join('flow.asset_'+a['name']+'.output' for a in mapping['assignment_workaround']['assets'])+']')
    aflow.sequence(START, context, product, contract, glossary, *assets, verify, END)
    for field in ['verification', 'context', 'glossary', 'product', 'contract']:
        node = 'verify' if field == 'verification' else 'recipe_context' if field == 'context' else field
        aflow.map_output(field, 'flow.'+node+'.output')
    return aflow
