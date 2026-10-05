# Provenance and reuse status

This local implementation was prepared at the skill owner's request on
2026-10-05. It is not official HPE guidance.

## Owner-supplied archive

Primary source: `vme-mcp.zip`, 51,957 bytes, supplied by the owner for review
and improvement. SHA-256:
`a6b85dc7d8a2677b57274adc22224565e80c77f539f1687864301bc10973d0f3`.

All 19 entries were inspected before private extraction. Absolute/traversal
paths, drive paths, symlinks and oversized entries were rejected by the extraction
procedure. All 18 entries in the enclosed manifest matched their hashes.
No archive, raw evidence, completed worksheets or old validation report is shipped.

Deliberately retained under `skills/vme-mcp`:

| Archive member | Original SHA-256 | Treatment |
| --- | --- | --- |
| `scripts/mcp_probe.py` | `384badeee816008f31903cd55e1180a23f601e79228c726ecd8591ed7c9e1cb8` | Retained health-only implementation; extended failure handling |
| `tests/test_mcp_probe.py` | `67e772adc131fa896072f28684578b11ef73a9d0bc9abce5af87dd850c686b01` | Retained 45 original tests unchanged |

The entry point and references are rewritten from the archive's useful
connection, protocol, change-control, inventory and migration guidance.
New fixtures and tests use synthetic data only. No source-author or copyright
notice was present in the two imported Python files; none was removed.
No LICENSE file or express redistribution grant was found in the archive.
Owner authorization covers this local work, not an inferred open-source license.

## Public administrator source

Reviewed `SKILL.md` and `references/version-capabilities.md` from
[setuplinux/agent-skills](https://github.com/setuplinux/agent-skills/tree/4b425d7f56704c1f5c8dd8dffada201dd6490f24/skills/hpe-vme),
skill revision `4b425d7f56704c1f5c8dd8dffada201dd6490f24` (2026-09-18).
Used the edition/build/layout distinctions, managed-control-plane preference,
exact approvals, confidentiality and actual-user-outcome verification principles.
Host/SSH/libvirt/OS recovery procedures were not imported. That repository was
not modified. Its root listing and license endpoint supplied no license grant.

## Public product references

[Source routing](skills/vme-mcp/references/sources.md) records URLs, retrieval
dates and limits. Product API documentation is cited/summarized, not bundled.
The official Morpheus OpenAPI repository declares Apache-2.0; that does not
license this archive or the administrator skill. No vendor documentation
archive or source tree is redistributed here.

**Publication gate:** have the owner confirm rights and choose any intended
license before pushing or publishing these imported/derived files. Do not
invent attribution, remove a later-discovered notice or assume public visibility
means permission to redistribute. Local implementation and validation do not
resolve that gate.
