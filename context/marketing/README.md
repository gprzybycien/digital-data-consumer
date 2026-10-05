# Marketing discovery context

`mapping.json` contains five local Marketing recipes, 28 glossary ID/revision/digest
references and 29 verified column-term bindings for Performance Marketing 1.0.2.
The only glossary category is **Marketing DPH**. No subcategories are created or
required. The parent Marketing domain hierarchy and native DPH use-case taxonomy
remain unverified. APQC identifiers are local process alignment with an unpinned
edition; they are not certified definitions.

The agent reads a pinned GitHub commit using the existing `github_snapshot_creds`
WxO connection. `tools/marketing_context/context_tools.py` carries the commit and
SHA-256 digest. Runtime tools have read-only permissions and no GitHub writes.
wxDI remains authoritative for definitions, state, assignments and products.
Full definitions, personal data, credentials and subscription state are not copied
into the active mapping. Existing inspection files are local audit evidence, not
runtime context and are not published by the context release script.

The temporary workaround reads `get_asset_details` on the exact DPH catalog asset
IDs because `get_data_product_details` omits column terms. `verify_use_case_context`
compares those live results with the reference bindings. If live reads fail, the
snapshot can explain historical mappings only; it never passes live verification.
A version, asset, schema or glossary-revision change fails verification.

When the product-details tool exposes column terms, the verifier automatically
prefers them. Remove the snapshot section and extra asset-read instructions in a
reviewed subsequent release, updating schema and tests together.

Known gaps: ODCS column descriptions are absent; the customer_consent contract
asset ID differs from the current item; formal glossary relationships, currency,
timezone and approved calculation results remain unverified. Discovery does not
authorize subscription creation or SQL.

To release: validate mapping/schema and agent tests; publish only reviewed release
files with `tools/publish_marketing_context.py`; pin its returned commit/digest;
import the three Python tools with `--app-id github_snapshot_creds`; import and
deploy the consumer agent after draft validation. Never change the connection's
credentials or permission scope as part of this process.
