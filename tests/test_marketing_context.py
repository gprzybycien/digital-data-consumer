import copy
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('marketing_context_tools', ROOT/'tools/marketing_context/context_tools.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def invoke(name, *args, **kwargs):
    decorated = getattr(module, name)
    return decorated.fn(*args, **kwargs)


class MarketingContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = json.loads((ROOT/'context/marketing/mapping.json').read_text())
        # Portable synthetic payloads: no private audit exports or glossary definitions.
        cls.runtime_mapping = copy.deepcopy(cls.mapping)
        cls.rows = []
        for name, term in cls.runtime_mapping['terms'].items():
            definition = 'Synthetic test definition for ' + name
            term['definition_sha256'] = hashlib.sha256(definition.encode()).hexdigest()
            cls.rows.append({'metadata': {'state': 'PUBLISHED', 'description': definition},
                             'entity': {'artifacts': {'global_id': term['id'], 'version_id': term['revision_id']}},
                             'categories': {'primary_category_id': cls.mapping['glossary_scope']['category_id']}})
        cls.product = {'success': True, 'data_product_details': {
            'id': cls.mapping['product']['version_id'], 'version': cls.mapping['product']['version'],
            'state': 'available', 'parts_out': [
                {'name': a['name'], 'asset': {'id': a['id'], 'container': {'id': cls.mapping['product']['catalog_id']}},
                 'columns': [{'name': c['column'], 'column_info': {}} for c in a['columns']]}
                for a in cls.mapping['assignment_workaround']['assets']]}}
        cls.assets = [{'success': True, 'asset_id': a['id'], 'catalog_id': cls.mapping['product']['catalog_id'], 'entity': {'column_info': {c['column']: {'column_terms': [{'term_id': t['id']} for t in c['assigned']]} for c in a['columns']}}} for a in cls.mapping['assignment_workaround']['assets']]

    def verify(self, product=None, rows=None, assets=None):
        with patch.object(module, '_load', return_value=self.runtime_mapping):
            return invoke('verify_use_case_context', 'campaign_engagement', product or self.product, self.rows if rows is None else rows, self.assets if assets is None else assets)

    def test_schema_and_references(self):
        jsonschema.validate(self.mapping, json.loads((ROOT/'context/schema/context-mapping.schema.json').read_text()))
        module._validate(self.mapping)

    def test_live_assignments_verify(self):
        result=self.verify()
        self.assertTrue(result['discovery_verified'])
        self.assertIn('get_asset_details_workaround', {c.get('source') for c in result['checks']})
        self.assertEqual('unverified', result['formal_glossary_relationships'])

    def test_changed_version_rejects_snapshot(self):
        product=copy.deepcopy(self.product);product['data_product_details']['version']='99.0.0'
        result=self.verify(product=product,assets=[])
        self.assertFalse(result['discovery_verified']);self.assertEqual([],result['verified_snapshot_fallback'])

    def test_missing_live_assets_never_passes(self):
        result=self.verify(assets=[])
        self.assertFalse(result['discovery_verified'])
        self.assertTrue(result['verified_snapshot_fallback'])
        self.assertIn('snapshot_only',{c['status'] for c in result['checks']})

    def test_wrong_live_assignment_fails(self):
        assets=copy.deepcopy(self.assets)
        for a in assets:
            if 'cmp_id' in a['entity']['column_info']:
                a['entity']['column_info']['cmp_id']['column_terms']=[{'term_id':'wrong-identifier'}]
        self.assertFalse(self.verify(assets=assets)['discovery_verified'])

    def test_glossary_revision_or_definition_drift_fails(self):
        rows=copy.deepcopy(self.rows)
        for r in rows:r['metadata']['description']+=' changed'
        self.assertFalse(self.verify(rows=rows)['discovery_verified'])

    def test_native_terms_replace_extra_asset_reads(self):
        product=copy.deepcopy(self.product)
        snapshot={a['name']:a for a in self.mapping['assignment_workaround']['assets']}
        for part in product['data_product_details']['parts_out']:
            columns={c['column']:c for c in snapshot[part['name']]['columns']}
            for c in part['columns']:
                c['column_info']['column_terms']=[{'term_id':t['id']} for t in columns[c['name']]['assigned']]
        result=self.verify(product=product,assets=[])
        self.assertTrue(result['discovery_verified'])
        self.assertEqual({'get_data_product_details'},{c.get('source') for c in result['checks'] if c['check']=='column_term_assignment'})

    def test_starter_and_read_only_routing(self):
        agent=yaml.safe_load((ROOT/'agent/wxdi-data-consumer.yaml').read_text())
        self.assertEqual(3,len(agent['starter_prompts']['prompts']))
        self.assertEqual('discover_marketing',agent['starter_prompts']['prompts'][0]['id'])
        self.assertLess(agent['instructions'].index('UNDERSTAND:'),agent['instructions'].index('AUTOMATIC SUBSCRIPTION RESOLUTION FOR DATA QUESTIONS'))
        self.assertIn('wxdi_consumer:get_asset_details',agent['tools'])
        self.assertIn('wxdi_consumer:run_gs_query',agent['tools'])

    def test_search_cannot_establish_current_state(self):
        with patch.object(module, '_load', return_value=self.mapping):
            result = invoke('search_use_case_context', 'Marketing', 'campaign engagement')
        self.assertFalse(result['current_state_verified'])
        self.assertTrue(result['verification_required'])
        self.assertEqual('historical_snapshot_not_live_verified', result['relationship_evidence']['column_term_assignments'])

    def test_generated_glossary_query_roundtrips(self):
        with patch.object(module, '_load', return_value=self.mapping):
            result = invoke('read_use_case_context', 'campaign_engagement')
        args = result['live_glossary_query_arguments']
        query = json.loads(args['gs_query'])
        self.assertEqual('category', args['auth_scope'])
        self.assertEqual(200, query['size'])
        self.assertEqual(self.mapping['glossary_scope']['category_id'], query['query']['bool']['filter'][1]['term']['categories.primary_category_id'])
        self.assertEqual(self.mapping['product']['version_id'], result['live_contract_arguments']['data_product_version_id'])
        self.assertEqual('available', result['live_contract_arguments']['data_product_state'])

    def test_summarized_product_payload_is_rejected(self):
        result = self.verify(product={'id': self.mapping['product']['version_id'], 'state': 'available'})
        self.assertFalse(result['success'])
        self.assertIn('complete', result['error'])

    def test_flow_preserves_payloads_without_language_model_nodes(self):
        source = (ROOT/'tools/marketing_context/verify_live_flow.py').read_text()
        tree = ast.parse(source)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertFalse(any(n.func.attr in ('agent', 'prompt', 'llm') for n in calls))
        for node in calls:
            if node.func.attr == 'tool':
                self.assertIn('input_schema', {kw.arg for kw in node.keywords})
                for kw in node.keywords:
                    if kw.arg == 'name' and isinstance(kw.value, ast.Constant):
                        self.assertNotIn(kw.value.value, ('context', 'input', 'output', 'private'))
        self.assertIn("'flow.product.output'", source)
        self.assertIn("'flow.glossary.output.rows'", source)

    def test_flow_data_envelopes_preserve_live_verification(self):
        result = self.verify(product={'data': self.product}, assets=[{'data': a} for a in self.assets])
        self.assertTrue(result['discovery_verified'])

    def test_unknown_recipe_fails(self):
        with patch.object(module,'_load',return_value=self.mapping):
            self.assertFalse(invoke('read_use_case_context','unknown')['success'])

if __name__=='__main__':unittest.main()
