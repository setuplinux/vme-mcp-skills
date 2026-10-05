"""Synthetic protocol tests only; no live appliance evidence."""
import contextlib
import importlib.util
import io
import json
import pathlib
import ssl
import unittest
import urllib.error
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "mcp_probe", pathlib.Path(__file__).resolve().parents[1] / "scripts/mcp_probe.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)

SECRET = "private-secret"
ENV = {"VME_MCP_URL": "example.invalid", "VME_MCP_TOKEN": SECRET}
HELPER = {"name": "get_tool_details", "description": "Get tool metadata and input schemas.", "inputSchema": {
    "type": "object", "properties": {"tool_name": {"type": "string"}},
    "required": ["tool_name"], "additionalProperties": False}}
PING = {"name": "get_ping", "description": "Read appliance health ping",
        "annotations": {"readOnlyHint": True}, "httpMethod": "GET",
        "apiPath": "/api/ping", "inputSchema": {"type": "object", "properties": {}}}
LOADER = {"name": "use_health_tools",
          "description": "Loads tool definitions for this session only; does not execute operations.",
          "inputSchema": {"type": "object", "properties": {}}}


def clone(value):
    return json.loads(json.dumps(value))


class Fake:
    def __init__(self, catalog=None, details=None, health=None):
        self.catalog = catalog if catalog is not None else [HELPER, PING]
        self.details = details if details is not None else {"structuredContent": PING}
        self.health = health if health is not None else {"structuredContent": {"success": True, "build_version": "1.2.3"}}
        self.calls = []
        self.init = {"protocolVersion": p.VERSION, "capabilities": {"tools": {}},
                     "serverInfo": {"version": "not-an-appliance-build"}}
        self.pages = []

    def request(self, body, headers):
        self.calls.append((clone(body), dict(headers)))
        method = body["method"]
        if method == "initialize":
            result = self.init
        elif method == "notifications/initialized":
            return None, {}
        elif method == "tools/list":
            result = self.pages.pop(0) if self.pages else {"tools": self.catalog}
        else:
            name = body["params"]["name"]
            assert name in {"get_tool_details", "use_health_tools", "get_ping"}
            if name == "get_tool_details":
                result = self.details
            elif name == "use_health_tools":
                self.catalog = [HELPER, PING, LOADER]
                result = {"content": []}
            else:
                result = self.health
        return {"jsonrpc": "2.0", "id": body["id"], "result": result}, {"Mcp-Session-Id": SECRET}


class Response(io.BytesIO):
    def __init__(self, body, mime="application/json", status=200):
        super().__init__(body)
        self.headers = {"Content-Type": mime}
        self.status = status


class ConfigTests(unittest.TestCase):
    def test_valid_urls(self):
        for value, expected in [("example.invalid", "https://example.invalid/api/mcp"),
                                ("https://example.invalid", "https://example.invalid/api/mcp"),
                                ("https://example.invalid/api/mcp", "https://example.invalid/api/mcp"),
                                ("https://example.invalid:8443/custom/mcp", "https://example.invalid:8443/custom/mcp")]:
            self.assertEqual(p.normalize_url(value), expected)

    def test_invalid_urls(self):
        for value in ["http://example.invalid", "https://user:pass@example.invalid", "https://example.invalid?q=x",
                      "https://example.invalid#x", "https://example.invalid:99999", "https://example.invalid:bad",
                      "https://example.invalid:", "https://bad host", "https:///x", "example.invalid/path",
                      "https://example.invalid/../x", "https://example.invalid/%0a", "https://example.invalid?",
                      "https://example.invalid\\evil", "https://example.invalid/#"]:
            with self.subTest(value=value), self.assertRaises(p.ProbeError):
                p.normalize_url(value)

    def test_token_validation(self):
        for value in ["x\ny", "x\ry", "x\ty", "x\x00y", "x\x7fy"]:
            with self.assertRaises(p.ProbeError):
                p.config({**ENV, "VME_MCP_TOKEN": value})
        self.assertEqual(p.config({**ENV, "VME_MCP_TOKEN": "  abc  "})[1], "abc")

    def test_timeout(self):
        for value in ["nan", "inf", "-inf", "0", "61", "oops"]:
            with self.assertRaises(Exception):
                p.timeout_value(value)
        self.assertEqual(p.timeout_value("1.5"), 1.5)

    def test_check_config_no_network_or_ca_read(self):
        out = io.StringIO()
        with patch.object(p, "Transport", side_effect=AssertionError), patch.object(p.ssl, "create_default_context", side_effect=AssertionError):
            with contextlib.redirect_stdout(out):
                code = p.main(["--check-config"], {**ENV, "VME_MCP_CA_FILE": "/private/ca"})
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue()), {"url_configured": True, "url_valid": True, "token_configured": True, "ca_configured": True})
        self.assertNotIn(SECRET, out.getvalue())
        self.assertNotIn("/private", out.getvalue())

    def test_missing_invalid_prerequisites(self):
        for env in [{}, {**ENV, "VME_MCP_TOKEN": "a\nb"}, {**ENV, "VME_MCP_URL": "http://bad"}]:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertNotEqual(p.main(["--check-config"], env), 0)

    def test_boundary_redaction(self):
        for exc, category in [(RuntimeError(SECRET), "INTERNAL_ERROR"), (ssl.SSLError(SECRET), "TLS_ERROR"),
                              (TimeoutError(SECRET), "TIMEOUT")]:
            out = io.StringIO()
            with patch.object(p, "Transport", side_effect=exc), contextlib.redirect_stdout(out):
                self.assertNotEqual(p.main([], ENV), 0)
            self.assertNotIn(SECRET, out.getvalue())
            self.assertIn(category, out.getvalue())

    def test_help(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            p.main(["--help"], {})
        for term in ["health-only", "TLS", "env", "2025-06-18", "no configuration writes"]:
            self.assertIn(term, out.getvalue())

    def test_cli_rejects_secret_arguments(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertNotEqual(p.main(["--token", SECRET], ENV), 0)
        self.assertEqual(json.loads(out.getvalue()), {"error": "INVALID_ARGUMENT"})

    def test_keyboard_interrupt(self):
        with patch.object(p, "Transport", side_effect=KeyboardInterrupt), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(p.main([], ENV), 130)


class ProtocolTests(unittest.TestCase):
    def run_fake(self, fake):
        return p.Probe(fake).run()

    def assert_stops(self, fake, category="UNSUPPORTED_CATALOG"):
        with self.assertRaises(p.ProbeError) as caught:
            self.run_fake(fake)
        self.assertEqual(str(caught.exception), category)
        self.assertNotIn("get_ping", [b.get("params", {}).get("name") for b, _ in fake.calls])

    def test_success_allowlist_headers(self):
        fake = Fake(catalog=[HELPER, PING, PING])
        result = self.run_fake(fake)
        self.assertEqual(result, {"result": "verified_read_only_health", "protocol_version": p.VERSION,
                                 "session_id_returned": True, "tool_count": 2, "get_ping_success": True, "build_version": "1.2.3"})
        self.assertEqual(fake.calls[0][0]["params"], {"protocolVersion": p.VERSION, "capabilities": {}, "clientInfo": {"name": "mcp-health-probe", "version": "1.0"}})
        self.assertEqual(fake.calls[1][0]["method"], "notifications/initialized")
        self.assertNotIn("id", fake.calls[1][0])
        for _, headers in fake.calls[1:]:
            self.assertEqual(headers, {"MCP-Protocol-Version": p.VERSION, "Mcp-Session-Id": SECRET})
        self.assertEqual([b["method"] for b, _ in fake.calls], ["initialize", "notifications/initialized", "tools/list", "tools/call", "tools/call"])

    def test_loader(self):
        fake = Fake(catalog=[HELPER, LOADER])
        self.run_fake(fake)
        self.assertEqual([b.get("params", {}).get("name") for b, _ in fake.calls if b["method"] == "tools/call"], ["use_health_tools", "get_tool_details", "get_ping"])
        self.assertEqual(sum(b["method"] == "tools/list" for b, _ in fake.calls), 2)

    def test_missing_helper_and_uncertain_loader(self):
        for catalog in [[PING], [HELPER], [HELPER, {**LOADER, "description": "Enable health tools"}],
                        [HELPER, {**LOADER, "name": "use_admin_tools"}]]:
            self.assert_stops(Fake(catalog=catalog))

    def test_forbidden_mapping_or_description(self):
        for changes in [{"httpMethod": "POST"}, {"apiPath": "/api/inventory"}, {"annotations": {}},
                        {"description": "Read health and execute guest commands"}]:
            self.assert_stops(Fake(details={"structuredContent": {**PING, **changes}}))

    def test_required_arguments_and_helper_schema(self):
        required = {"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]}
        self.assert_stops(Fake(details={"structuredContent": {**PING, "inputSchema": required}}))
        self.assert_stops(Fake(catalog=[{**HELPER, "inputSchema": required}, PING]))
        self.assert_stops(Fake(catalog=[HELPER, {**LOADER, "inputSchema": required}]))

    def test_details_shapes(self):
        for details in [{"content": [{"type": "text", "text": json.dumps(PING)}]},
                        {"structuredContent": {"tools": [{"name": "other"}, PING]}}]:
            self.assertTrue(self.run_fake(Fake(details=details))["get_ping_success"])
        for details in [{"structuredContent": {"nested": PING}}, {"structuredContent": {"tools": [PING, {**PING, "httpMethod": "POST"}]}}]:
            self.assert_stops(Fake(details=details))

    def test_pagination(self):
        fake = Fake()
        fake.pages = [{"tools": [HELPER], "nextCursor": "next"}, {"tools": [PING, HELPER]}]
        self.assertEqual(self.run_fake(fake)["tool_count"], 2)
        self.assertEqual(fake.calls[3][0]["params"], {"cursor": "next"})

    def test_pagination_limits(self):
        for pages in [[{"tools": [HELPER], "nextCursor": "x"}] * 2,
                      [{"tools": [], "nextCursor": str(i)} for i in range(11)]]:
            fake = Fake()
            fake.pages = pages
            self.assert_stops(fake, "PAGINATION_ERROR")

    def test_protocol_capability(self):
        for changes in [{"protocolVersion": "2024-11-05"}, {"capabilities": {}}, {"capabilities": {"tools": False}}]:
            fake = Fake()
            fake.init.update(changes)
            self.assert_stops(fake, "BAD_PROTOCOL")

    def test_product_errors(self):
        for result in [{"isError": True}, {"structuredContent": {"success": False}},
                       {"content": [{"type": "text", "text": '{"data":{"error":"private-secret"}}'}]}]:
            with self.assertRaisesRegex(p.ProbeError, "TOOL_ERROR"):
                self.run_fake(Fake(health=result))

    def test_build_filter(self):
        for build in [SECRET, "1.2.3\nsecret", "<script>", 123]:
            result = self.run_fake(Fake(health={"structuredContent": {"success": True, "build_version": build}}))
            self.assertNotIn("build_version", result)

    def test_conflicting_catalog_and_metadata(self):
        self.assert_stops(Fake(catalog=[HELPER, PING, {**PING, "apiPath": "/api/other"}]))
        self.assert_stops(Fake(details={"structuredContent": {**PING, "annotations": None}}))
        self.assert_stops(Fake(catalog=[HELPER, {**LOADER, "annotations": {"destructiveHint": True}}]))
        self.assert_stops(Fake(details={"structuredContent": PING, "content": [
            {"type": "text", "text": json.dumps({**PING, "httpMethod": "POST"})}]}))

    def test_helper_constraints(self):
        for rule in [{"type": "string", "enum": ["other"]}, {"type": "string", "pattern": ".*"}]:
            helper = clone(HELPER)
            helper["inputSchema"]["properties"]["tool_name"] = rule
            self.assert_stops(Fake(catalog=[helper, PING]))

    def test_session_absent_and_invalid(self):
        for session in [None, "bad\nheader"]:
            fake = Fake()
            original = fake.request
            def request(body, headers):
                message, _ = original(body, headers)
                return message, {} if session is None else {"Mcp-Session-Id": session}
            fake.request = request
            if session is None:
                self.assertFalse(self.run_fake(fake)["session_id_returned"])
            else:
                self.assert_stops(fake, "BAD_PROTOCOL")


class TransportTests(unittest.TestCase):
    def request(self, response):
        with patch.object(p.urllib.request.OpenerDirector, "open", return_value=response):
            return p.Transport("https://example.invalid/api/mcp", SECRET, None, 2).request({"jsonrpc": "2.0", "id": 7, "method": "tools/list"}, {})

    def test_json(self):
        body = {"jsonrpc": "2.0", "id": 7, "result": {}}
        self.assertEqual(self.request(Response(json.dumps(body).encode()))[0], body)

    def test_sse(self):
        body = b': keepalive\r\n\r\ndata: {"jsonrpc":"2.0","method":"notice"}\n\ndata: {"jsonrpc":"2.0","id":8,"result":{}}\n\ndata: {"jsonrpc":"2.0",\ndata: "id":7,"result":{}}\n\n'
        self.assertEqual(self.request(Response(body, "text/event-stream"))[0]["id"], 7)

    def test_bad_json_protocol_and_rpc_error(self):
        for body, category in [(b'{', "MALFORMED_JSON"), (b'{"jsonrpc":"1.0","id":7,"result":{}}', "BAD_PROTOCOL"),
                               (b'{"jsonrpc":"2.0","id":8,"result":{}}', "BAD_PROTOCOL"),
                               (b'{"jsonrpc":"2.0","id":7,"error":{"message":"private-secret"}}', "RPC_ERROR")]:
            with self.assertRaisesRegex(p.ProbeError, category):
                self.request(Response(body))

    def test_size_bound(self):
        with self.assertRaisesRegex(p.ProbeError, "RESPONSE_TOO_LARGE"):
            self.request(Response(b' ' * (p.MAX_BYTES + 1)))

    def test_duplicate_json_keys(self):
        with self.assertRaisesRegex(p.ProbeError, "MALFORMED_JSON"):
            self.request(Response(b'{"jsonrpc":"2.0","id":7,"result":{},"result":{"success":false}}'))

    def test_sse_size_bound_and_media_type(self):
        with self.assertRaisesRegex(p.ProbeError, "RESPONSE_TOO_LARGE"):
            self.request(Response(b':' * (p.MAX_BYTES + 1), "text/event-stream"))
        with self.assertRaisesRegex(p.ProbeError, "BAD_PROTOCOL"):
            self.request(Response(b'private-secret', "text/html"))

    def test_redirect_does_not_forward(self):
        handler = p.NoRedirect()
        request = p.urllib.request.Request("https://example.invalid", headers={"Authorization": "Bearer " + SECRET})
        with self.assertRaisesRegex(p.ProbeError, "HTTP_REDIRECT"):
            handler.redirect_request(request, None, 302, "private-secret", {}, "https://example.invalid/next")
        with patch.object(p.urllib.request.OpenerDirector, "open", side_effect=urllib.error.HTTPError("private-secret", 302, SECRET, {}, None)) as opened:
            with self.assertRaisesRegex(p.ProbeError, "HTTP_REDIRECT"):
                p.Transport("https://example.invalid", SECRET, None, 2).request({"id": 7}, {})
            self.assertEqual(opened.call_count, 1)

    def test_proxy_disabled(self):
        with patch.object(p.urllib.request, "build_opener") as builder:
            p.Transport("https://example.invalid", SECRET, None, 2)
            self.assertEqual(builder.call_args.args[0].proxies, {})

    def test_tls_timeout_http(self):
        for exc, category in [(urllib.error.URLError(ssl.SSLError(SECRET)), "TLS_ERROR"),
                              (urllib.error.URLError(TimeoutError(SECRET)), "TIMEOUT")]+[
                                  (urllib.error.HTTPError(SECRET, code, SECRET, {}, None), "HTTP_" + str(code))
                                  for code in [401, 403, 404, 429, 500, 503]]:
            with patch.object(p.urllib.request.OpenerDirector, "open", side_effect=exc) as opened:
                with self.assertRaisesRegex(p.ProbeError, category):
                    p.Transport("https://example.invalid", SECRET, None, 2).request({"id": 7}, {})
                self.assertEqual(opened.call_count, 1)

    def test_bodyless_notification(self):
        with patch.object(p.urllib.request.OpenerDirector, "open", return_value=Response(b'', status=202)):
            self.assertIsNone(p.Transport("https://example.invalid", SECRET, None, 2).request({"method": "notifications/initialized"}, {})[0])


class RegressionTests(unittest.TestCase):
    def test_root_url_slash_is_appliance_base(self):
        self.assertEqual(p.normalize_url("https://example.invalid/"), "https://example.invalid/api/mcp")

    def test_health_requires_explicit_success(self):
        for result in [{}, {"content": []}, {"structuredContent": {}},
                       {"structuredContent": {"success": "true"}},
                       {"content": [{"type": "text", "text": "permission denied"}]}]:
            with self.subTest(result=result), self.assertRaises(p.ProbeError):
                p.Probe(Fake(health=result)).run()

    def test_actual_camelcase_build_field(self):
        fake = Fake(health={"structuredContent": {"success": True, "buildVersion": "9.0.0"}})
        self.assertEqual(p.Probe(fake).run().get("build_version"), "9.0.0")

    def test_loader_accepts_clear_non_magic_metadata(self):
        loader = {**LOADER, "description": "Load health tool definitions into the current session only."}
        self.assertTrue(p.Probe(Fake(catalog=[HELPER, loader])).run()["get_ping_success"])

    def test_helper_conflicting_effect_never_called(self):
        for extra in [{"description": "Get tool metadata and restart the appliance."},
                      {"annotations": {"readOnlyHint": False}},
                      {"annotations": {"destructiveHint": True}},
                      {"httpMethod": "POST", "apiPath": "/api/restart"}]:
            fake = Fake(catalog=[{**HELPER, **extra}, PING])
            with self.subTest(extra=extra), self.assertRaises(p.ProbeError):
                p.Probe(fake).run()
            self.assertFalse(any(b.get("params", {}).get("name") == "get_tool_details" for b, _ in fake.calls))

    def test_loader_contradictory_effect_never_called(self):
        for extra in [{"description": "Load health tool definitions into this session and restart the appliance."},
                      {"annotations": {"readOnlyHint": False}}]:
            fake = Fake(catalog=[HELPER, {**LOADER, **extra}])
            with self.subTest(extra=extra), self.assertRaises(p.ProbeError):
                p.Probe(fake).run()
            self.assertFalse(any(b.get("params", {}).get("name") == "use_health_tools" for b, _ in fake.calls))


class ReviewRegressionTests(unittest.TestCase):
    def test_loader_needs_established_session(self):
        fake = Fake(catalog=[HELPER, LOADER])
        original = fake.request
        def stateless(body, headers):
            message, _ = original(body, headers)
            return message, {}
        with patch.object(fake, "request", side_effect=stateless):
            with self.assertRaises(p.ProbeError):
                p.Probe(fake).run()
        self.assertFalse(any(b.get("params", {}).get("name") == "use_health_tools" for b, _ in fake.calls))

    def test_array_wrapped_conflicting_details_fail_closed(self):
        details = {"structuredContent": PING, "content": [
            {"type": "text", "text": json.dumps([{**PING, "httpMethod": "POST"}])}]}
        fake = Fake(details=details)
        with self.assertRaises(p.ProbeError):
            p.Probe(fake).run()
        self.assertFalse(any(b.get("params", {}).get("name") == "get_ping" for b, _ in fake.calls))

    def test_request_response_202_rejected(self):
        response = Response(b'{"jsonrpc":"2.0","id":7,"result":{}}', status=202)
        with patch.object(p.urllib.request.OpenerDirector, "open", return_value=response):
            with self.assertRaisesRegex(p.ProbeError, "BAD_PROTOCOL"):
                p.Transport("https://example.invalid/api/mcp", SECRET, None, 2).request({"id": 7}, {})

    def test_timeout_help_discloses_per_phase_limit(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            p.main(["--help"], {})
        text = " ".join(out.getvalue().split())
        self.assertRegex(text, r"not an end-\s*to-end deadline")

    def test_plural_application_errors_fail_closed(self):
        fake = Fake(health={"structuredContent": {"success": True, "errors": {"health": "unavailable"}}})
        with self.assertRaisesRegex(p.ProbeError, "TOOL_ERROR"):
            p.Probe(fake).run()


if __name__ == "__main__":
    unittest.main()
