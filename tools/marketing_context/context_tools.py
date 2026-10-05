"""Read-only Marketing recipe context. GitHub is a crosswalk, wxDI is authoritative."""
import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Dict, List

import requests
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.agent_builder.connections import ConnectionType, ExpectedCredentials
from ibm_watsonx_orchestrate.run import connections

REPOSITORY = 'gprzybycien/digital-data-consumer'
MAPPING_PATH = 'context/marketing/mapping.json'
MAPPING_COMMIT = 'f18abf52283f102c9eb6ae805d3c0f971d91a123'
MAPPING_SHA256 = '26be966df24f0df7b4ecaddb2dbe2954111d0ce423d5327e3d7c9092a07e3acc'
CREDENTIALS = [ExpectedCredentials(app_id='github_snapshot_creds', type=ConnectionType.KEY_VALUE)]


def _validate(mapping):
    if mapping.get('schema_version') != '1.0' or mapping.get('status') != 'active':
        raise ValueError('Mapping is not an active supported revision.')
    if mapping['glossary_scope']['include_subcategories'] is not False:
        raise ValueError('This release supports the flat Marketing DPH category only.')
    names = set(mapping['terms'])
    assets = mapping['assignment_workaround']['assets']
    asset_names = {a['name'] for a in assets}
    if len(asset_names) != len(assets) or len(asset_names) != 5:
        raise ValueError('Expected five distinct product assets.')
    all_columns = [(a['name'], c['column']) for a in assets for c in a['columns']]
    if len(all_columns) != 29 or len(set(all_columns)) != 29:
        raise ValueError('Expected 29 distinct column bindings.')
    known_ids = {t['id'] for t in mapping['terms'].values()}
    for a in assets:
        for c in a['columns']:
            if len(c['assigned']) != 1 or c['assigned'][0]['id'] not in known_ids:
                raise ValueError('Unresolved column-term reference.')
    if len({u['id'] for u in mapping['use_cases']}) != len(mapping['use_cases']):
        raise ValueError('Duplicate recipe ID.')
    for u in mapping['use_cases']:
        if not set(u['term_names']) <= names or not set(u['assets']) <= asset_names:
            raise ValueError('Unresolved recipe reference.')
    return mapping


def _load():
    creds = connections.key_value('github_snapshot_creds')
    token = creds.get('access_token') or creds.get('token')
    if not token:
        raise ValueError('Existing github_snapshot_creds connection has no token.')
    if not re.fullmatch(r'[0-9a-f]{40}', MAPPING_COMMIT):
        raise ValueError('Tool release has no pinned mapping commit.')
    response = requests.get(
        f'https://api.github.com/repos/{REPOSITORY}/contents/{MAPPING_PATH}',
        params={'ref': MAPPING_COMMIT},
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28'}, timeout=30)
    if response.status_code != 200:
        raise ValueError(f'GitHub context read failed (HTTP {response.status_code}).')
    if len(response.content) > 1048576:
        raise ValueError('Context response exceeds size limit.')
    envelope = response.json()
    if envelope.get('encoding') != 'base64':
        raise ValueError('Unsupported GitHub content encoding.')
    content = base64.b64decode(envelope['content'])
    if hashlib.sha256(content).hexdigest() != MAPPING_SHA256:
        raise ValueError('Context digest does not match the pinned release.')
    return _validate(json.loads(content))


def _provenance():
    return {'mapping_commit': MAPPING_COMMIT, 'mapping_sha256': MAPPING_SHA256,
            'mapping_url': f'https://github.com/{REPOSITORY}/blob/{MAPPING_COMMIT}/{MAPPING_PATH}',
            'context_retrieved_at': datetime.now(timezone.utc).isoformat(),
            'authority': 'curated_crosswalk; live wxDI state must be checked'}


def _error(exc):
    message = str(exc) if isinstance(exc, ValueError) else 'Context unavailable; do not infer absent products or terms.'
    return {'success': False, 'error': message, **_provenance()}


def _recipe(mapping, use_case_id):
    return next((u for u in mapping['use_cases'] if u['id'] == use_case_id), None)


@tool(permission=ToolPermission.READ_ONLY, expected_credentials=CREDENTIALS)
def search_use_case_context(domain: str, intent: str, limit: int = 5) -> Dict:
    """Find curated Marketing analyses, industry alignment and limitations, without subscribing or querying data. Context is read from a pinned GitHub revision using the existing connection."""
    try:
        mapping = _load()
        if domain.casefold().strip() not in ('marketing', 'performance marketing'):
            return {'success': True, 'use_cases': [], 'coverage': 'Only Marketing is curated.', **_provenance()}
        if limit < 1 or limit > 5:
            raise ValueError('limit must be between 1 and 5.')
        query = intent.casefold()
        ranked = sorted(mapping['use_cases'], key=lambda u: (-sum(k in query for k in u['keywords']), u['id']))
        return {'success': True, 'glossary_scope': mapping['glossary_scope'], 'domain': mapping['domain'],
                'industry_reference': mapping['industry_reference'], 'candidate_product': mapping['product'],
                'use_cases': [{k: u[k] for k in ('id', 'name', 'industry_process_ids', 'term_names', 'measure_names', 'assets', 'time_basis', 'limitations')} for u in ranked[:limit]],
                'verification_required': True, 'current_state_verified': False, 'required_next_step': 'read_use_case_context, live wxDI product/glossary/asset reads, then verify_use_case_context before claims of current availability or assignments', 'gaps': mapping['gaps'], 'relationship_evidence': {**mapping['relationship_evidence'], 'column_term_assignments': 'historical_snapshot_not_live_verified'}, **_provenance()}
    except (ValueError, KeyError, TypeError, requests.RequestException):
        return _error(ValueError('Could not read or validate the pinned context. No live availability established.'))


@tool(permission=ToolPermission.READ_ONLY, expected_credentials=CREDENTIALS)
def read_use_case_context(use_case_id: str) -> Dict:
    """Read a Marketing recipe with exact product, asset, glossary IDs and a temporary verified column-assignment snapshot. Retrieve live wxDI definitions and product metadata before using it."""
    try:
        mapping = _load()
        recipe = _recipe(mapping, use_case_id)
        if recipe is None:
            raise ValueError('Unknown Marketing use-case ID.')
        return {'success': True, 'use_case': recipe, 'product': mapping['product'],
                'terms': {name: mapping['terms'][name] for name in recipe['term_names']},
                'glossary_scope': mapping['glossary_scope'], 'domain': mapping['domain'],
                'industry_reference': mapping['industry_reference'],
                'assignment_workaround': {**{k: v for k, v in mapping['assignment_workaround'].items() if k != 'assets'},
                    'assets': [a for a in mapping['assignment_workaround']['assets'] if a['name'] in recipe['assets']]},
                'relationship_evidence': {**mapping['relationship_evidence'], 'column_term_assignments': 'historical_snapshot_not_live_verified'}, **_provenance()}
    except (ValueError, KeyError, TypeError, requests.RequestException) as exc:
        return _error(exc)


@tool(permission=ToolPermission.READ_ONLY, expected_credentials=CREDENTIALS)
def verify_use_case_context(use_case_id: str, live_product_details: Dict, live_glossary_rows: List[Dict], live_asset_details: List[Dict]) -> Dict:
    """Compare actual wxDI tool results against pinned context. Pass get_data_product_details payload, run_gs_query rows, and relevant get_asset_details payloads. These inputs must come from successful live calls, never fabricated. Reports drift; does not verify subscriptions, contracts, metric results or SQL eligibility."""
    try:
        mapping = _load()
        recipe = _recipe(mapping, use_case_id)
        if recipe is None:
            raise ValueError('Unknown Marketing use-case ID.')
        product = mapping['product']
        details = live_product_details.get('data_product_details', {})
        checks = []
        same_version = (live_product_details.get('success') is True and
                        details.get('id', '').split('@')[0] == product['version_id'] and
                        details.get('version') == product['version'] and details.get('state') == 'available')
        checks.append({'check': 'exact_published_product_version', 'status': 'verified' if same_version else 'failed'})
        live_parts = {p['name']: p for p in details.get('parts_out', [])}
        raw_assets = {a.get('asset_id'): a for a in live_asset_details if a.get('success') is True}
        term_rows = {r.get('entity', {}).get('artifacts', {}).get('global_id'): r for r in live_glossary_rows}
        live_term_ids = set()
        for name in recipe['term_names']:
            expected = mapping['terms'][name]
            row = term_rows.get(expected['id'], {})
            metadata = row.get('metadata', {})
            state_ok = metadata.get('state') == 'PUBLISHED'
            definition_ok = hashlib.sha256(metadata.get('description', '').encode()).hexdigest() == expected['definition_sha256']
            revision_ok = row.get('entity', {}).get('artifacts', {}).get('version_id') == expected['revision_id']
            category_ok = row.get('categories', {}).get('primary_category_id') == mapping['glossary_scope']['category_id']
            ok = state_ok and definition_ok and revision_ok and category_ok
            if ok:
                live_term_ids.add(expected['id'])
            checks.append({'check': 'published_term_revision', 'term': name, 'id': expected['id'], 'status': 'verified' if ok else 'failed'})
        snapshot = []
        for asset in mapping['assignment_workaround']['assets']:
            if asset['name'] not in recipe['assets']:
                continue
            part = live_parts.get(asset['name'], {})
            part_id = part.get('asset', {}).get('id')
            container_id = part.get('asset', {}).get('container', {}).get('id')
            schema_ok = {c['name'] for c in part.get('columns', [])} == {c['column'] for c in asset['columns']}
            identity_ok = same_version and part_id == asset['id'] and container_id == product['catalog_id'] and schema_ok
            checks.append({'check': 'exact_asset_and_columns', 'asset': asset['name'], 'status': 'verified' if identity_ok else 'failed'})
            raw = raw_assets.get(asset['id'], {})
            raw_ok = identity_ok and raw.get('catalog_id') == product['catalog_id']
            part_cols = {c['name']: c for c in part.get('columns', [])}
            for c in asset['columns']:
                # Prefer native product-tool assignments as soon as they become available.
                native = part_cols.get(c['column'], {}).get('column_info') or {}
                native_terms = native.get('column_terms')
                if identity_ok and isinstance(native_terms, list):
                    assigned = native_terms
                    source = 'get_data_product_details'
                elif raw_ok:
                    assigned = raw.get('entity', {}).get('column_info', {}).get(c['column'], {}).get('column_terms', [])
                    source = 'get_asset_details_workaround'
                else:
                    assigned = None
                    source = 'verified_snapshot_only'
                expected_ids = {t['id'] for t in c['assigned']}
                if assigned is not None:
                    ok = {t.get('term_id') for t in assigned} == expected_ids
                    status = 'verified' if ok else 'failed'
                else:
                    status = 'snapshot_only' if identity_ok else 'failed'
                checks.append({'check': 'column_term_assignment', 'asset': asset['name'], 'column': c['column'], 'status': status, 'source': source})
                if status == 'snapshot_only':
                    snapshot.append({'asset': asset['name'], **c})
        ready = bool(checks) and all(c['status'] == 'verified' for c in checks)
        return {'success': True, 'discovery_verified': ready, 'checks': checks,
                'verified_snapshot_fallback': snapshot, 'snapshot_verified_at': mapping['assignment_workaround']['verified_at'],
                'formal_glossary_relationships': 'unverified',
                'not_verified': ['contract semantics and asset bindings', 'metric results', 'subscription and query access', 'domain parent hierarchy', 'APQC edition'],
                'removal_condition': mapping['assignment_workaround']['removal_condition'], **_provenance()}
    except (ValueError, KeyError, TypeError, requests.RequestException) as exc:
        return _error(exc)
