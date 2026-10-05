# Operation receipt template

Complete privately; sanitize before sharing. Do not commit completed receipts.
Use one receipt per actual operation; aggregate only with per-call traceability.

```text
Requested outcome:
Evidence kind: documented | observed | historical | unknown
Capability stage: advertised | schema-inspected | client-callable | executed | verified outcome
Execution origin: public documentation | offline fixture | direct MCP client | supplied evidence
Timestamp/timezone:
Product/edition/appliance build: verified value + source | unknown
HVM release/layout (when relevant): verified value + source | unknown
Authorized target/account/cloud/object scope (sanitized):
Actual tool and sanitized resolved arguments:
Schema/effect reference and inspection time:
Actual operation submitted: yes/no (loader != business read)
Read/write classification and exact approval reference if applicable:
Transport/wrapper/application/job result:
Requested vs actual filters and limits:
API pages/offsets/cursors, returned rows, unique rows, declared total:
Artifact hops/pages/path, accessible rows vs preview, remaining truncation:
Selected/query-matching count (separate from collection total):
Completeness: complete in stated scope | partial | unknown | not applicable
Identity: current cloud/server/provider identity verified | historical only | unknown
Requested fields verified / missing / substituted (not credited):
Outcome/read-back/application acceptance:
Changes actually performed:
Failure class, limits, uncertainty and next owner:
```

Not applicable is appropriate for counts in schema-only calls; it is not a
substitute for unknown inventory totals. Keep credentials and sensitive fields
out of argument receipts. A redacted argument indicates omitted sensitive data,
not permission to discard the private audit record required by policy.
