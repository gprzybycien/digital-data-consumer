# Native clickable follow-up pilot

2026-10-06. Isolated two-tool pilot, no credentials or data writes. Native FormWidget
radio choices plus Continue. ToolEvent validates the selected choice; MessageEvent
continues understanding/refinement. Selecting a question never authorizes calculation
or subscription. Users can keep typing normally.

Initial area -> sample questions in that area -> explanation/evidence/readiness.
Numeric replies use the most recent choices. Do not repeat the area menu after
selection. Engagement examples: recorded clicks/impressions by campaign, by channel,
or over time. These do not introduce CTR, ROI, unique-reach or funnel measures.

The pilot's question library currently reflects the five curated recipes and one
mapped product. New product/use-case coverage requires reviewed library updates;
no new product IDs, glossary entries or metric definitions are fabricated.

## Rollback

Run `sh rollback/next-step-widget/rollback.sh` from the project (or by absolute path)
after activating the intended WxO environment. It imports and deploys the complete
pre-pilot agent definition. Both widget tools are then detached. No wxDI content,
managed connections, mapping commit, subscriptions or data were changed by this
pilot. Installed detached tools can remain for re-enabling or be removed separately.

The original baseline is `rollback/next-step-widget/wxdi-data-consumer.before.yaml`.
The new tools are `tools/discovery_ui/next_steps.py`. Text fallback is available
if the chat channel fails to render the form. Successful tool payload generation
alone does not prove browser rendering or form-submit behavior; record these
checks separately during live verification.

Follow-up refinement: the tool now supplies substantive stage-specific text before
the form. Area labels describe the analysis rather than naming a topic alone.
Overview text identifies curated product/glossary scope, relevant measures and
limitations without claiming live verification. The original pre-pilot rollback
baseline remains unchanged.

## Default answer on question selection

Selecting a business-question option now requests a read-only default answer through
existing subscription, semantic, physical-mapping and source-access gates. Area
selection remains discovery only. No extra explain/readiness/proceed level is
required. Default period is all available records, grouping follows the question,
and timestamp handling follows recorded source basis without inventing UTC
conversion. State defaults with the result. If execution is blocked, provide an
explicitly unexecuted query only when mappings are verified, plus the actual blocker.
Offer period/grouping/filter customization after the answer. Monetary and date
ambiguities that materially affect the result remain legitimate blockers.

The visible form message is now simply “Continue with my selection.” Internal
routing and authorization details remain in the validated tool result.

Before declaring access absent, reconcile the product VERSION ID (not table IDs),
exact-version subscriptions without a restrictive state filter, pagination, item
states, and the connection identity versus the DPH UI identity. Empty results are
not proof the human user has no subscription. Do not recommend duplicate orders.

A second local checkpoint is rollback/default-answer/, containing the agent and
tool before this default-answer refinement. The original pre-widget rollback remains
rollback/next-step-widget/rollback.sh.

Engagement default drafts now use prepare_default_engagement_query, collecting
full live metadata, glossary and assignments plus an exact-version subscription
search before build_default_engagement_query creates SQL. It never invents tables
or claims execution. The three Engagement questions are deterministic; other areas
retain the existing guarded agent query path. Actual result execution still requires
subscription item delivery, source access, and relevant metric validation.
