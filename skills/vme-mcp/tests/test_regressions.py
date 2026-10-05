"""Offline execution tests for the health probe, not inventory or agent compliance."""
import contextlib
import io
import json
import pathlib
import unittest
from unittest.mock import patch

from test_mcp_probe import ENV, HELPER, LOADER, PING, Fake, p


FIXTURES = json.loads(pathlib.Path(__file__).with_name("scenarios.json").read_text(encoding="utf-8"))


class FailureEnvelopeTests(unittest.TestCase):
    def test_fixture_failures_are_executed_by_probe(self):
        for case in FIXTURES["probe_cases"]:
            with self.subTest(case=case["id"]), self.assertRaises(p.ProbeError) as caught:
                p.Probe(Fake(health=case["response"])).run()
            self.assertEqual(str(caught.exception), case["expected_error"])

    def test_loader_returning_metadata_does_not_establish_callability(self):
        fake = Fake(catalog=[HELPER, LOADER])
        fake.pages = [{"tools": [HELPER, LOADER]}, {"tools": [HELPER, LOADER]}]
        with self.assertRaisesRegex(p.ProbeError, "UNSUPPORTED_CATALOG"):
            p.Probe(fake).run()
        calls = [body.get("params", {}).get("name") for body, _ in fake.calls]
        self.assertIn("use_health_tools", calls)
        self.assertNotIn("get_ping", calls)

    def test_business_dispatch_not_added(self):
        fake = Fake()
        for tool in ("list_servers", "create_migrations", "migrations_run", "delegate_to_specialist"):
            with self.subTest(tool=tool), self.assertRaisesRegex(p.ProbeError, "UNSUPPORTED_CATALOG"):
                p.Probe(fake).call(tool, {})
        self.assertEqual(fake.calls, [])

    def test_error_category_output_does_not_leak_message(self):
        sentinel = "synthetic-sensitive-message"
        fake = Fake(health={"structuredContent": {
            "success": True, "message": "Permission denied " + sentinel}})
        output = io.StringIO()
        with patch.object(p, "Transport", return_value=fake), contextlib.redirect_stdout(output):
            self.assertEqual(p.main([], ENV), 1)
        self.assertEqual(json.loads(output.getvalue()), {"error": "AUTHORIZATION_DENIED"})
        self.assertNotIn(sentinel, output.getvalue())

    def test_explicit_license_beats_generic_error(self):
        fake = Fake(health={"isError": True, "structuredContent": {
            "success": False, "error": "Feature Not Included for the Applied License"}})
        with self.assertRaisesRegex(p.ProbeError, "LICENSE_DENIED"):
            p.Probe(fake).run()

    def test_benign_health_metadata_is_not_a_denial(self):
        fake = Fake(health={"structuredContent": {
            "success": True, "license": {"status": "active"}, "errors": {},
            "message": "Healthy", "buildVersion": "9.0.1"}})
        self.assertTrue(p.Probe(fake).run()["get_ping_success"])

    def test_empty_health_and_transport_version_do_not_prove_build(self):
        fake = Fake(health={"structuredContent": {"success": True}})
        self.assertNotIn("build_version", p.Probe(fake).run())
        with self.assertRaisesRegex(p.ProbeError, "UNVERIFIED_HEALTH"):
            p.Probe(Fake(health={"structuredContent": {}})).run()

    def test_catalog_page_budget_is_exact(self):
        fake = Fake()
        fake.pages = [{"tools": [HELPER], "nextCursor": str(i)} for i in range(p.MAX_PAGES)]
        with self.assertRaisesRegex(p.ProbeError, "PAGINATION_ERROR"):
            p.Probe(fake).run()
        self.assertEqual(sum(body["method"] == "tools/list" for body, _ in fake.calls), p.MAX_PAGES)
        self.assertFalse(any(body.get("params", {}).get("name") == PING["name"] for body, _ in fake.calls))


if __name__ == "__main__":
    unittest.main()
