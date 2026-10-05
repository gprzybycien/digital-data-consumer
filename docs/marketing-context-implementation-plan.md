# Marketing context discovery implementation plan

Status: implementation in progress, 2026-10-05. See [release details](marketing-context-release.md). Current scope uses the flat Marketing DPH category, skips subcategories, and adds a removable live get_asset_details column-term workaround with version-bound GitHub reference mappings. Native DPH use-case IDs are optional and unverified. The older proposal below is retained as design context; the release document and active mapping define implemented scope.

Read the [verified wxDI content preparation checklist](wxdi-marketing-content-preparation.md) before implementing this plan. The 2026-10-05 audit supersedes earlier assumptions: domains are present but names are ambiguous; eight project columns already have term assignments; 27 descriptions are blank; DPH target enrichment is not exposed; direct CLI reads return 403. Domain hierarchy, native use-case associations and published semantic relationships remain unverified.

## Outcome and starter experience

Add a starter titled **Find a data product in Marketing** with subtitle **Explore supported analyses and governed meanings**. Its submitted prompt should be:

> Explain which marketing analyses the available governed data products support. Start with supported use cases and their industry references, then show the glossary categories analyzed, the business terms and measures retrieved, and the underlying products and assets. Verify published product versions and glossary definitions using live tools. Distinguish verified glossary relationships from proposed or unverified relationships. Explain gaps and limitations. Help me choose a use case before proceeding to subscription or querying.

Use the native agent's existing `starter_prompts.prompts` structure: `id: discover_marketing`, title, subtitle, prompt and `state: active`. Preserve existing starters subject to the deployed UI's supported count: current IBM UI documentation says up to three, while the repository YAML has five. Validate with the installed ADK and deployed chat; do not promise a distinct hidden prompt/title rendering without checking it.

First answer contract:

1. State the actual DPH domain/subdomain and glossary category paths analyzed, including child/secondary membership coverage and retrieval failures.
2. Show a compact use-case table: supported analysis, industry reference, core terms/measures, exact available product/version and main limitation.
3. Summarize formal glossary relationships retrieved; mark unverified relationships explicitly. Column assignment, conceptual relationship and SQL join are separate evidence.
4. Explain missing capabilities such as actual spend, ROI, audience segmentation or historical consent.
5. Invite selection of an analysis; defer detailed term lists until selected. No implicit subscription or SQL execution from this starter.

Example answer shape, not a live response:

| Analysis | Industry alignment | Meaning | Product coverage |
| --- | --- | --- | --- |
| Campaign engagement | APQC process 10170 | Recorded clicks/impressions by event date | Campaign + digital event |
| Paid-booking performance | APQC process 10170 | Bookings with recorded payment completion; select booking/payment date | Campaign + booking detail |
| Daily booking cohorts | APQC process 10170 | Daily booking counts and paid amounts by conversion date | Daily aggregate |
| Planned budgets | APQC process 10157 | Whole-campaign planned budget, not actual spend | Campaign |
| Current opt-in among converters | Partial support for APQC process 10153 | Current recorded state, not historical permission | Consent + booking detail or approved aggregate |

These are locally defined use cases aligned to APQC, not APQC-certified product definitions. IAB audience categories are not assigned to the five assets because segment membership is absent.

## GitHub persistence

Proposed repository folder: `context/marketing/` in https://github.com/gprzybycien/digital-data-consumer.

Start with `mapping.proposed.yaml` supplied alongside this plan. Before release, resolve its null identifiers, pin the industry edition, review coverage and promote to `mapping.yaml` with `status: active`. Keep the proposed file out of production tool indexes.

Suggested structure:

```text
context/
  schema/context-mapping.schema.json       # structural validation
  marketing/mapping.yaml                  # reviewed discovery relationships
  marketing/bindings/<environment>.yaml   # tenant IDs; no credentials
  marketing/README.md                     # owners, scope, review procedure
  marketing/evidence.json                 # compact verification report, not raw data
tools/
  context_search.py
  context_read.py
  context_verify.py
```

Mapping owns: local use-case IDs, industry references and versions, domain/category crosswalks, required concept and measure references, candidate-product relationships, requirements and limitations. Environment bindings own DPH container/domain/subdomain/use-case IDs, product family/version IDs, catalog/project asset IDs, and glossary artifact IDs. Do not match by names at runtime after onboarding.

wxDI remains authoritative for glossary text, publication state, assigned terms, contracts, product versions, access and subscriptions. GitHub is authoritative only for the reviewed crosswalk/recipe. Do not store secrets, personal values, query results, full copied glossaries or user access state here. Use PR review, CODEOWNERS, schema/reference validation and a pinned commit packaged with the tool release. Normal chat reads the packaged revision; avoid reliance on mutable GitHub main or GitHub availability during every turn. A changed mapping requires validation and redeployment or an explicitly managed refresh.

Every context response should include mapping commit, live retrieval time, exact source IDs/links, relationship evidence state and unresolved checks. Scope live retrieval to objects the authenticated identity may access. Absence from a failed or incomplete read is not evidence of absence.

## Consumer-agent implementation

1. Add `UNDERSTAND` intent routing before the current automatic subscription-resolution instructions. Domain explanation, semantic exploration and product evaluation use metadata reads only; explicit data analysis retains the subscription/contract/query gates.
2. Add three proposed read-only ADK tools (these names are not existing wxDI MCP tools):
   - `search_use_case_context(domain, intent, limit)` returns compact curated candidates and requirements.
   - `read_use_case_context(use_case_id)` returns exact mapping references, relevant asset roles, term/measure references and limitations.
   - `verify_use_case_context(use_case_id)` resolves live domain, published terms and relationships, exact product details/contracts and relevant assignments; returns per-check evidence rather than one optimistic boolean.
3. Initially implement these as Python ADK tools using the pinned mapping and verified API/MCP adapters. A separate context MCP server is optional later. Do not put tokens or arbitrary HTTP URLs in model-supplied parameters.
4. Use existing product search/detail/contract, glossary-assignment, quality and subscription tools. Attach verified category/term readers or a read-only glossary adapter: the current agent YAML lacks complete category/term/relationship lookup. Resolve installed names through actual tool discovery; names in research are not guaranteed deployment names.
5. For taxonomy retrieval use SDK `list_data_product_domains(include_subdomains=True)` and `get_domain`; the installed MCP domain reader exposes neither recursive coverage nor product `use_cases` assignment. Wrap missing read capabilities rather than assuming a flattened MCP response is complete.
6. After selection, collect the question's measure, dimensions and time basis, then check coverage. Actual analytical questions can continue through existing access resolution. Subscription creation still requires the exact contract review/acceptance and identity explanation already in the agent.
7. Query only using verified implementations and safe joins. The mapping's term names and requirements are not executable formulas. Retrieve approved model/contract expressions; aggregate event and booking facts separately; handle cohort date, null-date placeholders and non-additive distinct subjects.
8. For gaps, produce a producer/steward handoff with missing semantics, asset requirements, accountable owner and acceptance criteria. Consumer tools prepare requests; producer writes run through a separate controlled workflow or role. A new consumer question does not itself authorize platform mutations.

## wxDI preparation and update sequence

### 1. Baseline inventory

Read exact tenant domain/subdomain IDs, product-associated use-case references, all five asset IDs in source project, curated catalog and DPH catalog, product family/version/contract, term IDs and published definitions, assignments and relationship evidence. The latest MCP domain-list read returned an empty array; verify through the SDK with explicit container before concluding the tenant is empty. Do not initialize starter content merely to fix a read failure.

### 2. Domain and use-case configuration

Reuse Marketing and appropriate subdomains. If missing and authorized, create domains/subdomains through configuration UI or verified SDK. Evaluate existing `domains_multi_industry` starter taxonomy before creating local use cases; initialization is a write and may initialize dependencies. The SDK supports product `use_cases` references, but dedicated use-case CRUD was not verified. Resolve existing IDs or verify the backing asset/UI mechanism before creating use cases. No invented endpoint.

### 3. Glossary reconciliation

Reconcile the existing 24 terms and seven locally proposed metrics against live published content. Some metric-like aggregate terms already exist: avoid duplicate measures. Create only missing governed measures such as explicit click/impression counts and paid-booking count if absent. Review business definitions, time basis, currency, counting rules, exclusions and aggregation behavior with the steward.

Organize primary categories by responsible subject area; use secondary membership for `agent access` discovery. The existing subcategory move plan has not been applied. An ID-preserving category move path must be verified before execution; never substitute a CSV import that could duplicate terms. Reorganization can affect access/workflows. Include both descendant categories and secondary membership in subsequent discovery.

Publish approved revisions and verify formal concept relationships separately from category membership. Store glossary IDs in environment bindings. Do not describe steward-review caveats as removed simply because a term is published.

### 4. Technical asset metadata

Import/reimport the scoped five Databricks assets if missing or stale, preserving curated descriptions and importing available key/lineage metadata. Profile candidate keys, nulls, referential coverage and row grain. Resolve source timezone, currency and freshness evidence; do not fill unspecified values by inference.

Assign terms at the correct column level. The exposed `update_asset_metadata` tool provides asset-level terms/description, not a verified column-description/column-term write interface. Use a verified catalog API adapter or UI for these edits. Metadata expansion/enrichment produces suggestions, not deterministic approved glossary copies.

Descriptions combine glossary meaning with asset-specific grain, units, dates, transformations and null behavior. Verify source project, catalog and DPH target copies separately. Record term/version references and protect curated content against future imports. Direct contact data remains subject to product access restrictions.

### 5. Product metadata and analytical semantics

Keep the existing five-asset Performance Marketing product for the MVP. Attach the intended domain/subdomain and verified use-case IDs using the SDK/API or UI; the installed MCP attachment tool only accepts a domain name. Add purpose, supported questions, limitations, delivery and service commitments.

Update the analytical model and ODCS together from reviewed definitions. Verify formulas, relationships and transformations survive import/readback; standard schema validation does not prove custom-extension consumption. A separate Current Marketing Consent product is a later ownership/access decision, not required by the starter. Review consent-derived aggregate visibility as well as raw-table visibility.

Prefer a new draft/version for material published-product changes. Validate contract, coverage and representative calculations before publication; bind context to the exact published version. Existing subscriptions need explicit compatibility/re-subscription handling after a version change. Consumer-facing context does not auto-publish products.

### 6. Release and operate

Update environment bindings from verified IDs, activate the reviewed mapping, import the validated agent/tools, check actual starter rendering, and run an end-to-end consumer trial. Existing subscriptions are read first; create only with explicit contract acceptance. Verify succeeded delivery and actual read-only query access before claiming readiness. Track glossary/contract/schema/version drift; mark stale mappings and revalidate before use.

## Acceptance scenarios

- Starter returns use cases, APQC references, analyzed categories, retrieved terms/measures, available exact products and missing evidence without subscription or SQL calls.
- Engagement selects event detail; daily bookings select the cohort aggregate; paid-booking questions clarify their time basis.
- ROI/spend and historical-consent questions produce specific gaps, not unsupported queries.
- Failed category/product reads remain visible; secondary membership and descendants are covered; ambiguous names do not resolve silently.
- Mapping references validate; live definitions and product versions are rechecked; no SQL uses unresolved metric implementations.
- A chosen supported question proceeds through reviewed subscription/access to a verified result; identity is explained and personal fields are not exposed.

## Verified reference sources

- [WxO welcome content and starter prompts](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=agents-customizing-welcome-message-starter-prompts)
- [WxO starter UI limit](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=agents-getting-started-building)
- [IBM DPH SDK implementation](https://github.com/IBM/data-intelligence-sdk/blob/main/src/wxdi/dph_services/dph_v1.py): domain/subdomain APIs, product use_cases, starter taxonomy initialization.
- [wxDI domain configuration](https://www.ibm.com/docs/en/watsonx/wdi/2.4.x?topic=hub-managing-business-domains)
- [Glossary categories and governance](https://www.ibm.com/docs/en/watsonx/wdi/2.4.x?topic=categories-designing)
- [Metadata import preparation](https://www.ibm.com/docs/en/watsonx/wdi/2.4.x?topic=metadata-creating-imports)
- [APQC marketing process references](https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/marketing-reach-b2b-customers)
- [IAB Audience Taxonomy](https://iabtechlab.com/standards/audience-taxonomy/)
