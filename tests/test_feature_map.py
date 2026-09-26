"""Tests for feature-map, on invented outlines only."""

import importlib.machinery
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "bin" / "feature-map"
loader = importlib.machinery.SourceFileLoader("feature_map", str(TOOL))
spec_ = importlib.util.spec_from_loader("feature_map", loader)
assert spec_ is not None
fm = importlib.util.module_from_spec(spec_)
loader.exec_module(fm)

OUTLINE = """# Tinytool
> Does small things well
One line about it.

source: the Tinytool help
date: 2 March 2026

## Read
- **open**: open a file
- **peek**: the first lines

## Write
- **save**: write it back
- a plain item with no head

## Later [planned]
- undo
- redo
"""


def spec_from(text):
    return fm.normalise(fm.parse_markdown(text))


def overlaps(a, b):
    return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
                or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])


class Outline(unittest.TestCase):
    def test_reads_every_part(self):
        s = spec_from(OUTLINE)
        self.assertEqual(s["title"], "Tinytool")
        self.assertEqual(s["subtitle"], "Does small things well")
        self.assertEqual(s["source"], "the Tinytool help")
        self.assertEqual([g["name"] for g in s["groups"]], ["Read", "Write", "Later"])
        self.assertTrue(s["groups"][2]["planned"])
        self.assertEqual(s["groups"][0]["items"][0], {"head": "open", "text": "open a file", "planned": False})
        self.assertEqual(s["groups"][1]["items"][1]["text"], "a plain item with no head")

    def test_an_item_can_be_planned_on_its_own(self):
        s = spec_from(OUTLINE.replace("- **peek**: the first lines", "- **peek**: the first lines [planned]"))
        self.assertTrue(s["groups"][0]["items"][1]["planned"])

    def test_json_says_the_same_thing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.json"
            p.write_text(json.dumps({"title": "T", "source": "s", "groups": [{"name": "G", "items": ["a", "b"]}]}))
            s = fm.load(p)
        self.assertEqual(s["groups"][0]["items"], [{"text": "a"}, {"text": "b"}])


class Refusals(unittest.TestCase):
    def test_a_map_without_a_source_is_refused(self):
        with self.assertRaisesRegex(fm.SpecError, "source"):
            spec_from(OUTLINE.replace("source: the Tinytool help\n", ""))

    def test_the_same_feature_twice_is_refused(self):
        with self.assertRaisesRegex(fm.SpecError, "twice"):
            spec_from(OUTLINE.replace("- undo", "- **save**: write it back"))

    def test_an_empty_group_is_refused(self):
        with self.assertRaisesRegex(fm.SpecError, "no items"):
            spec_from(OUTLINE + "\n## Empty\n")

    def test_a_stray_line_inside_a_group_is_an_error_not_ignored(self):
        with self.assertRaisesRegex(fm.SpecError, "line"):
            spec_from(OUTLINE + "this is not an item\n")


class Layout(unittest.TestCase):
    def check_no_overlap(self, s):
        pills = fm.layout(s)["pills"]
        for i, a in enumerate(pills):
            for b in pills[i + 1:]:
                self.assertFalse(overlaps(a, b), f"{a['item']} overlaps {b['item']}")

    def test_no_pills_overlap(self):
        self.check_no_overlap(spec_from(OUTLINE))

    def test_no_pills_overlap_on_a_crowded_map(self):
        groups = "".join(f"## Group {g}\n" + "".join(f"- **item {g}{i}**: a fairly long description that wraps onto two lines\n" for i in range(6)) for g in range(7))
        s = spec_from("# Busy\nsource: a test\n" + groups + "## Later [planned]\n- one\n- two\n- three\n- four\n- five\n")
        self.check_no_overlap(s)
        geo = fm.layout(s)
        for p in geo["pills"]:
            self.assertGreaterEqual(p["y"], fm.TOP - 60, "a pill runs into the title block")
            self.assertLessEqual(p["y"] + p["h"], geo["height"] - 40, "a pill runs off the bottom")
            self.assertGreaterEqual(p["x"], 0)
            self.assertLessEqual(p["x"] + p["w"], geo["width"])


    def test_columns_are_balanced_by_height_not_count(self):
        tall = "".join(f"- **t{i}**: item\n" for i in range(9))
        s = spec_from("# Lean\nsource: a test\n## Tall\n" + tall + "## A\n- a\n## B\n- b\n## C\n- c\n")
        sides = {g["group"]["name"]: g["side"] for g in fm.layout(s)["groups"]}
        self.assertEqual(sides["Tall"], -1)
        self.assertEqual({sides["A"], sides["B"], sides["C"]}, {1}, "the three short groups share the other side")

HELP = """Usage: tinytool <command> [arguments]

Reading
  open FILE        Open a file, read-only. Asks nothing
  peek [-n N]      Show the first lines
                   of a file, then stop

Writing
  save             Write it back
  sync push|pull   Send or fetch changes
  <group>:<cmd>    Any plugin command runs directly

Exit codes:
  0  done
"""

MAKEFILE = """help: ## Show this help
\t@echo
build: deps ## Build the thing
lint:
\t@ruff .
"""


class Sources(unittest.TestCase):
    def test_help_text_is_read_under_its_own_headings(self):
        groups = fm.read_help(HELP)
        self.assertEqual([h for h, _ in groups], ["Reading", "Writing"])
        self.assertEqual(groups[0][1][0], ("open", "Open a file, read-only. Asks nothing"))
        self.assertEqual(groups[0][1][1], ("peek", "Show the first lines of a file, then stop"))
        self.assertIn(("sync push|pull", "Send or fetch changes"), groups[1][1])

    def test_exit_codes_and_usage_are_not_commands(self):
        names = [n for _, cmds in fm.read_help(HELP) for n, _ in cmds]
        self.assertNotIn("0", names)
        self.assertFalse(any(n.lower().startswith("usage") for n in names))

    def test_only_documented_make_targets_count(self):
        self.assertEqual(fm.read_make(MAKEFILE), [("Make targets", [("help", "Show this help"), ("build", "Build the thing")])])

    def test_a_draft_is_an_outline_that_loads(self):
        text = fm.draft(fm.read_help(HELP), "Tinytool", "tinytool --help")
        s = spec_from(text)
        self.assertEqual(s["source"], "tinytool --help")
        self.assertIn("TODO", text, "a draft says it is not finished")


class Drift(unittest.TestCase):
    MAP = """# Tinytool
source: tinytool --help
omit: sync pull
## Read
- **open and peek**: look at a file
## Write
- **save**: write it back
- **sync push**: send changes
## Later [planned]
- **undo**: take it back
"""

    def test_a_map_that_covers_its_source_has_not_drifted(self):
        self.assertEqual(fm.drift(spec_from(self.MAP), fm.read_help(HELP)), ([], []))

    def test_a_new_command_in_the_source_is_reported(self):
        help2 = HELP.replace("  save ", "  export           Write a copy\n  save ")
        missing, stale = fm.drift(spec_from(self.MAP), fm.read_help(help2))
        self.assertEqual((missing, stale), (["export"], []))

    def test_a_command_the_source_dropped_is_reported_but_planned_work_is_not(self):
        help2 = HELP.replace("  save             Write it back\n", "")
        self.assertEqual(fm.drift(spec_from(self.MAP), fm.read_help(help2)), ([], ["save"]))

    def test_an_undeclared_omission_is_drift(self):
        self.assertEqual(fm.drift(spec_from(self.MAP.replace("omit: sync pull\n", "")), fm.read_help(HELP))[0], ["sync pull"])

    def test_drift_exits_1_and_is_silent_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            m, h = Path(tmp) / "m.md", Path(tmp) / "h.txt"
            m.write_text(self.MAP)
            h.write_text(HELP)
            clean = subprocess.run([sys.executable, str(TOOL), "drift", str(m), "help", str(h)], capture_output=True, text=True, check=False)
            h.write_text(HELP.replace("  save ", "  export           Write a copy\n  save "))
            loud = subprocess.run([sys.executable, str(TOOL), "drift", str(m), "help", str(h)], capture_output=True, text=True, check=False)
        self.assertEqual((clean.returncode, clean.stdout, clean.stderr), (0, "", ""))
        self.assertEqual(loud.returncode, 1)
        self.assertIn("not on the map: export", loud.stdout)


SHOP = ROOT / "examples" / "shop-stack.json"


class Stack(unittest.TestCase):
    def model(self):
        return fm.read_compose(SHOP.read_text())

    def test_ports_read_as_their_defaults_and_secrets_are_never_resolved(self):
        m = self.model()
        self.assertEqual(m["services"]["db"]["ports"], ["3306 \u2192 3306"])
        self.assertEqual(fm.plain("${DB_PASSWORD}"), "$DB_PASSWORD")
        self.assertNotIn("DB_PASSWORD", fm.stack_svg(m, "T", "", "a test", "")[0].replace("$DB_PASSWORD", ""))

    def test_columns_follow_the_request_path_and_data_goes_last(self):
        m = self.model()
        main = [n for n, s in m["services"].items() if not s["profiles"]]
        cols, sinks = fm.stack_columns(main, m["services"])
        self.assertEqual(cols[0], ["proxy"])
        self.assertEqual(sorted(sinks), ["db", "queue", "search"])
        column_of = {n: i for i, c in enumerate(cols) for n in c}
        self.assertEqual(column_of["web"], column_of["app"], "a service sharing a volume sits with its mate")

    def test_three_arrows_into_the_data_become_one_into_its_bus(self):
        svg, _, _ = fm.stack_svg(self.model(), "T", "", "a test", "")
        self.assertEqual(svg.count('stroke-width="3" stroke-linecap="round"'), 1, "one bus for the data column")

    def test_profiles_become_dashed_boxes(self):
        svg, _, _ = fm.stack_svg(self.model(), "T", "", "a test", "")
        self.assertIn("OPT-IN PROFILE: JOBS", svg)
        self.assertIn("OPT-IN PROFILE: MAIL", svg)

    def test_no_two_cards_overlap(self):
        m = self.model()
        svg, _, _ = fm.stack_svg(m, "T", "", "a test", "")
        cards = [tuple(map(float, r)) for r in re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="250" height="([\d.]+)"', svg)]
        boxes = [{"x": x, "y": y, "w": 250, "h": h} for x, y, h in cards]
        self.assertEqual(len(boxes), len(m["services"]))
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                self.assertFalse(overlaps(a, b))

    def test_an_empty_configuration_is_refused(self):
        with self.assertRaises(fm.SpecError):
            fm.read_compose('{"services": {}}')


class Drawing(unittest.TestCase):
    def test_svg_escapes_what_it_draws(self):
        s = spec_from(OUTLINE.replace("open a file", "open <b>&</b> a file"))
        out = fm.svg(s)
        self.assertIn("open &lt;b&gt;&amp;&lt;/b&gt; a file", out)
        self.assertNotIn("<b>", out)

    def test_the_source_is_printed_on_the_map(self):
        self.assertIn("DRAWN FROM THE TINYTOOL HELP", fm.svg(spec_from(OUTLINE)))

    def test_planned_work_is_dashed(self):
        out = fm.svg(spec_from(OUTLINE))
        undo = out.index(">undo<")
        self.assertIn("stroke-dasharray", out[out.rfind("<rect", 0, undo) - 400:undo])

    def test_mermaid_marks_planned_and_survives_quotes(self):
        s = spec_from(OUTLINE.replace("open a file", 'open a "quoted" [file]'))
        out = fm.mermaid(s)
        self.assertTrue(out.startswith("flowchart LR"))
        self.assertNotIn('"quoted"', out)
        self.assertRegex(out, r"class N\d+ no")
        self.assertEqual(len(re.findall(r"class N\d+ no", out)), 2)


class CommandLine(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False)

    def test_check_summarises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.md"
            p.write_text(OUTLINE)
            r = self.run_tool("check", str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("3 groups, 6 items, 2 not done yet", r.stdout)

    def test_an_invalid_outline_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.md"
            p.write_text("# No source\n## G\n- a\n")
            r = self.run_tool("check", str(p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("source", r.stderr)

    def test_a_missing_file_exits_2(self):
        self.assertEqual(self.run_tool("check", "/nonexistent/outline.md").returncode, 2)

    def test_format_follows_the_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.md"
            p.write_text(OUTLINE)
            for ext, marker in (("svg", "<svg"), ("html", "<!doctype html>"), ("mmd", "flowchart LR")):
                out = Path(tmp) / f"out.{ext}"
                r = self.run_tool("render", str(p), "-o", str(out))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(out.read_text().startswith(marker), ext)

    def test_png_without_a_browser_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.md"
            p.write_text(OUTLINE)
            r = subprocess.run([sys.executable, str(TOOL), "render", str(p), "-o", str(Path(tmp) / "o.png")],
                               capture_output=True, text=True, check=False, env={"PATH": "/nonexistent", "FEATURE_MAP_BROWSER": "no-such-browser"})
        self.assertEqual(r.returncode, 3)
        self.assertIn("browser", r.stderr)


if __name__ == "__main__":
    unittest.main()
