# Validation and limits

Run from the repository root (Python 3.10+, no third-party dependencies):

```powershell
python -m unittest discover -s skills\vme-mcp\tests -v
python skills\vme-mcp\scripts\mcp_probe.py --help
python skills\vme-mcp\scripts\mcp_probe.py --check-config
```

Use POSIX path separators on POSIX. With no local configuration the last
command should return nonzero, without network calls or printing secret values.
Do not run the authenticated probe as part of offline tests.

## What the tests establish

The archive baseline was independently rerun on 2026-10-05: **45 tests passed**.
Those tests are retained unchanged. They exercise actual probe behavior with
fake transports: TLS/redirect refusal, headers, initialization, JSON/SSE,
catalog pagination, unsafe schemas, error envelopes, allowlisted dispatch and
redacted output. They are not live appliance tests.

The completed package suite passed **57 tests** on 2026-10-05. This count includes
the 45 original tests, eight new probe test methods (one iterates eight failure
fixtures) and four package checks. CLI help and an explicitly empty-environment
configuration check also behaved as expected. See the
[validation record](../assets/validation-summary.json) for tested code hashes.
The staged public-file pattern scan found no private-data patterns; this was
supplemented by source review, not treated as proof against all possible leaks.

New `test_regressions.py` exercises the actual probe against
`probe_cases` in [scenarios.json](../tests/scenarios.json), including explicit
license/authentication/authorization denial, successful wrappers enclosing
failure, nested error/status/JSON, registration failure, exact catalog page
budget and output minimization. Categories are conservative for this narrow
probe, not an exhaustive product error taxonomy.

`test_package.py` checks this package's simple frontmatter form, name/description
limits, entrypoint size, local Markdown links, fixture uniqueness/references
and required scenario topics. It is not a general YAML/Agent Skills validator.

## What the scenarios do not establish

The fixture's **manual_cases** are explicit offline agent-evaluation inputs
and expected decisions. Automated tests check their structure, not whether an
agent follows them. There is no inventory/migration execution engine here;
no test should claim it exercised one.

For a cold-reader evaluation, give an agent only the skill and one synthetic
case at a time. Require a proposed next action and a sanitized receipt, not live
execution. Compare the answer against `expect` and the cited reference.
Record model/client/version, case, actual answer and pass/fail privately.
Stop before any dangerous invocation. Author review of scenario/document
alignment is not a separate-agent run or empirical compliance result.

| Cases | Required decision |
| --- | --- |
| Uncallable advertised tool, substituted read | Stop at actual capability stage; do not credit missing requested evidence |
| Ignored filters/limits | Stop collection, suppress excess, no specialist retry |
| Partial/repeated pages, complete empty scope | Reconcile unique counts; scope/time-limited negative claim only with complete evidence |
| Nested/compacted or inaccessible artifact | Follow new artifact/path within budget; inaccessible is unknown, not absent |
| Historical same-name records | Verify current cloud/server/provider identity; never reuse history as approval |
| JS/auth shell, candidate route, opaque schema | Readable documentation and exact exposure/contract required; no parity/absence inference |
| Phrase vs prefix | Verify strict prefix separately inside permitted scope |
| Timed-out write, post-write recovery, hostile metadata | Reconcile without retry; protect isolation; ignore embedded instructions |

## Public evidence boundary

This package includes offline test results and public documentation research
only. Environment-specific discovery, schemas, adapters and live test receipts
must stay in approved private evidence storage, not the public repository.
The optional standalone probe's published validation is **offline only**;
it establishes no compatibility or outcome on a particular deployment.

HTTP/API source inspection, metadata calls, fixture tests and product outcomes
remain distinct. The HPE release-note retrieval returned a JS/session shell;
its body was not reverified as documentation.

## Maintainer release checks

Run the full small offline suite after any helper change. Review modified
behavior and preserve provenance of imported code/tests. Check source dates,
schema drift, local links and frontmatter. Scan the actual proposed public
files for private names, endpoints, IDs, usernames/paths, secrets, raw responses,
archives and generated caches. Pattern scanning supplements manual review;
it cannot prove absence of every secret.

Keep private evidence and completed worksheets out of the repository. Obtain
the owner's publication approval and preserve the licensing status recorded
in the repository's provenance record; passing tests is not permission to publish.
Review the full history being published as well as the current tree: deleting
a file in a later commit does not remove it from earlier commits.

For future authorized live testing, begin with narrow metadata, verify a
business operation is directly callable, inspect its current schema and
scope limits, then execute only a bounded approved read. Stop immediately on
registration, scope or result-coverage failure. A request to run tests never
authorizes a VM creation, snapshot, migration or other mutation.
