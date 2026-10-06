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
