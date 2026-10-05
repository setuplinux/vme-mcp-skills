"""Package integrity checks; scenario structure is not model-behavior validation."""
import json
import pathlib
import re
import unittest
import urllib.parse


SKILL = pathlib.Path(__file__).resolve().parents[1]
ROOT = SKILL.parents[1]


class PackageTests(unittest.TestCase):
    def test_frontmatter_and_entrypoint_budget(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n", text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), SKILL.name)
        self.assertLessEqual(len(match.group(1)), 64)
        self.assertTrue(1 <= len(match.group(2)) <= 1024)
        self.assertLess(len(text.splitlines()), 150)

    def test_all_local_markdown_links_exist(self):
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                parsed = urllib.parse.urlsplit(target)
                if parsed.scheme or target.startswith("#"):
                    continue
                with self.subTest(file=str(path.relative_to(ROOT)), target=target):
                    resolved = (path.parent / urllib.parse.unquote(parsed.path)).resolve()
                    self.assertTrue(resolved.is_relative_to(ROOT.resolve()))
                    self.assertTrue(resolved.is_file())

    def test_scenarios_are_explicitly_offline_and_have_references(self):
        data = json.loads((SKILL / "tests" / "scenarios.json").read_text(encoding="utf-8"))
        self.assertIn("synthetic offline", data["provenance"])
        ids = [case["id"] for key in ("probe_cases", "manual_cases") for case in data[key]]
        self.assertEqual(len(ids), len(set(ids)))
        for case in data["manual_cases"]:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["input"])
                self.assertGreater(len(case["expect"]), 40)
                self.assertTrue((SKILL / case["reference"]).is_file())

    def test_required_scenario_topics_present(self):
        data = json.loads((SKILL / "tests" / "scenarios.json").read_text(encoding="utf-8"))
        actual = {case["id"] for cases in (data["manual_cases"], data["probe_cases"]) for case in cases}
        required = {
            "advertised-not-callable", "ignored-limit", "ignored-filter",
            "partial-pagination", "nested-compacted-history", "inaccessible-artifact",
            "license-denial", "success-enclosing-failure",
            "historical-current-name-collision", "documentation-js-shell",
            "candidate-route-not-exposed", "substituted-read", "timed-out-write",
        }
        self.assertTrue(required <= actual)


if __name__ == "__main__":
    unittest.main()
