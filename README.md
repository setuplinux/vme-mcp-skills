# vme-mcp-skills

Unofficial, portable MCP-only guidance for HPE Morpheus VM Essentials (VME).
Start with [the skill](skills/vme-mcp/SKILL.md), not the optional script.
Give a compatible agent the complete `skills/vme-mcp` folder and an already
authorized MCP connection. Installing/reading a skill grants no permissions and
does not configure a client or appliance.

The core covers discovery, ordinary operations, inventory, troubleshooting and
migration assessment. Keep environment-specific adapters, connection details,
inventory and live test receipts outside this public package.
Public API research is allowed; target execution stays on MCP. This is not the
separate all-access [administrator skill](https://github.com/setuplinux/agent-skills/tree/main/skills/hpe-vme).

## Local validation

Python 3.10+; standard library only. From this repository in PowerShell:

```powershell
python -m unittest discover -s skills\vme-mcp\tests -v
python skills\vme-mcp\scripts\mcp_probe.py --help
python skills\vme-mcp\scripts\mcp_probe.py --check-config
```

On POSIX shells use `/` instead of `\` in filesystem paths. Tests are offline.
`--check-config` reports presence/validity, makes no network requests and exits
nonzero when configuration is missing. Running the probe without that flag is
an authenticated **health-only** MCP operation requiring prior scope/TLS checks;
it is not inventory or a migration-readiness test.

See [validation and scenario limits](skills/vme-mcp/references/validation.md)
and [provenance/reuse status](PROVENANCE.md). No vendor endorsement or support
promise. Published with the owner's authorization; no open-source license has
been selected. Public visibility does not itself grant redistribution rights.
