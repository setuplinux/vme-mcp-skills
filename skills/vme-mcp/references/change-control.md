# Exact approvals and verified outcomes

MCP-only is not read-only-only. Reads can support a properly approved change
when product support, entitlement, permissions, current schema and exact
identity are resolved. Discovery in this package's authoring performs no writes.

Present this privately before a mutation; sanitize shared copies:

```text
Action and purpose:
Exact tool / resolved arguments / schema reference:
Target account, cloud, object kind, current IDs and provider identity:
Product, build, host/layout dependencies and support evidence:
Expected effects, downtime, cost, data impact and blast radius:
Prechecks, current state, concurrent operations and exclusions:
Recovery/rollback feasibility, owner, deadline and approved recovery actions:
Verification reads, user/application acceptance and bounded wait:
Approver, exact scope and expiry:
```

Obtain approval for this exact operation; reuse an existing explicit approval
only if it resolves the same targets, arguments and boundaries. "Test everything,"
"fix it" or urgency does not authorize unknown changes. Credential/role/license
changes, feature enablement, refresh/sync, validation with side effects, plan
creation, execution, cleanup and external sharing all need their own scope.

Recheck identity/preconditions immediately before execution. Stop if material
facts changed. Do not send credentials in chat payloads; use supported secure
references. An opaque nested schema, contradictory documentation or unresolved
required secret-handling path blocks execution, not an invitation to guess.

Record actual tool, sanitized arguments and job/resource identifiers privately.
After acceptance, inspect status within a bounded window. After terminal success,
read the exact target independently and validate the intended user outcome.
If MCP cannot verify the application, mark application verification pending and
request approved owner evidence. Never equate power-on, HTTP 200 or `success:true`
with a healthy migrated workload.

On timeout, report **submitted; outcome unknown**. Reconcile task/history/target
state before any decision to retry. Never duplicate, automatically roll back,
restore, delete, power-cycle or run cleanup unless that exact action is already
approved and its preconditions still hold.

Hard stops: ambiguous identity, unsafe/unknown required quorum or storage state,
possible duplicate active VM, concurrent HA/migration/restore activity, lost
visibility, changed scope, rejected licensing/role or exceeded window. Escalate
through the managed administrator workflow; no SSH/libvirt/OS repair procedures
belong here.
