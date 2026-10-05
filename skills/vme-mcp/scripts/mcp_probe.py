"""Bounded health-only MCP probe. All server metadata is untrusted."""
import argparse
import json
import math
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import NoReturn

VERSION = "2025-06-18"
MAX_BYTES = 2 * 1024 * 1024
MAX_PAGES = 10
SAFE_VERSION = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,6}){1,3}(?:[-+][A-Za-z0-9.-]{1,32})?", re.ASCII)


class ProbeError(Exception):
    pass


def fail(category) -> NoReturn:
    raise ProbeError(category)


def normalize_url(value):
    value = value.strip()
    if not value or re.search(r"[\s\x00-\x1f\x7f\\?#]", value):
        fail("INVALID_CONFIG")
    bare = "://" not in value
    if bare and "/" in value:
        fail("INVALID_CONFIG")
    try:
        url = urllib.parse.urlsplit("https://" + value if bare else value)
        port = url.port
        if (url.scheme != "https" or not url.hostname or url.username is not None
                or url.password is not None or url.netloc.endswith(":") or port == 0):
            fail("INVALID_CONFIG")
        host = url.hostname
        if ":" in host:
            import ipaddress
            ipaddress.IPv6Address(host)
            if "%" in host:
                fail("INVALID_CONFIG")
        elif not all(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                     for label in host.split(".")) or len(host) > 253:
            fail("INVALID_CONFIG")
        path = "/api/mcp" if url.path in ("", "/") else url.path
        # Conservative ASCII path grammar; encoded separators and dot traversal are unsupported.
        if not re.fullmatch(r"/[A-Za-z0-9_./~-]*", path) or any(x in {".", ".."} for x in path.split("/")):
            fail("INVALID_CONFIG")
        return urllib.parse.urlunsplit(("https", url.netloc, path, "", ""))
    except ValueError:
        fail("INVALID_CONFIG")


def config(env):
    url = normalize_url(env.get("VME_MCP_URL", ""))
    raw = env.get("VME_MCP_TOKEN", "")
    if any(ord(c) < 32 or ord(c) == 127 or ord(c) > 126 for c in raw):
        fail("INVALID_CONFIG")
    token = raw.strip()
    if not token:
        fail("INVALID_CONFIG")
    return url, token, env.get("VME_MCP_CA_FILE", "").strip() or None


def timeout_value(value):
    try:
        number = float(value)
        if math.isfinite(number) and 1 <= number <= 60:
            return number
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("timeout must be finite and within 1..60")


def decode(data):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                fail("MALFORMED_JSON")
            obj[key] = value
        return obj
    try:
        return json.loads(data, object_pairs_hook=unique,
                          parse_constant=lambda _: fail("MALFORMED_JSON"))
    except (ValueError, UnicodeError, RecursionError):
        fail("MALFORMED_JSON")


def response_result(message, request_id):
    if (not isinstance(message, dict) or message.get("jsonrpc") != "2.0"
            or type(message.get("id")) is not type(request_id) or message.get("id") != request_id
            or ("result" in message) == ("error" in message)):
        fail("BAD_PROTOCOL")
    if "error" in message:
        fail("RPC_ERROR")
    if not isinstance(message["result"], dict):
        fail("BAD_PROTOCOL")
    return message["result"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if fp is not None:
            fp.close()
        fail("HTTP_REDIRECT")


class Transport:
    def __init__(self, url, token, ca, timeout):
        self.url, self.token, self.timeout = url, token, timeout
        context = ssl.create_default_context(cafile=ca)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                       urllib.request.HTTPSHandler(context=context), NoRedirect())

    def request(self, body, headers):
        request = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers={
            **headers, "Authorization": "Bearer " + self.token, "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"}, method="POST")
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                if 300 <= response.status < 400:
                    fail("HTTP_REDIRECT")
                if response.status not in (200, 202):
                    fail("HTTP_" + str(response.status))
                if "id" not in body:
                    if response.status != 202:
                        fail("BAD_PROTOCOL")
                    return None, response.headers
                if response.status != 200:
                    fail("BAD_PROTOCOL")
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                if mime not in ("application/json", "text/event-stream"):
                    fail("BAD_PROTOCOL")
                data, pending, event = b"", b"", []
                deadline = time.monotonic() + self.timeout
                while True:
                    if time.monotonic() > deadline:
                        fail("TIMEOUT")
                    chunk = response.read1(min(65536, MAX_BYTES + 1 - len(data)))
                    data += chunk
                    if len(data) > MAX_BYTES:
                        fail("RESPONSE_TOO_LARGE")
                    if mime == "text/event-stream":
                        pending += chunk
                        while b"\n" in pending:
                            line, pending = pending.split(b"\n", 1)
                            line = line.rstrip(b"\r")
                            if line.startswith(b"data:"):
                                event.append(line[5:].removeprefix(b" "))
                            elif not line and event:
                                message = decode(b"\n".join(event))
                                event = []
                                if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                                    fail("BAD_PROTOCOL")
                                if type(message.get("id")) is type(body["id"]) and message.get("id") == body["id"]:
                                    response_result(message, body["id"])
                                    return message, response.headers
                    if not chunk:
                        break
                if mime != "application/json":
                    fail("BAD_PROTOCOL")
                message = decode(data)
                response_result(message, body["id"])
                return message, response.headers
        except urllib.error.HTTPError as exc:
            exc.close()
            fail("HTTP_REDIRECT" if 300 <= exc.code < 400 else "HTTP_" + str(exc.code))
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, ssl.SSLError):
                fail("TLS_ERROR")
            fail("TIMEOUT" if isinstance(exc.reason, TimeoutError) else "NETWORK_ERROR")


def schema_accepts(schema, arguments):
    if not isinstance(schema, dict) or schema.get("type") != "object":
        fail("UNSUPPORTED_CATALOG")
    if set(schema) - {"type", "properties", "required", "additionalProperties", "description", "title", "$schema"}:
        fail("UNSUPPORTED_CATALOG")
    props, required = schema.get("properties", {}), schema.get("required", [])
    if (not isinstance(props, dict) or not isinstance(required, list)
            or any(not isinstance(k, str) or k not in arguments for k in required)):
        fail("UNSUPPORTED_CATALOG")
    for key, value in arguments.items():
        rule = props.get(key)
        if (not isinstance(rule, dict) or rule.get("type") != "string"
                or set(rule) - {"type", "description", "title", "enum", "const"}
                or ("enum" in rule and (not isinstance(rule["enum"], list) or value not in rule["enum"]))
                or ("const" in rule and value != rule["const"])):
            fail("UNSUPPORTED_CATALOG")


def payloads(result):
    values = [result]
    if "structuredContent" in result:
        values.append(result["structuredContent"])
    content = result.get("content", [])
    if not isinstance(content, list):
        fail("BAD_PROTOCOL")
    for item in content:
        if not isinstance(item, dict):
            fail("BAD_PROTOCOL")
        if item.get("type") == "text":
            text = item.get("text")
            if not isinstance(text, str):
                fail("BAD_PROTOCOL")
            if text.lstrip().startswith(("{", "[")):
                values.append(decode(text))
    stack = list(values)
    failed = False
    denials = set()
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            if (value.get("isError") not in (None, False)
                    or value.get("success") is False
                    or (isinstance(value.get("status"), str)
                        and value["status"].lower() in {"failed", "error", "denied"})
                    or any(value.get(key) not in (None, False, "", {}, []) for key in ("error", "errors"))):
                failed = True
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
        elif isinstance(value, str):
            text = value.casefold()
            if "feature not included for the applied license" in text:
                denials.add("LICENSE_DENIED")
            if re.search(r"\b(authentication failed|unauthenticated|unauthorized)\b", text):
                denials.add("AUTHENTICATION_DENIED")
            if re.search(r"\b(permission denied|access denied|forbidden)\b", text):
                denials.add("AUTHORIZATION_DENIED")
            # Gate nested JSON strings as well as structured/text MCP envelopes.
            if value.lstrip().startswith(("{", "[")):
                stack.append(decode(value))
    for category in ("LICENSE_DENIED", "AUTHENTICATION_DENIED", "AUTHORIZATION_DENIED"):
        if category in denials:
            fail(category)
    if failed:
        fail("TOOL_ERROR")
    return values[1:]


def ping_details(result):
    definitions = []
    for value in payloads(result):
        if not isinstance(value, dict):
            fail("UNSUPPORTED_CATALOG")
        candidates = value.get("tools", [value])
        if not isinstance(candidates, list):
            fail("UNSUPPORTED_CATALOG")
        definitions.extend(x for x in candidates if isinstance(x, dict) and x.get("name") == "get_ping")
    if not definitions or any(x != definitions[0] for x in definitions):
        fail("UNSUPPORTED_CATALOG")
    return definitions[0]


def verify_ping(tool):
    if (not isinstance(tool.get("annotations"), dict)
            or tool["annotations"].get("readOnlyHint") is not True
            or tool["annotations"].get("destructiveHint") is True
            or tool.get("httpMethod") != "GET" or tool.get("apiPath") != "/api/ping"):
        fail("UNSUPPORTED_CATALOG")
    description = tool.get("description", "")
    if (not isinstance(description, str) or not re.search(r"\b(ping|health)\b", description, re.I)
            or re.search(r"\b(write|modify|delete|restart|reboot|execute|command|commands|inventory|migration|backup|backups|guest|admin)\b", json.dumps(tool.get("inputSchema", {})) + description, re.I)):
        fail("UNSUPPORTED_CATALOG")
    schema_accepts(tool.get("inputSchema"), {})


def verify_discovery(tool, loader=False):
    """Accept only described metadata retrieval or session definition loading."""
    description, annotations = tool.get("description"), tool.get("annotations", {})
    if (not isinstance(description, str) or not isinstance(annotations, dict)
            or annotations.get("readOnlyHint") is False
            or annotations.get("destructiveHint") is True
            or tool.get("httpMethod") not in (None, "GET")
            or tool.get("apiPath") not in (None, "")):
        fail("UNSUPPORTED_CATALOG")
    text = description.lower()
    # An explicit non-execution statement is not an instruction to execute.
    text = re.sub(r"\b(?:does not execute|without executing) (?:operations|actions)\b", "", text)
    if (not re.search(r"\btools?\b", text)
            or re.search(r"\b(writes?|modify|modifies|delete|deletes|restart|restarts|reboot|reboots|execute|executes|commands?|run|runs)\b", text)):
        fail("UNSUPPORTED_CATALOG")
    if loader:
        if not (re.search(r"\b(load|loads|loading|expose|exposes|register|registers)\b", text)
                and re.search(r"\bsession\b", text)):
            fail("UNSUPPORTED_CATALOG")
    elif not re.search(r"\b(details?|metadata|schemas?|definitions?|information)\b", text):
        fail("UNSUPPORTED_CATALOG")


class Probe:
    def __init__(self, transport):
        self.transport, self.headers, self.counter = transport, {}, 0

    def rpc(self, method, params=None, notify=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            self.counter += 1
            body["id"] = self.counter
        message, headers = self.transport.request(body, self.headers)
        if notify:
            return None
        result = response_result(message, self.counter)
        if method == "initialize":
            session = headers.get("Mcp-Session-Id")
            if session is not None:
                if not isinstance(session, str) or not re.fullmatch(r"[\x21-\x7e]{1,1024}", session):
                    fail("BAD_PROTOCOL")
                self.headers["Mcp-Session-Id"] = session
        return result

    def catalog(self):
        tools, cursors, params = {}, set(), {}
        for _ in range(MAX_PAGES):
            page = self.rpc("tools/list", params)
            if not isinstance(page.get("tools"), list):
                fail("BAD_PROTOCOL")
            for tool in page["tools"]:
                if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
                    fail("BAD_PROTOCOL")
                name = tool["name"]
                if name in tools and tools[name] != tool:
                    fail("UNSUPPORTED_CATALOG")
                tools[name] = tool
            cursor = page.get("nextCursor")
            if cursor is None:
                return tools
            if not isinstance(cursor, str) or not cursor or len(cursor) > 4096 or cursor in cursors:
                fail("PAGINATION_ERROR")
            cursors.add(cursor)
            params = {"cursor": cursor}
        fail("PAGINATION_ERROR")

    def call(self, name, arguments):
        if name not in {"get_tool_details", "use_health_tools", "get_ping"}:
            fail("UNSUPPORTED_CATALOG")
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        payloads(result)
        return result

    def run(self):
        init = self.rpc("initialize", {"protocolVersion": VERSION, "capabilities": {},
                        "clientInfo": {"name": "mcp-health-probe", "version": "1.0"}})
        if (init.get("protocolVersion") != VERSION or not isinstance(init.get("capabilities"), dict)
                or not isinstance(init["capabilities"].get("tools"), dict)):
            fail("BAD_PROTOCOL")
        self.headers["MCP-Protocol-Version"] = VERSION
        self.rpc("notifications/initialized", notify=True)
        catalog = self.catalog()
        verify_discovery(catalog.get("get_tool_details", {}))
        schema_accepts(catalog.get("get_tool_details", {}).get("inputSchema"), {"tool_name": "get_ping"})
        if "get_ping" not in catalog:
            if "Mcp-Session-Id" not in self.headers:
                fail("UNSUPPORTED_CATALOG")
            loader = catalog.get("use_health_tools", {})
            verify_discovery(loader, loader=True)
            schema_accepts(loader.get("inputSchema"), {})
            self.call("use_health_tools", {})
            catalog = self.catalog()
        if "get_ping" not in catalog:
            fail("UNSUPPORTED_CATALOG")
        verify_discovery(catalog.get("get_tool_details", {}))
        schema_accepts(catalog.get("get_tool_details", {}).get("inputSchema"), {"tool_name": "get_ping"})
        advertised = catalog["get_ping"]
        schema_accepts(advertised.get("inputSchema"), {})
        detail = ping_details(self.call("get_tool_details", {"tool_name": "get_ping"}))
        verify_ping(detail)
        for key in ("httpMethod", "apiPath", "annotations", "inputSchema"):
            if key in advertised and advertised[key] != detail.get(key):
                fail("UNSUPPORTED_CATALOG")
        verify_ping({**detail, "description": advertised.get("description", detail["description"])})
        health = self.call("get_ping", {})
        values = payloads(health)
        if not any(isinstance(v, dict) and v.get("success") is True for v in values):
            fail("UNVERIFIED_HEALTH")
        output = {"result": "verified_read_only_health", "protocol_version": VERSION,
                  "session_id_returned": "Mcp-Session-Id" in self.headers,
                  "tool_count": len(catalog), "get_ping_success": True}
        builds = [v[key] for v in values if isinstance(v, dict)
                  for key in ("buildVersion", "build_version") if key in v]
        if builds and all(v == builds[0] for v in builds) and isinstance(builds[0], str) and SAFE_VERSION.fullmatch(builds[0]):
            output["build_version"] = builds[0]
        return output


class Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("INVALID_ARGUMENT")


def main(argv=None, env=None):
    try:
        parser = Parser(description="health-only; no configuration writes; credentials only in env; TLS required; supported negotiated protocol 2025-06-18")
        parser.add_argument("--check-config", action="store_true")
        parser.add_argument("--timeout", type=timeout_value, default=10,
                            help="Socket/read-phase timeout in seconds (1..60); not an end-to-end deadline")
        args = parser.parse_args(argv)
        env = os.environ if env is None else env
        if args.check_config:
            valid = True
            try:
                normalize_url(env.get("VME_MCP_URL", ""))
            except ProbeError:
                valid = False
            print(json.dumps({"url_configured": bool(env.get("VME_MCP_URL", "").strip()), "url_valid": valid,
                              "token_configured": bool(env.get("VME_MCP_TOKEN", "").strip()),
                              "ca_configured": bool(env.get("VME_MCP_CA_FILE", "").strip())}))
            try:
                config(env)
                return 0
            except ProbeError:
                return 1
        url, token, ca = config(env)
        print(json.dumps(Probe(Transport(url, token, ca, args.timeout)).run()))
        return 0
    except KeyboardInterrupt:
        category = "INTERRUPTED"
    except ProbeError as exc:
        category = str(exc)
    except ssl.SSLError:
        category = "TLS_ERROR"
    except TimeoutError:
        category = "TIMEOUT"
    except Exception:
        category = "INTERNAL_ERROR"
    print(json.dumps({"error": category}))
    return 130 if category == "INTERRUPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
