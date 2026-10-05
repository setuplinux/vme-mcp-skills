# Ordinary tasks through the managed MCP interface

Every tool below is a semantic discovery target, not a guaranteed name.
Use the relevant catalog family, exact schema and current edition/build/role.
Resolve [identity and coverage](inventory.md) before conclusions or changes.

| Goal | Authorized read/preparation | Approved action and real completion |
| --- | --- | --- |
| Connection/health | Inspect narrow health tool and build evidence | Health does not prove inventory, host or application health |
| Find VMs/hosts | Scoped clouds, servers, instances and cluster views; reconcile IDs | Counts carry completeness; HVM host records do not prove direct access |
| Create a small VM | Resolve tenant/group, cloud/pool, layout/type, image, service plan, disk/network mapping, quota/capacity and duplicates | Approve exact payload; follow job and read back ID/placement; guest/application acceptance still required |
| Start/stop/restart/resize | Current VM identity/state, owner, concurrent jobs, supported graceful/force and resize semantics | Approve power/downtime/storage effects; task plus exact-target read-back, then user outcome |
| Snapshot | Discover applicable server/instance snapshot capability, coverage, consistency, capacity | Create/revert/delete are separate approvals; local snapshot is not independent backup |
| Backup investigation | Exact configuration/run/time, scoped result/history and sanitized error, supported provider evidence | Rerun, change schedule/retention, restore or delete recovery points needs exact approval |
| Placement/network/storage | Scoped pools, networks/datastores, policy, capacity and accessibility reports | No implicit refresh, sync, attach/detach or repair; a listing does not prove routing, I/O or quorum |
| Monitoring/alerts | Inspect only requested checks/events/time window and entitlement | License denial is unavailable evidence, not zero alerts; acknowledge/clear is a change |
| Reports | List existing scoped report/status if exposed | Generating/running/exporting/uploading a report may change state or disclose data; not implicit |
| Incident triage | Classify appliance vs workload, capture timestamp/IDs/impact; compare relevant current MCP views | State facts, hypotheses and unknown layers; no host/guest command workaround or automatic remediation |

For creating a VM, a virtual-image record is not an ISO upload, and an ISO-backed
powered-on VM is not an installed OS. Don't invent an upload or snapshot tool.
Default placement, public addressing, retention or disk deletion can have real
effects; resolve them rather than inherit a known-working peer's stale settings.

For a failed job, preserve the exact job/resource/time. A "pending" or "running"
result is not failure or success. Bounded status reads can verify terminal state,
but successful backup/migration jobs do not prove restore quality or application
acceptance. Operator-provided guest evidence stays labeled as supplied, not as
MCP-executed verification.

If the requested operation is absent or uncallable, give the last verified state,
missing capability/evidence and an administrator handoff. Do not install tools,
repair hosts, invoke arbitrary workflows or switch to REST to fill the gap.
Use [change control](change-control.md) before any supported mutation.
