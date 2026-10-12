# Level-three Marketing calculation execution

Previously only Engagement form submissions called a deterministic execution flow. Budget, Conversion and Consent submissions returned selector intent to the model, allowing it to stop or invent a sample.

All 11 displayed calculation questions now call `answer_selected_marketing_question` directly. A resolver selects the correct local recipe; live glossary, product, contract and catalog assets are verified. SQL templates validate exact contract asset IDs, required columns and physical paths. Existing exact-version subscriptions are searched; required original assets must have successful nested delivery states and matching source descriptors. The authenticated read-only Databricks tool executes the bounded query; polling and compact actual-result evidence follow. No subscription is created. Explanatory Consent requests remain typed metadata-only questions, rather than calculation buttons.

Budget defaults return campaign records in descending recorded numeric budget order, without aggregating campaigns. Currency is unverified: the answer must not present this as a verified monetary-value comparison, converted currency, actual spend or ROI. Channel budget answers retain campaign rows. Paid-amount defaults return paid booking records without cross-record sums. Daily cohort answers retain the stored cohort grain and exclude null-date placeholders. Consent counts distinct booking subjects with one consistent current Y state, excludes conflicting states, and does not establish outreach eligibility.

All templates were executed against the exported asset fixture schemas in regression tests. This does not establish live data freshness. Live WxO verification records are separate.

Rollback: `rollback/all-area-execution/rollback.sh` restores the previous agent and Python tools. Existing chat forms keep their stored event routing; use a fresh chat after deployment or rollback. The new flow may remain installed but detached.
