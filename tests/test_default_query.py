import ast,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('d',ROOT/'tools/discovery_ui/default_query.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class DefaultQueryTests(unittest.TestCase):
 def run_draft(self, verified=True, bad_id=False):
  parts=[{'name':n,'asset':{'id':n}} for n in ['campaign','digital_event']]
  schema=[{'name':n,'asset_id':n,'physical_name':'/workspace/performance_marketing_mvp/'+n,'properties':[{'name':c} for c in cols]} for n,cols in [('campaign',['campaign_id','channel_code']),('digital_event',['cmp_id','evt','ts'])]]
  if bad_id:schema[0]['asset_id']='old'
  return m.build_default_engagement_query.fn('How many recorded clicks and impressions did each campaign generate?',{'success':True,'discovery_verified':verified},{'success':True,'data_product_details':{'id':'version@catalog','version':'1.0.4','parts_out':parts}},{'success':True,'data_contract':repr({'schema':schema})},{'success':True,'subscriptions':[{'id':'order','asset':{'id':'version'},'state':'succeeded'}]})
 def test_grounded_default_and_product_version_subscription(self):
  r=self.run_draft();self.assertTrue(r['success']);self.assertFalse(r['executed']);self.assertIn('digital_event',r['query']);self.assertNotIn('campaign_events',r['query']);self.assertEqual('order',r['subscriptions'][0]['id']);self.assertEqual('all available records',r['defaults']['period'])
 def test_semantic_failure_and_stale_contract_block_draft(self):
  self.assertFalse(self.run_draft(verified=False)['success']);self.assertFalse(self.run_draft(bad_id=True)['success'])

class DeliveryGuardTests(unittest.TestCase):
 def test_null_top_level_state_accepts_nested_delivered_original_assets(self):
  parts=[{'name':n,'asset':{'id':n}} for n in ('campaign','digital_event')]
  items=[{'asset':{'id':n},'state':None,'properties':{'data_product_delivery_state':'delivered','output':{'route':[{'key':k,'value':v} for k,v in [('catalog','workspace'),('schema','performance_marketing_mvp'),('table',n)]]}}} for n in ('campaign','digital_event')]
  args=({'success':True,'query':'SELECT 1'},{'success':True,'items':items},{'data_product_details':{'parts_out':parts}})
  self.assertEqual('SELECT 1',m.authorize_delivered_engagement_query.fn(*args)['query'])
  items[0]['properties']['data_product_delivery_state']='revoked'
  with self.assertRaises(ValueError):m.authorize_delivered_engagement_query.fn(*args)
 def test_failed_search_never_becomes_missing_access(self):
  with self.assertRaisesRegex(ValueError,'unknown'):m.select_existing_engagement_subscription.fn({'success':True,'subscription_search_succeeded':False})

class ExecutedAnswerTests(unittest.TestCase):
 def test_polled_success_is_not_labeled_unexecuted(self):
  d={'question':'channels','product_version':'1.0.4','defaults':{},'query':'SELECT 1','executed':False,'label':'UNEXECUTED query'}
  r=m.summarize_executed_engagement_answer.fn(d,{'status':{'state':'SUCCEEDED'},'statement_id':'s','result':{'data_array':[['DISPLAY',1,0]]}},{'subscription_id':'order'})
  self.assertTrue(r['executed']);self.assertEqual('SUCCEEDED',r['execution_state']);self.assertNotIn('label',r);self.assertIn('result',r)

class AllAreaQueryTests(unittest.TestCase):
 def setUp(self):
  import csv,duckdb
  self.db=duckdb.connect();self.db.execute("ATTACH ':memory:' AS workspace");self.db.execute('CREATE SCHEMA workspace.performance_marketing_mvp')
  self.parts=[];self.schema=[]
  for path in (ROOT/'exports/databricks').glob('*.csv'):
   n=path.stem
   with path.open() as f:cols=next(csv.reader(f))
   self.parts.append({'name':n,'asset':{'id':n}});self.schema.append({'name':n,'asset_id':n,'physical_name':'/workspace/performance_marketing_mvp/'+n,'properties':[{'name':c} for c in cols]})
   self.db.execute(f"CREATE TABLE workspace.performance_marketing_mvp.{n} AS SELECT * FROM read_csv_auto(?)",[str(path)])
 def tearDown(self):self.db.close()
 def draft(self,q):
  return m.build_default_marketing_query.fn(q,{'discovery_verified':True},{'success':True,'data_product_details':{'id':'version@catalog','version':'1.0.4','parts_out':self.parts}},{'success':True,'data_contract':repr({'schema':self.schema})},{'success':True,'subscriptions':[{'id':'order','asset':{'id':'version'},'state':'succeeded'}]})
 def test_every_calculation_runs_on_recorded_asset_schema(self):
  for q in m.QUESTION_RECIPES:
   with self.subTest(question=q):
    d=self.draft(q);rows=self.db.execute(d['query']).fetchall();self.assertTrue(rows);self.assertIn('LIMIT 100',d['query']);self.assertTrue(d['required_assets'])
 def test_budget_ranking_and_booking_counts_match_fixture(self):
  q='Which campaigns have the largest planned budgets?';rows=self.db.execute(self.draft(q)['query']).fetchall()
  self.assertEqual(sorted([r[3] for r in rows],reverse=True),[r[3] for r in rows]);self.assertTrue(self.draft(q)['limitations'])
  rows=self.db.execute(self.draft('How many bookings and paid bookings does each campaign have?')['query']).fetchall();self.assertEqual(3,sum(r[1] for r in rows));self.assertEqual(2,sum(r[2] for r in rows))
 def test_stale_budget_binding_blocks_execution(self):
  next(a for a in self.schema if a['name']=='campaign')['asset_id']='stale'
  with self.assertRaises(ValueError):self.draft('Which campaigns have the largest planned budgets?')
 def test_explanation_never_resolves_to_a_query(self):
  with self.assertRaises(ValueError):m.resolve_marketing_question.fn('What does the current opt-in measure mean and what are its limitations?')
