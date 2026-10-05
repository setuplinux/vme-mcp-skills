# Discovery, invocation and failure classification

## Evidence stages

| Stage | Required evidence | Does not establish |
| --- | --- | --- |
| Advertised | Tool name in current catalog/loader response | Complete schema, ability to call it |
| Schema-inspected | Exact current input schema, description, effect/method/path and conflicts reviewed | Client registration, permissions, entitlement |
| Client-callable | Exact operation is registered in this client, or supported same-session MCP `tools/call` route is available | Successful target execution |
| Executed | Actual operation and resolved arguments submitted; actual response captured | Success or user outcome |
| Verified outcome | Result layers, exact target read-back and required user-level checks agree | Uninspected capabilities or other scopes |

Track evidence kind separately: documented, observed, historical, unknown.
Observed registration failures are not evidence of a missing product API.
An inspected opaque object payload can remain inadequate for safe execution.

## Portable sequence

Use the client's native discovery mechanism; do not assume adapter-specific naming.
For a direct MCP client, initialize with supported protocol/capabilities,
complete `notifications/initialized`, preserve returned session ID privately
and send the negotiated protocol header. Follow `tools/list` cursors within a
page/time budget; reject cycles/conflicting definitions.

Inspect any loader's schema and verify it only registers definitions. Load
the relevant family, then refresh the **client's callable catalog in the same
session**. A loader returning JSON descriptions may not register any tools.
Do not type a tool name that the client cannot call, nor infer a generic
dispatcher from the server's business catalog. Stop at a registration gap;
do not ask a specialist to gather a fleet to work around it.

Inspect the full business-tool schema, required arguments, types, nested
properties, method/path/effects and version applicability. Hints such as
`readOnlyHint` are advisory, not authorization controls. Even a GET/name
beginning `get` must have an understood effect. MCP's outer POST is transport,
not necessarily a product mutation. Omit unused optional fields, not nulls.

Only if a discovered client implements this standard dispatch, a call has shape:

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"<inspected-tool>","arguments":{}}}
```

This is a protocol illustration, not a universally callable chat tool or valid
payload for every operation. Use exact discovered schemas, never infer spelling
from public API operation IDs. Fingerprint privately saved schemas using SHA-256
of sorted-key, compact UTF-8 JSON; fingerprints detect drift, not support.
Reinspect after session loss, catalog changes, upgrade, role or license changes.

## Check every response layer

Check transport/TLS and HTTP, JSON-RPC request ID/error, `isError`,
`structuredContent`, JSON text in `content[]`, nested application
`success:false`/errors/status, and operation/task terminal state.
An outer success enclosing failure is failure. Plain-text licensing/permission
denials must not be discarded beside a successful wrapper.

| Class | Interpretation and next safe step |
| --- | --- |
| Registration | Advertised operation not callable in client; report stage, stop target execution |
| Wrapper/protocol | Wrong envelope/ID, JSON-RPC error, malformed JSON, HTML or incompatible schema; no outcome claim |
| Authentication | 401 or explicit authentication denial; credential owner verifies approved token locally |
| Authorization | 403/explicit forbidden without a more specific cause; scope unavailable, not empty |
| Licensing | Explicit feature/license denial; affected capability blocked, not healthy/zero alerts |
| Appliance | Actual application error or failed job; record sanitized error and scope |
| Empty | Successful scoped collection with evidence of zero total and no truncation; only empty in that scope |
| Partial | Missing pages, unknown totals, inaccessible artifacts, stale/conflicting data; no negative search conclusion |
| Scope violation | Returned excess records or wrong filters; stop, suppress excess and report bounded counts only |
| Unknown write outcome | Timeout after submission; reconcile inspected job/target reads, never blindly resubmit |

Do not collapse every 403 into licensing or every 404 into missing API support.
Expired sessions, path mismatches and hidden resources are distinct possibilities.
Bound safe read retries, respect rate limits, and stop on excess collection.
No generic retries for writes. A substitute inventory read cannot satisfy an
identity/build/cluster-detail request: mark each requested field unverified.

For protocol details and source-content checks see [sources](sources.md);
for artifact handling see [inventory](inventory.md).
