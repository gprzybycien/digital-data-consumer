# Existing subscription routing

The question selector previously returned `subscription_authorized: false` to prohibit new subscription creation. The agent incorrectly used that flag as evidence that existing access was missing, and generated SQL with nonexistent digital_event columns.

The selector now returns `subscription_creation_authorized: false` and `read_only_answer_requested`. Engagement question forms invoke `answer_selected_engagement_question` directly. This native flow reads the current pinned product, contract, glossary, catalog assets and exact-version subscription search, then builds SQL from verified physical mappings, validates nested delivered item states and original-source descriptors, and invokes the authenticated read-only SQL tool. Pending SQL results are polled by the agent. Existing delivered subscriptions remain eligible for read-only execution after item and source checks. Failed searches must be described as unknown access, not absence of subscription.

The channel query counts click/impression event values in digital_event and joins campaign for channel_code. It must not invent count columns or put channel_code in digital_event.

Rollback: run `rollback/subscription-routing/rollback.sh`. Existing open chat forms retain their old event definitions; start a new chat after deployment.
