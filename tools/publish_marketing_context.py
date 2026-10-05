"""Publish reviewed context using existing WxO GitHub connection; never prints credentials.
Run with the configured ADK Python. Does not change credentials or connection permissions.
"""
import base64
import hashlib
import json
from pathlib import Path

import requests
from ibm_watsonx_orchestrate.client.utils import instantiate_client
from ibm_watsonx_orchestrate.client.connections.connections_client import ConnectionsClient, ConnectionEnvironment

REPO = 'gprzybycien/digital-data-consumer'
RELEASE_FILES = [
    'context/marketing/mapping.json', 'context/marketing/README.md',
    'context/schema/context-mapping.schema.json',
    'tools/marketing_context/context_tools.py', 'tools/marketing_context/requirements.txt',
    'agent/wxdi-data-consumer.yaml', 'docs/marketing-context-implementation-plan.md',
    'docs/marketing-context-release.md', 'tests/test_marketing_context.py',
    'tools/publish_marketing_context.py',
]


def main():
    client = instantiate_client(ConnectionsClient)
    record = client.get_credentials('github_snapshot_creds', ConnectionEnvironment.DRAFT, False)
    creds = (record or {}).get('credentials_key', {})
    token = creds.get('access_token') or creds.get('token')
    if token and set(token) <= set('*•'):
        raise SystemExit('WxO administration API masks runtime credentials. Publish through a WxO runtime tool; never authenticate GitHub with this placeholder.')
    if not token:
        raise SystemExit('Existing github_snapshot_creds has no runtime token; refresh it in WxO.')
    session = requests.Session()
    session.headers.update({'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})

    def call(method, path, body=None):
        r = session.request(method, 'https://api.github.com/repos/'+REPO+path, json=body, timeout=30)
        if not r.ok:
            raise SystemExit(f'GitHub {method} failed (HTTP {r.status_code}); no credentials logged. Check existing WxO connection.')
        return r.json()

    repo = call('GET','')
    branch = repo['default_branch']
    head = call('GET','/git/ref/heads/'+branch)['object']['sha']
    base = call('GET','/git/commits/'+head)['tree']['sha']
    # A single commit updates only these reviewed files; existing repository content is preserved.
    entries=[]
    for filename in RELEASE_FILES:
        content=Path(filename).read_bytes()
        blob=call('POST','/git/blobs',{'encoding':'base64','content':base64.b64encode(content).decode()})
        entries.append({'path':filename,'mode':'100644','type':'blob','sha':blob['sha']})
    tree=call('POST','/git/trees',{'base_tree':base,'tree':entries})
    commit=call('POST','/git/commits',{'message':'Add Marketing semantic discovery context and temporary column-term workaround','tree':tree['sha'],'parents':[head]})
    call('PATCH','/git/refs/heads/'+branch,{'sha':commit['sha'],'force':False})
    sha=commit['sha'];digest=hashlib.sha256(Path('context/marketing/mapping.json').read_bytes()).hexdigest()
    check=call('GET','/contents/context/marketing/mapping.json?ref='+sha)
    if hashlib.sha256(base64.b64decode(check['content'])).hexdigest()!=digest:
        raise SystemExit('Published mapping readback mismatch; do not deploy.')
    path=Path('tools/marketing_context/context_tools.py')
    code=path.read_text()
    import re
    code=re.sub(r"MAPPING_COMMIT = '[^']+'",f"MAPPING_COMMIT = '{sha}'",code)
    code=re.sub(r"MAPPING_SHA256 = '[^']+'",f"MAPPING_SHA256 = '{digest}'",code)
    path.write_text(code)
    # Store the pinned release tool in a follow-up commit; its mapping stays bound to sha.
    remote=call('GET','/contents/'+str(path)+'?ref='+branch)
    call('PUT','/contents/'+str(path),{'message':'Pin Marketing context tools to verified mapping commit','sha':remote['sha'],'branch':branch,'content':base64.b64encode(code.encode()).decode()})
    evidence={'repository':REPO,'mapping_commit':sha,'mapping_sha256':digest,'branch':branch,'mapping_readback_verified':True,'connection':'github_snapshot_creds'}
    Path('context/marketing/release-binding.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence))

if __name__=='__main__':main()
