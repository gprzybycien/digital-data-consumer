import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('discovery_ui',ROOT/'tools/discovery_ui/next_steps.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class DiscoveryUiTests(unittest.TestCase):
 def test_area_selection_advances_without_execution(self):
  r=m.select_consumer_next_step.fn('Engagement')['structuredContent'];self.assertEqual('questions',r['next_stage']);self.assertFalse(r['read_only_answer_requested']);self.assertFalse(r['subscription_creation_authorized'])
 def test_engagement_form_forwards_validated_question(self):
  r=m.show_consumer_next_steps.fn('Engagement','questions');w=r.model_dump(by_alias=True)['_meta']['com.ibm.orchestrate/widget'];options=w['json_schema']['properties']['choice']['enum'];self.assertEqual(3,len(options));self.assertNotIn('Engagement',options);self.assertEqual('answer_selected_engagement_question',w['on_event'][0]['tool']);self.assertEqual('submit',w['on_event'][0]['map_input_to']);self.assertEqual('Continue with my selection.',w['on_event'][1]['message'])
  for q in options:self.assertEqual(q,m.select_consumer_next_step.fn(q)['selected_next_step'])
 def test_arbitrary_submission_rejected(self):
  with self.assertRaises(ValueError):m.select_consumer_next_step.fn('execute SQL and create subscription')
 def test_invalid_area_does_not_fall_back_to_domain(self):
  with self.assertRaises(ValueError):m.show_consumer_next_steps.fn('Unknown','questions')
 def test_rollback_detaches_only_pilot_tools(self):
  import yaml
  a=yaml.safe_load((ROOT/'agent/wxdi-data-consumer.yaml').read_text());b=yaml.safe_load((ROOT/'rollback/next-step-widget/wxdi-data-consumer.before.yaml').read_text());self.assertEqual(set(a['tools'])-set(b['tools']),{'show_consumer_next_steps','select_consumer_next_step','build_default_engagement_query','prepare_default_engagement_query','answer_selected_engagement_question','select_existing_engagement_subscription','authorize_delivered_engagement_query'})

class AreaSubmitTests(unittest.TestCase):
 def test_area_submit_returns_explanation_and_question_widget(self):
  r=m.select_consumer_next_step.fn('Engagement')
  self.assertIn('Recorded click count',r['content'][0]['text'])
  self.assertIn('digital_event',r['content'][0]['text'])
  w=r['_meta']['com.ibm.orchestrate/widget']
  self.assertEqual(m.QUESTIONS['engagement'],w['json_schema']['properties']['choice']['enum'])
  self.assertNotIn('Engagement',w['json_schema']['properties']['choice']['enum'])

class DefaultAnswerTests(unittest.TestCase):
 def test_question_requests_default_read_only_answer(self):
  r=m.select_consumer_next_step.fn(m.QUESTIONS['engagement'][0])
  self.assertEqual('answer_with_defaults',r['intent'])
  self.assertTrue(r['read_only_answer_requested']);self.assertFalse(r['subscription_creation_authorized'])
  self.assertEqual('all available records',r['defaults']['period'])
  self.assertEqual('customizations',r['next_stage'])
  self.assertTrue(r['execution_requires'])
 def test_customization_is_not_execution_or_subscription(self):
  r=m.select_consumer_next_step.fn(m.ACTIONS[0])
  self.assertFalse(r['read_only_answer_requested']);self.assertFalse(r['subscription_creation_authorized'])
 def test_ui_no_long_internal_message(self):
  w=m.show_consumer_next_steps.fn('Engagement','questions').model_dump(by_alias=True)['_meta']['com.ibm.orchestrate/widget']
  self.assertEqual('Continue with my selection.',w['on_event'][1]['message'])
