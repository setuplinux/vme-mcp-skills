# Inventory identity, scope and completeness

## Before a read

Agree tenant/account, cloud, resource type, requested fields and a collection
budget (records, pages, time). Validate server-side scope filters before calling.
A small page size does not constrain tenant/cloud scope. If the available tool
cannot enforce authorized scope, stop rather than collect broadly and filter later.

Inspect exact schema types; the public server API describes integer `zoneId`,
boolean `vm`, integer `max`/`offset`, and string `stats`. These public API types
do not establish any MCP adapter's schema. `phrase`
can match names/descriptions and is not a strict prefix. Apply a requested
prefix locally only inside an already authorized, bounded server-side scope;
label that additional selection and preserve both counts.

After each page, validate actual count <= requested maximum, returned scope,
actual offset/total and identifiers. A violated filter/limit is not a reason to
fetch more. Suppress identifying previews, record the violation and stop.

## Count the collection, not the preview

Maintain requested page size, actual rows, unique IDs, offsets/cursors, declared
total, query scope and capture time. Follow only the endpoint's inspected
pagination semantics. Detect repeated pages/IDs/cursors, changing totals,
unexpected ordering and no-progress pages; report partial if not resolvable
within the budget. Do not simply add duplicates to reach the declared total.

Complete requires all pages for the same permitted query, all required rows
accessible, reconciled unique counts and no unexplained conflicts/truncation.
If the schema provides no authoritative total, record it as unknown; use a
documented end-of-collection marker if available and disclose snapshot limits.
An empty intermediate page with remaining total is not completion.

Examples are synthetic: 3 visible of 12 means partial; 0 results in an
inaccessible/partial collection does not mean "not found." Even 12/12 authorizes
only "not found in this queried scope at this time," not a global absence claim.
A query result/excerpt match count is not the source collection total.

## Compacted and nested results

Artifact retrieval and API pagination are separate layers, with separate counts.

1. Record the artifact reference and truncation metadata privately. A preview,
   summary, `{type, preview, truncated}` object or wrapper is not a row array.
2. Inspect the retrieval helper's own schema and retrieval-only behavior. Scope
   path/query and `offset`/`limit`; do not assume those are API row offsets.
3. Follow the **new artifact ID** if an excerpt is itself compacted. Resolve
   the path in that artifact's structure, not the old root. Track an explicit
   hop/page/output budget and seen artifact/path/offset tuples to prevent cycles.
4. Synthetic examples include root `migrations`, then a newly compacted
   result at `items.0.servers`. These are not universal shapes. Inspect returned
   keys and retrieve only the required branch, never recursively dump everything.
5. If a necessary artifact expires, is inaccessible or remains truncated,
   report partial/unknown. Never issue a negative search conclusion.

Check the current retrieval helper's query semantics: substring search is not
identity lookup. An excerpt may locate history without proving complete current
inventory or migration eligibility.

## Stable identity and historical evidence

Keep account + object kind + current cloud ID + server ID, plus provider identity
(VMware UUID/MoRef/external ID where exposed). Names may collide across clouds,
source/destination, clones and time. Do not conflate instance and server IDs:
managed instances are not all discovered VMs; correlate rather than double-count.

Read the selected current object by its inspected ID tool and compare provider
identity, cloud, current state and time. A same-name migration history record
is a lead only. Historical mappings, datastore/network IDs, source/destination
records and successful past runs are not current eligibility or approved settings.
If identity fields are unavailable/conflicting, mark unknown and block changes.

Keep exact IDs in private operational evidence. Share stable synthetic aliases
or approved minimal fields. The optional health probe performs none of this
inventory logic; [offline scenarios](../tests/scenarios.json) evaluate the
documented decisions, not an inventory automation engine.
