from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
AGENT_FILE = ROOT / "agent" / "wxdi-data-consumer.yaml"


class AgentDefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = AGENT_FILE.read_text(encoding="utf-8")
        cls.agent = yaml.safe_load(cls.raw)

    def test_native_agent_identity(self):
        self.assertEqual("v1", self.agent["spec_version"])
        self.assertEqual("native", self.agent["kind"])
        self.assertEqual("wxdi_data_consumer", self.agent["name"])
        self.assertFalse(self.agent["memory_enabled"])
        self.assertTrue(self.agent["is_schedulable"])

    def test_required_consumer_tools_are_attached(self):
        required = {
            "wxdi_consumer:search_data_products",
            "wxdi_consumer:get_data_product_details",
            "wxdi_consumer:get_data_product_contract",
            "wxdi_consumer:search_data_product_subscriptions",
            "wxdi_consumer:get_data_product_subscription_details",
            "wxdi_consumer:get_data_contract_test_results",
            "wxdi_consumer:get_semantic_model",
            "wxdi_consumer:create_sql_query",
            "databrics-sql:execute_sql_read_only",
            "databrics-sql:poll_sql_result",
        }
        self.assertTrue(required.issubset(set(self.agent["tools"])))

    def test_mutating_wxdi_tools_are_not_attached(self):
        forbidden_fragments = (
            "publish",
            "create_or_update",
            "create_update",
            "attach_",
            "add_delivery",
            "run_",
            "perform_workflow",
            "update_",
            "delete_",
        )
        for tool in self.agent["tools"]:
            if tool == "wxdi_consumer:run_gs_query":
                continue  # Read-only global search; name prefix is not a mutation.
            self.assertFalse(
                any(fragment in tool for fragment in forbidden_fragments), tool
            )

    def test_instructions_preserve_execution_boundary(self):
        instructions = " ".join(self.agent["instructions"].split())
        for phrase in (
            "never say that you submitted",
            "SUCCEEDED subscription",
            "Do not claim that generated SQL was executed",
            "Enforce read-only execution through execute_sql_read_only",
        ):
            self.assertIn(phrase, instructions)

    def test_agent_uses_contract_semantics_and_databricks(self):
        instructions = " ".join(self.agent["instructions"].split())
        self.assertIn("Resolve business meaning", instructions)
        self.assertIn("authenticated Databricks SQL MCP connection", instructions)
        self.assertNotIn("flight", self.raw.lower())
        self.assertNotIn("Genie", instructions)

    def test_scheduled_insights_are_pinned_and_read_only(self):
        instructions = " ".join(self.agent["instructions"].split())
        for phrase in (
            "one interactive run has succeeded",
            "product ID and version",
            "At every scheduled run",
            "do not silently move to a newer product",
            "must not request interactive input at runtime",
        ):
            self.assertIn(phrase, instructions)

    def test_no_obvious_secret_fields_or_values(self):
        lowered = self.raw.lower()
        self.assertNotIn("api_key:", lowered)
        self.assertNotIn("password:", lowered)
        self.assertNotIn("bearer ", lowered)


if __name__ == "__main__":
    unittest.main()
