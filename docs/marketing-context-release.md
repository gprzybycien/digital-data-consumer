# Marketing consumer extension

Published and deployed 2026-10-05 to the existing `wxdi_data_consumer` in
`pm-steward-syd`. All 33 tests pass. The mapping is pinned to GitHub commit
`f18abf52283f102c9eb6ae805d3c0f971d91a123` with verified SHA-256 readback.
An initial smoke test exposed premature snapshot claims; the deployed correction
requires live product, glossary and asset checks and explicitly labels GitHub
search results as unverified historical candidates. Retest evidence is recorded
in the local implementation-status file. Administrative credential readback is
masked; release publication runs inside WxO using `github_snapshot_creds`.

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
orchestrate agents import -f agent/wxdi-data-consumer.yaml
```

Verify imported tool schemas and expected connections before deployment. Exercise
an UNDERSTAND conversation without SQL/subscription calls, a supported selected
analysis, a drifted version, and an unsupported ROI/historical-consent question.
Use the agent owner's normal deployment command after validation.

Known outstanding content gaps are not silently repaired: ODCS descriptions,
customer_consent contract binding, formal glossary relationships, APQC edition,
currency/timezone and validated metric results. The agent reports these gaps and
does not claim query readiness from discovery verification.
