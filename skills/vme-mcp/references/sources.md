# Source routing and version gates

Public documentation research does not execute anything on the target.
Do not send private hostnames, inventory, schema instances or credentials to
public search services. Read product docs without target authentication.

## Sources reviewed on 2026-10-05

| Source | Actual evidence and limits |
| --- | --- |
| [Morpheus API](https://apidocs.morpheusdata.com/) | Good API research starting point; not a VME entitlement/MCP parity guarantee |
| [Get All Hosts](https://apidocs.morpheusdata.com/reference/listhosts) | Readable OpenAPI `9.0.1`: GET `/api/servers`; `zoneId`, `vm`, `name`, `phrase`, `max`, `offset`; phrase is name/description partial matching, not strict prefix |
| [Get a Specific Host](https://apidocs.morpheusdata.com/reference/gethost) | GET `/api/servers/{id}`; public schema accepts an integer ID or UUID string; independently inspect the MCP input type |
| [List](https://apidocs.morpheusdata.com/reference/listmigrations), [get](https://apidocs.morpheusdata.com/reference/getmigration), [create](https://apidocs.morpheusdata.com/reference/addmigration), [run migration](https://apidocs.morpheusdata.com/reference/runmigration) | Readable OpenAPI `9.0.1`; plan CRUD/run and option-route references; run is asynchronous, not completion |
| [Pinned official OpenAPI tree](https://github.com/HewlettPackard/morpheus-openapi/tree/ab68e45eecc1de4f0603bb43bc69cb230e54c83c) | Reviewed server list/detail path definitions from `dev-9.1` at this commit; development branch, not installed API contract; Apache-2.0 repository |
| [Public administrator skill](https://github.com/setuplinux/agent-skills/tree/4b425d7f56704c1f5c8dd8dffada201dd6490f24/skills/hpe-vme) | Secondary, community source; reviewed entry point and version-capabilities; historical product distinctions, not freshly verified release claims |
| [VME 9.0.0 release notes](https://support.hpe.com/hpesc/public/docDisplay?docId=sd00008079en_us) | Fresh retrieval returned a JavaScript authentication/session shell with no readable document title/body; product claims were **not reverified** from this fetch |

The guessed API page names `listservers`/`getservers` returned 404; actual
operation IDs in official OpenAPI led to `listhosts`/`gethost`. A failed page
lookup says nothing about endpoint existence. Prefer documentation navigation
and schemas over constructing names.

## Documentation to obtain for the installed release

- [HPE VM Essentials manuals catalog](https://support.hpe.com/connect/s/product?language=en_US&kmpmoid=1014875616&tab=manuals):
  select exact product, edition, release manual and release notes.
- [VME 9.0.2 manual](https://support.hpe.com/hpesc/public/docDisplay?docId=sd00008401en_us):
  archive-provided source lead for API Access, migration requirements/plans and
  driver preparation. Not newly verified readable content in this run.
- [HVM qualification matrix](https://support.hpe.com/hpesc/public/docDisplay?docId=sd00006551en_us):
  source lead for host qualification, not proof of migration eligibility.
- MCP `2025-06-18` [lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle),
  [transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
  and [tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools):
  protocol references for the retained helper; a compatible client may use a
  different negotiated protocol. These links are source routing, not a claim
  of fresh exhaustive specification review.
- [Agent Skills specification](https://agentskills.io/specification):
  portable folder/frontmatter conventions; client install/config is separate.

A 200 response, search snippet, login page or JavaScript bootstrap is not
verified document content. Confirm title, substantive body, revision and claim.
If the canonical HPE page is a shell, use authorized rendered browser reading
or an operator-provided official export with provenance; do not bypass login.
If inaccessible, mark the claim unknown and continue an evidence-gap report.
Following a link can change release scope; record contradictions rather than
silently adopting an older fallback.

## Keep the version axes separate

Record product/edition, appliance build, HVM host release/agent and cluster
layout independently. MCP `serverInfo.version` may describe the MCP
implementation, not the appliance. Report unknown rather than infer from docs.

Historical distinctions from the reviewed September administrator guide:

| Scope | Interpretation constraint |
| --- | --- |
| 8.x | Match exact minor/build/layout; evidence of REST tokens is not MCP enablement, nor proof all 8.x lacks MCP |
| 9.0 / layout 1.3 | The guide attributes an HA ownership transition from Pacemaker to Morpheus Agent to version-scoped vendor docs; do not apply it to an unidentified 8.x layout |
| 9.1 | Guide reports different host configuration/network behavior as field observations, not universal defaults; full layout 2.0 behavior remains unverified |
| Enterprise / HKS | Shared API chapters or observed menus do not establish VME licensing, enabled features or Kubernetes availability |

These are reasons to discover the live build/layout and retrieve matching
documentation, not host command recipes. This package includes no host
configuration or recovery instructions. If MCP cannot expose a required layer,
request narrowly scoped administrator evidence.

For each new claim save privately: title, URL, source version/commit, retrieval
time, relevant section, evidence kind, applicability and unresolved conflict.
Neither API docs nor schema metadata alone proves live permission or outcome.
