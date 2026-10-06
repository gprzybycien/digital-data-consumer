# Domain-wide consumer discovery journey

Accepted design, 2026-10-06. Marketing discovery must accommodate more products
and use cases without showing the entire catalogue in a chat response.

## Conversation

1. Explore the business goal. For a broad Marketing prompt, show up to four
   business navigation areas: engagement, conversion performance, budget planning,
   and customer consent. These labels are local navigation, not verified glossary
   subcategories or DPH subdomains. Offer another question as an alternative.
2. Choose an analysis. Show up to five relevant, plainly named analyses within
   the selected area. Describe each in one sentence. Offer refinement or more
   results; do not assert that the curated list is the whole domain catalogue.
3. Understand the recommendation. Explain only the selected measures, business
   meanings, grain, date basis and relevant limitations. Recommend suitable
   products with reasons, including direct fit, combined fit, or missing data.
4. Shape the question. Resolve only missing choices such as period, grouping,
   and booking-creation versus conversion-cohort versus payment date.
5. Check readiness. Validate exact product versions, glossary semantics, contract
   and subscription/access gates. Show concise actionable blockers.
6. Answer. Execute only an authorized data question with existing read-only gates;
   report results, interpretation, and sources.

Allow direct questions to skip navigation. Retain selections in the current
conversation; do not require persistent cross-session memory. Selecting an
analysis or asking for its explanation never authorizes subscription or SQL.

## Presentation and evidence

Use short paragraphs and numbered choices, no wide overview tables. Default
responses should fit roughly 150–200 words. Show product and glossary category
once when relevant. Hide internal IDs, hashes, raw payloads and APQC codes unless
requested. Include up to three suggested next prompts, with one clear primary
choice. Present detailed semantic verification and industry alignment on request.
Keep live checks automatic before claims of current availability or assignments.
For an overview based only on curated context, label it curated coverage, not
live availability. Explain failed checks as unverified, not absent.

Distinguish published glossary terms, active column assignments, formal artifact
relationships, contract retrieval, contract test status, and execution readiness.
A queued contract test is pending. Current opt-in does not establish outreach
eligibility; planned budgets are not actual spend; recorded amounts are not net
accounting revenue. Never hide a limitation that changes the selected answer.

## Multiple products and coverage

Use live DPH search alongside curated recipe context. One product may serve many
use cases; one use case may need several products. Rank candidates by governed
meaning, grain, date basis, coverage, freshness and access evidence where returned.
Do not fabricate ranking inputs. Explain why each selected product fits and whether
additional data or transformations are needed; verify join keys before combined
execution. Missing context for a newly discovered product requires live evaluation,
not reuse of another product's verification.

Current mapping/verification flow remains limited to Performance Marketing 1.0.4
and five recipes. The agent must disclose this boundary. Other live products can
be discovered and evaluated with existing tools, but cannot be called verified
by this recipe-specific flow. A future context schema should normalize products,
use cases, navigation areas, and many-to-many use-case/product bindings, including
asset role, required measures, fit and version provenance. Do not manufacture
future product IDs or imply this schema has already been implemented.

## Implementation and rollout

- Replace the agent's mandatory overview table with stage-specific response rules.
- Update the Marketing starter to business-goal discovery.
- Preserve deterministic recipe verification, pinned mappings, and execution gates.
- Publish the reviewed plan and agent definition through the existing managed
  GitHub connection; deploy through WxO.
- First release uses ordinary chat. Evaluate WxO form/widget support in the target
  channel separately before adding analysis selection or date/time-basis forms.
- Verify broad discovery, selected explanations, direct questions, evidence requests,
  unsupported ROI, and multiple-product discovery. Check no horizontal scrolling,
  no IDs/hashes by default, no premature subscription/SQL, and accurate pending states.

This release changes agent interaction and domain discovery guidance. It does not
extend the existing single-product mapping schema or create new wxDI content.
