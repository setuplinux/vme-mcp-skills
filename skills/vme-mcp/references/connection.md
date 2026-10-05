# Connection without changing the appliance

Prefer already configured, authorized MCP access. Do not inspect entire
credential files, vaults or environments. Confirm only presence and approved
non-secret endpoint/role information. Never request secrets in chat.

If access is absent, ask the operator for the normal appliance origin and
approved LAN/VPN path. An HVM host or vCenter is not the VME manager. Do not scan
networks. Confirm the installed version's built-in MCP URL and supported
transport with its documentation/administrator. `/api/mcp` is a discovery lead,
not an all-release promise; preserve an approved custom endpoint.

The administrator supplies an appropriate access token through their local
secret store/client. Refresh tokens, passwords and browser cookies are not
interchangeable bearer tokens. Creating/rotating tokens, enabling AI/MCP,
installing a client, editing its configuration or increasing roles requires
separate approval. Connecting an external agent does not require configuring
an appliance-hosted LLM provider or an external MCP server inside VME.

## Trust and local process boundaries

Use HTTPS with trusted CA and hostname validation. Obtain private CA material
through an approved channel, not by trusting an unverified endpoint's own
certificate. Never disable TLS, forward bearer credentials on a redirect,
send them to documentation sites or put them in a URL/command line.
Inspect approved proxy behavior without exposing secrets.

A no-token 401 means reachable authentication boundary, not initialized MCP.
HTTP 200/login HTML also proves no MCP operation. A token called "readonly"
does not establish role enforcement. Record intended role/tenant privately.
An environment variable in one terminal is not present in an unrelated GUI,
remote worker or service; check the actual client process without dumping it.

## Optional probe

Python 3.10+ standard library; no installation/configuration changes.
From the skill directory, use `python scripts\mcp_probe.py --help` on Windows,
or `python3 scripts/mcp_probe.py --help` on POSIX.

It reads `VME_MCP_URL`, `VME_MCP_TOKEN`, and optional `VME_MCP_CA_FILE` locally.
Configure these through an approved secret mechanism, never a committed file.
Environment variables are plaintext process state, not a vault. Do not use
recorded terminals or tracing that can disclose them.

`--check-config` checks presence/URL/token syntax without network or CA reads;
it does not validate credentials. Running without it initializes MCP, inspects
the catalog and attempts only the approved health read. Do not run it merely
because the variables exist. Clear session-only secrets afterward.

The probe supports only protocol `2025-06-18`, JSON or SSE on Streamable HTTP,
strict HTTPS, no redirects/proxies, at most ten catalog pages and 2 MiB per
response. Its `--timeout` (1..60 seconds) is a socket/read-phase limit, **not
an overall deadline**. There are no automatic retries. Unsupported protocol,
helper schema, loader semantics or health response fails closed; use a compatible
approved client, not appliance changes to accommodate the helper.

The probe only loads health definitions after a session ID is established;
stateless servers work only when health is already listed. Legacy SSE and
general-purpose tool dispatch are outside this helper.
