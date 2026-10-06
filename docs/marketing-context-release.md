# Marketing consumer extension

Release refresh 2026-10-06: verified published Performance Marketing 1.0.4
(`01a10fd7-7791-7021-be40-1ff4e176d2e0`) through wxDI MCP. Contract retrieval
succeeded; a deterministically generated glossary query returned 28 published
terms. All five DPH assets' 29 active column assignments were read live. The
verifier passes all five recipes against those actual live payloads.
Context tools generate exact glossary, product, contract and asset arguments
and reject summarized product payloads. The deployed agent now uses the
`verify_marketing_use_case_live` WxO flow to forward the query and complete
wxDI outputs deterministically, with no LLM reconstruction. This avoids the earlier malformed query
and incorrect retired-version contract request. Commit/digest pins are recorded
in release-binding.json after publication. Full deployed chat verification is
recorded separately in implementation-status.json.

## Changes

- Metadata-only UNDERSTAND routing precedes automatic subscription resolution.
- Three read-only context tools search, read and verify five curated use cases.
- The Marketing starter explains industry references, actual category, terms,
  measures, reusable product version, limitations and evidence status.
- Three visible starters: Marketing discovery, data questions and subscriptions.
  Comparison and scheduling remain supported through chat instructions.
- Flat Marketing DPH category, 28 term references and 29 column bindings. No
  subcategories and no invented native use-case IDs or domain parent hierarchy.
- Existing subscription, contract acceptance, query and scheduling gates remain.

## Temporary workaround

Live `get_asset_details` reads the exact product catalog copies' column terms.
GitHub provides stable references and a historical snapshot; it cannot establish
current assignments. Product version/asset/schema mismatches invalidate it.
When `get_data_product_details` provides column terms, the verifier prefers them,
allowing the extra reads/snapshot to be removed in a subsequent release.

The tools retrieve the mapping using existing `github_snapshot_creds`, a pinned
commit and a SHA-256 digest. They do not write GitHub or wxDI. Release publication
uses the same managed connection through the ADK administration client. No raw
glossary definitions, source data, credentials or subscription state are published.

## Verification and deployment

Run `tests/test_marketing_context.py` plus the existing suite. Validate the mapping
against `context/schema/context-mapping.schema.json` and its cross-reference checks.
Publish reviewed files from a temporary fixed-payload tool inside WxO using
`connections.key_value("github_snapshot_creds")`. Verify mapping readback, pin
commit/digest, then remove the publishing tool and helper. The administrative
CLI publisher refuses masked credential values and cannot retrieve the secret.

```sh
orchestrate tools import -k python -f tools/marketing_context/context_tools.py \
  -r tools/marketing_context/requirements.txt --app-id github_snapshot_creds
orchestrate tools import -k flow -f tools/marketing_context/verify_live_flow.py
orchestrate agents import -f agent/wxdi-data-consumer.yaml
```

Verify imported tool schemas and expected connections before deployment. Exercise
an UNDERSTAND conversation without SQL/subscription calls, a supported selected
analysis, a drifted version, and an unsupported ROI/historical-consent question.
Use the agent owner's normal deployment command after validation.

Known outstanding content gaps are not silently repaired: ODCS descriptions,
formal glossary relationships, APQC edition,
currency/timezone and validated metric results. The agent reports these gaps and
does not claim query readiness from discovery verification.

Runtime compatibility: flow nodes declare explicit input schemas so the SDK does
not add an unsupported `data` argument. Catalog-only asset calls pass an empty
project string because this runtime drops a mapped null, whereas the MCP tool
requires the project argument. wxDI MCP confirmed that this catalog lookup works.
The verifier accepts both flow `data` envelopes and MCP `structuredContent`.
All 37 unit tests pass.

Version 1.0.4 readback: all five contract asset IDs and all 29 column names match
the delivered product metadata. Contract column descriptions remain absent, its
test status is queued, and no successful subscription is returned for this version.
These are execution readiness limitations, not discovery verification failures.
