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
