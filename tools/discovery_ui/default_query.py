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

@tool(permission=ToolPermission.READ_ONLY)
def select_existing_engagement_subscription(draft: Dict) -> Dict:
 """Select only an exact-version succeeded subscription from the grounded live draft; never create access."""
 d=unwrap(draft)
 if not d.get('success') or not d.get('subscription_search_succeeded'):
  raise ValueError('Live subscription search or semantic verification failed; access is unknown.')
 ids=sorted(x['id'] for x in d.get('subscriptions',[]) if str(x.get('state','')).lower() in ('succeeded','delivered'))
 if not ids:raise ValueError('No delivered exact-version subscription visible to this connection; reconcile identity/version before requesting new access.')
 return {'subscription_id':ids[0]}

@tool(permission=ToolPermission.READ_ONLY)
def authorize_delivered_engagement_query(draft: Dict, delivery: Dict, product: Dict) -> Dict:
 """Require delivered original assets and exact source descriptors before returning grounded read-only SQL."""
 d,v,p=map(unwrap,[draft,delivery,product])
 if not d.get('success') or not v.get('success'):raise ValueError('Cannot verify delivered subscription items.')
 parts={x['name']:x['asset']['id'] for x in p['data_product_details']['parts_out']}
 required=d.get('required_assets', ['digital_event','campaign'])
 for name in required:
  items=[x for x in v.get('items',[]) if x.get('asset',{}).get('id')==parts[name]]
  valid=False
  for x in items:
   props=x.get('properties') or {}
   state=props.get('data_product_delivery_state') or x.get('state')
   if state not in ('delivered','succeeded'):continue
   for descriptors in (props.get('output') or {}).values():
    if not isinstance(descriptors,list):continue
    fields={r.get('key'):r.get('value') for r in descriptors}
    if [fields.get(k) for k in ('catalog','schema','table')]==['workspace','performance_marketing_mvp',name]:valid=True
  if not valid:raise ValueError('Delivered original asset/source mapping is not verified: '+name)
 query=d['query']
 if not query.startswith(('SELECT ','WITH ')) or ';' in query:raise ValueError('Invalid read-only query.')
 return {'query':query}

@tool(permission=ToolPermission.READ_ONLY)
def summarize_executed_engagement_answer(draft: Dict, result: Dict, subscription: Dict) -> Dict:
 """Return compact actual execution evidence; never label an executed query as unexecuted."""
 d,r,s=map(unwrap,[draft,result,subscription])
 state=(r.get('status') or {}).get('state','UNKNOWN')
 return {'question':d['question'],'product_version':d['product_version'],'defaults':d['defaults'],'query':d['query'],'subscription_id':s['subscription_id'],'execution_state':state,'executed':state=='SUCCEEDED','statement_id':r.get('statement_id'),'result':r,'limitations':d.get('limitations',[]),'instruction':'Answer with the actual returned rows when SUCCEEDED. If PENDING or RUNNING, poll the statement_id. Never ask to run a query already submitted. If failed, report the actual SQL error.'}

QUESTION_RECIPES = {
 'What is the planned budget for each campaign?':'planned_budgets',
 'Which campaigns have the largest planned budgets?':'planned_budgets',
 'What are the planned budgets and scheduled dates by marketing channel?':'planned_budgets',
 'How many bookings and paid bookings does each campaign have?':'paid_booking_performance',
 'How do daily booking counts and paid amounts compare by conversion cohort?':'daily_booking_cohorts',
 'How much recorded paid-booking amount is associated with each campaign?':'paid_booking_performance',
 'How many distinct converters currently have recorded marketing opt-in?':'current_opt_in_converters',
 'How does current opt-in among converters vary by campaign?':'current_opt_in_converters',
 'How many recorded clicks and impressions did each campaign generate?':'campaign_engagement',
 'Which marketing channels have the most recorded clicks and impressions?':'campaign_engagement',
 'How do recorded clicks and impressions change over time for a campaign?':'campaign_engagement',
}

@tool(permission=ToolPermission.READ_ONLY)
def resolve_marketing_question(choice: str) -> Dict:
 """Resolve a supported calculation to its exact governed recipe, without SQL or subscription creation."""
 if choice not in QUESTION_RECIPES:raise ValueError('Unsupported calculation. Concept explanation does not execute SQL.')
 return {'use_case_id':QUESTION_RECIPES[choice]}

@tool(permission=ToolPermission.READ_ONLY)
def build_default_marketing_query(question: str, verification: Dict, product: Dict, contract: Dict, subscriptions: Dict) -> Dict:
 """Build a bounded Marketing default from verified recipe and exact live contract bindings. Never produces sample data."""
 recipe=resolve_marketing_question.fn(question)['use_case_id']
 if recipe=='campaign_engagement':
  d=build_default_engagement_query.fn(question,verification,product,contract,subscriptions)
  d['required_assets']=['digital_event','campaign'];return d
 v,p,c,s=map(unwrap,[verification,product,contract,subscriptions])
 if not v.get('discovery_verified') or not p.get('success') or not c.get('success'):raise ValueError('Live semantic/product/contract verification failed.')
 try:odcs=json.loads(c['data_contract'])
 except (ValueError,TypeError):odcs=ast.literal_eval(c['data_contract'])
 parts={a['name']:a for a in p['data_product_details']['parts_out']};schemas={a['name']:a for a in odcs['schema']}
 t='workspace.performance_marketing_mvp.'
 budget='campaign_id, campaign_name, channel_code, planned_budget, start_date, end_date'
 queries={
 'What is the planned budget for each campaign?':('campaign',{'campaign_id','campaign_name','channel_code','planned_budget','start_date','end_date'},f'SELECT {budget} FROM {t}campaign ORDER BY campaign_id LIMIT 100'),
 'Which campaigns have the largest planned budgets?':('campaign',{'campaign_id','campaign_name','channel_code','planned_budget','start_date','end_date'},f'SELECT {budget} FROM {t}campaign ORDER BY planned_budget DESC NULLS LAST, campaign_id LIMIT 100'),
 'What are the planned budgets and scheduled dates by marketing channel?':('campaign',{'campaign_id','campaign_name','channel_code','planned_budget','start_date','end_date'},f'SELECT {budget} FROM {t}campaign ORDER BY channel_code, start_date, campaign_id LIMIT 100'),
 'How many bookings and paid bookings does each campaign have?':('booking_conversion',{'cmp_id','conversion_id','payment_completed_ts'},f'SELECT cmp_id AS campaign_id, COUNT(DISTINCT conversion_id) AS bookings, COUNT(DISTINCT CASE WHEN payment_completed_ts IS NOT NULL THEN conversion_id END) AS paid_bookings FROM {t}booking_conversion GROUP BY cmp_id ORDER BY bookings DESC, campaign_id LIMIT 100'),
 'How do daily booking counts and paid amounts compare by conversion cohort?':('campaign_daily_performance',{'campaign_id','campaign_name','performance_date','conversions','confirmed_revenue'},f'SELECT campaign_id, campaign_name, performance_date AS conversion_cohort_date, conversions AS booking_count, confirmed_revenue AS recorded_paid_amount FROM {t}campaign_daily_performance WHERE performance_date IS NOT NULL ORDER BY performance_date, campaign_id LIMIT 100'),
 'How much recorded paid-booking amount is associated with each campaign?':('booking_conversion',{'cmp_id','conversion_id','payment_completed_ts','revenue_amount'},f'SELECT cmp_id AS campaign_id, conversion_id, revenue_amount AS recorded_paid_booking_amount FROM {t}booking_conversion WHERE payment_completed_ts IS NOT NULL ORDER BY cmp_id, conversion_id LIMIT 100'),
 }
 limitations=[]
 if question in queries:
  name,cols,query=queries[question];required={name:cols}
  if recipe=='planned_budgets':limitations=['Recorded numeric budget values only; currency is unverified, so ranking is not a verified comparison of monetary value. Planned budget is not actual spend or ROI.']
  elif 'amount' in question or recipe=='daily_booking_cohorts':limitations=['Currency unverified: amounts are shown at source grain without summing across records.','Cohort date is not payment date; null-date placeholders are excluded.']
 else:
  required={'booking_conversion':{'uid','cmp_id'},'customer_consent':{'uid','marketing_opt_in'}}
  consent=f"WITH consent AS (SELECT uid FROM {t}customer_consent GROUP BY uid HAVING COUNT(DISTINCT marketing_opt_in) = 1 AND MAX(marketing_opt_in) = 'Y') "
  group=' GROUP BY b.cmp_id ORDER BY currently_opted_in_converters DESC, campaign_id' if 'vary by campaign' in question else ''
  field='b.cmp_id AS campaign_id, ' if group else ''
  query=consent+f'SELECT {field}COUNT(DISTINCT b.uid) AS currently_opted_in_converters FROM {t}booking_conversion b INNER JOIN consent c ON b.uid = c.uid'+group+' LIMIT 100'
  limitations=['Current recorded Y opt-in only; conflicting consent states excluded. Not historical consent or outreach permission. Campaign distinct counts are not additive.']
 for name,cols in required.items():
  a=schemas.get(name,{})
  if name not in parts or a.get('asset_id')!=parts[name]['asset']['id'] or not cols<={z['name'] for z in a.get('properties',[])}:raise ValueError('Current contract binding/columns missing: '+name)
  if a.get('physical_name')!='/workspace/performance_marketing_mvp/'+name:raise ValueError('Unverified physical mapping: '+name)
 version=p['data_product_details']['id'].split('@')[0]
 matches=[z for z in s.get('subscriptions',[]) if z.get('asset',{}).get('id')==version] if s.get('success') else []
 return {'success':True,'question':question,'query':query,'required_assets':list(required),'product_version':p['data_product_details']['version'],'defaults':{'period':'all available records','limit':100,'timezone':'recorded source basis; not converted'},'subscription_search_succeeded':s.get('success') is True,'subscriptions':[{'id':z['id'],'state':z.get('state')} for z in matches],'limitations':limitations}
