"""Grounded Engagement query drafts. No network or SQL execution."""
import ast,json
from typing import Dict
from ibm_watsonx_orchestrate.agent_builder.tools import tool,ToolPermission

def unwrap(p):
 for _ in range(3):
  if isinstance(p.get('structuredContent'),dict):p=p['structuredContent']
  elif 'success' not in p and isinstance(p.get('data'),dict):p=p['data']
  else:break
 return p

@tool(permission=ToolPermission.READ_ONLY)
def build_default_engagement_query(question: str, verification: Dict, product: Dict, contract: Dict, subscriptions: Dict) -> Dict:
 """Build an UNEXECUTED query only from verified live Engagement metadata. Reports exact-version visible subscriptions without guessing delivery or execution."""
 v,p,c,s=map(unwrap,[verification,product,contract,subscriptions])
 if not v.get('discovery_verified') or not p.get('success') or not c.get('success'):
  return {'success':False,'error':'Live semantic/product/contract checks did not pass. No grounded query available.','executed':False}
 try:odcs=json.loads(c['data_contract'])
 except (ValueError,TypeError):odcs=ast.literal_eval(c['data_contract'])
 parts={a['name']:a for a in p['data_product_details']['parts_out']};schemas={a['name']:a for a in odcs['schema']}
 paths={}
 for name,columns in [('digital_event',{'cmp_id','evt'}),('campaign',{'campaign_id','channel_code'})]:
  a=schemas[name]
  if a['asset_id']!=parts[name]['asset']['id'] or not columns<={z['name'] for z in a['properties']}:
   return {'success':False,'error':'Contract binding or required columns do not match current product.','executed':False}
  path=a['physical_name'];expected='/workspace/performance_marketing_mvp/'+name
  if path!=expected:return {'success':False,'error':'Unrecognized physical mapping; refusing to guess table.','executed':False}
  paths[name]='workspace.performance_marketing_mvp.'+name
 if question=='How many recorded clicks and impressions did each campaign generate?':
  query=f"SELECT cmp_id AS campaign_id, SUM(CASE WHEN evt = 'click' THEN 1 ELSE 0 END) AS recorded_clicks, SUM(CASE WHEN evt = 'impression' THEN 1 ELSE 0 END) AS recorded_impressions FROM {paths['digital_event']} GROUP BY cmp_id ORDER BY campaign_id LIMIT 100"
 elif question=='Which marketing channels have the most recorded clicks and impressions?':
  query=f"WITH events AS (SELECT cmp_id, SUM(CASE WHEN evt = 'click' THEN 1 ELSE 0 END) AS clicks, SUM(CASE WHEN evt = 'impression' THEN 1 ELSE 0 END) AS impressions FROM {paths['digital_event']} GROUP BY cmp_id), channels AS (SELECT campaign_id, MIN(channel_code) AS channel_code FROM {paths['campaign']} GROUP BY campaign_id HAVING COUNT(DISTINCT channel_code) = 1) SELECT c.channel_code, SUM(e.clicks) AS recorded_clicks, SUM(e.impressions) AS recorded_impressions FROM events e LEFT JOIN channels c ON e.cmp_id = c.campaign_id GROUP BY c.channel_code ORDER BY recorded_clicks DESC LIMIT 100"
 elif question=='How do recorded clicks and impressions change over time for a campaign?':
  if 'ts' not in {z['name'] for z in schemas['digital_event']['properties']}:raise ValueError('Missing event timestamp')
  query=f"SELECT cmp_id AS campaign_id, CAST(ts AS DATE) AS recorded_date, SUM(CASE WHEN evt = 'click' THEN 1 ELSE 0 END) AS recorded_clicks, SUM(CASE WHEN evt = 'impression' THEN 1 ELSE 0 END) AS recorded_impressions FROM {paths['digital_event']} GROUP BY cmp_id, CAST(ts AS DATE) ORDER BY campaign_id, recorded_date LIMIT 100"
 else:raise ValueError('Question is not a supported Engagement default.')
 version=p['data_product_details']['id'].split('@')[0]
 matches=[z for z in s.get('subscriptions',[]) if z.get('asset',{}).get('id')==version] if s.get('success') else []
 return {'success':True,'question':question,'query':query,'executed':False,'label':'UNEXECUTED query','product_version':p['data_product_details']['version'],'defaults':{'period':'all available records','limit':100,'timezone':'recorded source basis; not converted'},'subscription_search_succeeded':s.get('success') is True,'subscriptions':[{'id':z['id'],'state':z.get('state')} for z in matches],'access_note':'Inspect subscription item delivery and source SQL access before execution. Empty/failed search does not prove the user lacks a DPH subscription.','limitations':['Counts are recorded event rows; event identifier uniqueness must be validated.','Channel draft groups conflicting or unmatched campaign mappings under null; review before execution.','Trend draft uses recorded source date; timezone is unverified.']}
