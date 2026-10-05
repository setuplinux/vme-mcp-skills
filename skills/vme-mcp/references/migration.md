# Migration assessment, history and approved execution

First distinguish VMware-to-HVM conversion from HVM host/storage movement,
image import and restore. Do not assume zero downtime. The default deliverable
is an assessment and proposed mapping, **not** a pending appliance plan.
Creating a plan, guest preparation/precheck, running it and recovery are
separate potentially mutating steps.

## Candidate lookup is not plan history

The public [Create a Migration reference](https://apidocs.morpheusdata.com/reference/addmigration),
retrieved 2026-10-05, exposes OpenAPI version `9.0.1` and cites these option
routes in field descriptions:

| Documented route | Documented parameter leads |
| --- | --- |
| `/api/migrations/source-clouds` | No parameters shown in this description |
| `/api/migrations/target-clouds` | `sourceCloudId` |
| `/api/migrations/source-servers` | `sourceCloudId` |
| `/api/migrations/source-storage` | `sourceCloudId`, `sourceServerIds` |
| `/api/migrations/source-network` | `sourceCloudId`, `sourceServerIds` |
| `/api/migrations/target-storage` | `targetCloudId`, `targetPoolId` |
| `/api/migrations/target-network` | `targetCloudId`, `targetPoolId` |

These are **documented route references**, not independently inspected complete
endpoint contracts: full filters, pagination, provider support and MCP exposure
remain unverified. Do not execute these routes through authenticated REST here.
Search relevant migration/options tool metadata for a verified MCP mapping.
If absent, report exposure unknown/not found in the inspected scope, not
"the product has no candidate endpoint."

Generic servers can supply inventory, not eligibility proof. Migration plan
lists supply history, not a current candidate set. Search permitted history
and [artifact branches](inventory.md) without confusing preview coverage with
collection completeness. A plan name or same-name source/destination VM is
never enough: re-resolve current source cloud/server and provider UUID/MoRef.
Historical mappings are not approved/current storage or network settings.

## Current evidence gates

| Gate | Required evidence |
| --- | --- |
| Method/support | Appliance edition/build, source provider/version, HVM release/agents/layout, supported method and live entitlement/role/tool exposure |
| Workload | OS/architecture, BIOS/UEFI/Secure Boot, disk/controller/device/encryption/RDM/shared-disk constraints, boot drivers and application dependencies |
| Target | Healthy supported hosts/storage/network and placement, HA headroom, capacity including conversion/staging overhead, host-to-source data path |
| Mapping | Every current source disk/NIC mapped to eligible target datastore/network, group/pool, VLAN/MTU/addressing/DNS/firewall intent |
| Cutover | Owner-approved outage, consistency/quiesce/shutdown order, source isolation, duplicate identity prevention, pilot and go/no-go holds |
| Recovery | Recoverable protection, restore evidence, retention/isolation, RPO/RTO, deadline, recovery/data owner and post-write reconciliation |
| Acceptance | Job/target read-back plus guest/network/application tests and named technical/business acceptance owners |

Each mandatory gate is Pass, Fail or Unknown with evidence and time.
Any Fail means **not ready for the selected path**. No Fail but any Unknown
means **readiness unknown**. All Pass means **assessment ready**, not execution
authorization. No selected workloads means intake incomplete, not fleet-ready.

MCP inventory may not establish boot drivers, application consistency,
restore quality, host-to-vCenter reachability or effective packet routing.
Request narrow administrator evidence and label it supplied; never run guest
commands or a benchmark to fill these gaps under read-only permission.

## Resolve documentation and schemas before a plan

Use matching release requirements, qualification matrix and actual exposed
schema. Do not promote older archive claims (batch recommendations, minimum
agent, firmware/RDM/media restrictions, disk format or preparation behavior)
to current support guarantees without readable, applicable vendor sources.
Keep prerequisite checks enabled; "precheck" may itself prepare/restart a guest.

An opaque object or truncated field description is not sufficient proof of
a migration tool's nested contract. The public addMigration page uses `skippedPrechecks` in
the schema but `skipPrechecks` in its example. Resolve this with build-matched
documentation and tool validation, not trial mutations or guessed spellings.

Draft exact current mappings, downtime assumptions (not fabricated throughput),
unresolved gates, pilot/wave order and proposed tools privately.
Use [change control](change-control.md). Approval to draft is not approval to
create; approval to create is not approval to run.

Run, if separately approved and supported, is asynchronous: inspect the exact
job and current destination identity/placement, then obtain application
acceptance. Before target writes, source recovery still requires verified
isolation and a supported plan. **After target writes the source may be stale**:
starting it is not an automatic rollback. Stop and involve the data/recovery
owner for reconciliation/restore/forward recovery. No reverse-migration API
or permission to change power/network state is implied.
