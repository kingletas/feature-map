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

    def test_bold_that_is_not_a_name_is_refused_rather_than_drawn_with_its_asterisks(self):
        for line in ("- **Always** backs up first", "- **sync:** push and pull", "- **search** : find notes"):
            with self.assertRaisesRegex(fm.SpecError, "written", msg=line):
                spec_from(OUTLINE.replace("- a plain item with no head", line))

    def test_prose_that_starts_like_a_setting_is_refused_with_advice_and_a_url_is_not(self):
        with self.assertRaisesRegex(fm.SpecError, "rewrap"):
            spec_from(OUTLINE.replace("One line about it.", "It does three things, by\npriority: sync and search."))
        s = spec_from(OUTLINE.replace("One line about it.", "https://example.com/manual covers it."))
        self.assertIn("https://example.com/manual covers it.", " ".join(s["lede"]))

    def test_json_items_of_the_wrong_type_are_refused_not_a_traceback(self):
        base = {"title": "T", "source": "s", "groups": [{"name": "G", "items": ["a"]}]}
        for bad in ({"items": [1]}, {"items": [{"head": 3, "text": "x"}]}):
            spec = json.loads(json.dumps(base))
            spec["groups"][0].update(bad)
            with self.assertRaises(fm.SpecError, msg=bad):
                fm.normalise(spec)
        with self.assertRaises(fm.SpecError):
            fm.normalise(dict(json.loads(json.dumps(base)), omit=5))

    def test_a_byte_order_mark_does_not_hide_the_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.md"
            p.write_bytes(b"\xef\xbb\xbf" + OUTLINE.encode())
            self.assertEqual(fm.load(p)["title"], "Tinytool")

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

    def test_an_unknown_setting_is_refused_rather_than_absorbed(self):
        with self.assertRaisesRegex(fm.SpecError, "not a setting"):
            spec_from(OUTLINE.replace("source: the Tinytool help", "sorce: the Tinytool help\nsource: x"))

    def test_the_same_bold_name_twice_is_refused_however_it_is_described(self):
        with self.assertRaisesRegex(fm.SpecError, "twice"):
            spec_from(OUTLINE.replace("- undo", "- **save**: keep a copy"))

    def test_a_json_group_with_no_name_is_refused(self):
        with self.assertRaisesRegex(fm.SpecError, "no name"):
            fm.normalise({"title": "T", "source": "s", "groups": [{"items": ["a"]}]})

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


    def test_long_planned_items_under_the_centre_never_touch(self):
        long = "".join(f"- **a much longer planned feature name {i}**: " + "a description that runs on " * 4 + "\n" for i in range(5))
        self.check_no_overlap(spec_from("# Later\nsource: a test\n## Now\n- one\n## Later [planned]\n" + long))

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
    def test_a_heading_that_only_contains_option_is_still_read(self):
        names = [n for _, cmds in fm.read_help("Adoption workflow:\n  adopt   Take a site in\n") for n, _ in cmds]
        self.assertEqual(names, ["adopt"])

    def test_options_and_examples_are_never_commands(self):
        text = ("Commands:\n  open FILE   Open it\n\nGlobal Options:\n  --config PATH   Where\n\n"
                "optional arguments:\n  -h, --help   Help\n\nExamples:\n  tinytool open notes.txt\n\n"
                "More:\n  -v, --verbose   Louder\n  save   Write\n")
        names = [n for _, cmds in fm.read_help(text) for n, _ in cmds]
        self.assertEqual(names, ["open", "save"])

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
    def test_a_fresh_draft_has_not_drifted_from_its_own_source(self):
        drafted = fm.draft(fm.read_help(HELP), "Tinytool", "its help")
        self.assertEqual(fm.drift(spec_from(drafted), fm.read_help(HELP)), ([], []))

    def test_a_removed_short_command_is_not_hidden_by_a_longer_one(self):
        m = spec_from("# T\nsource: s\n## G\n- **up**: start\n- **clean**: tidy\n- **scale**: resize\n")
        help_text = "Commands\n  update   Update\n  cleanup   Tidy\n  scale grow   Grow\n"
        missing, stale = fm.drift(m, fm.read_help(help_text))
        self.assertEqual(stale, ["clean", "up"])
        self.assertEqual(missing, ["cleanup", "scale grow", "update"])

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

    def test_a_variable_with_no_default_is_drawn_only_as_its_name(self):
        svg = fm.stack_svg(self.model(), "T", "", "a test", "")[0]
        self.assertNotIn("DB_PASSWORD", svg.replace("$DB_PASSWORD", ""))

    def test_environment_is_never_drawn(self):
        c = json.loads(SHOP.read_text())
        c["services"]["db"]["environment"] = {"INVENTED_SETTING": "value-never-drawn-7f3a"}
        c["services"]["db"]["image"] = "mariadb:${DB_TAG}"
        svg = fm.stack_svg(fm.read_compose(json.dumps(c)), "T", "", "a test", "")[0]
        self.assertNotIn("value-never-drawn-7f3a", svg)
        self.assertNotIn("INVENTED_SETTING", svg)
        self.assertIn("mariadb:$DB_TAG", svg)

    def test_columns_follow_the_request_path_and_data_goes_last(self):
        m = self.model()
        main = [n for n, s in m["services"].items() if not s["profiles"]]
        cols, sinks = fm.stack_columns(main, m["services"])
        self.assertEqual(cols[0], ["proxy"])
        self.assertEqual(sorted(sinks), ["db", "queue", "search"])
        column_of = {n: i for i, c in enumerate(cols) for n in c}
        self.assertEqual(column_of["web"], column_of["app"], "a service sharing a volume sits with its mate")

    def test_a_next_hop_that_ends_a_line_is_not_a_data_store(self):
        svcs = {
            "gate": {"ports": ["80"], "depends": ["cache", "debug-web"], "volumes": []},
            "cache": {"ports": [], "depends": ["web"], "volumes": []},
            "web": {"ports": [], "depends": [], "volumes": []},
            "debug-web": {"ports": [], "depends": [], "volumes": []},
            "app": {"ports": [], "depends": ["db", "search"], "volumes": []},
            "db": {"ports": [], "depends": [], "volumes": []},
            "search": {"ports": [], "depends": [], "volumes": []},
        }
        cols, sinks = fm.stack_columns(list(svcs), svcs)
        self.assertEqual(sorted(sinks), ["db", "search"])
        column_of = {n: i for i, c in enumerate(cols) for n in c}
        self.assertEqual(column_of["debug-web"], column_of["cache"], "a next hop sits beside the other next hop")

    def test_three_arrows_into_the_data_become_one_into_its_bus(self):
        svg, _, _ = fm.stack_svg(self.model(), "T", "", "a test", "")
        self.assertEqual(svg.count('stroke-width="3" stroke-linecap="round"'), 1, "one bus for the data column")
        # proxy->cache, cache->app, app->bus, worker->bus, worker->app, three
        # stubs off the bus, and the legend's own arrow. Without the bus, app
        # and worker would draw three arrows each into the data column.
        self.assertEqual(svg.count('marker-end="url(#arr)"'), 9)

    def test_the_same_stack_draws_the_same_svg_every_run(self):
        runs = {subprocess.run([sys.executable, str(TOOL), "stack", str(SHOP)], capture_output=True, text=True,
                               check=True, env={"PYTHONHASHSEED": seed}).stdout for seed in ("1", "2", "3")}
        self.assertEqual(len(runs), 1)

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


def svc(**kw):
    return dict({"image": "tinyapp:1"}, **kw)


# An invented shop that runs as two projects: a site, and a data tier it joins
# over a network whose name both files take from one variable.
SITE = {
    "name": "site",
    "networks": {"default": {"name": "site_default"},
                 "data": {"name": "${DATA_NET:?set it}", "external": True},
                 "edge": {"name": "${EDGE_NET:-edge_default}", "external": True}},
    "services": {
        "gate": svc(image="gatekeeper:2", networks={"default": {}, "edge": {}}, depends_on={"front": {"condition": "service_started"}}),
        "front": svc(networks={"default": {}}, depends_on={"engine": {"condition": "service_started"},
                                                          "unpack": {"condition": "service_completed_successfully"}}),
        "engine": svc(networks={"data": {}, "default": {}}),
        "unpack": svc(networks={"default": {}}),
        "worker-mail": svc(networks={"data": {}, "default": {}}),
        "worker-images": svc(networks={"data": {}, "default": {}}),
        "worker-feeds": svc(networks={"data": {}, "default": {}}),
    },
}
DATA = {
    "name": "data",
    "networks": {"default": {"name": "${DATA_NET:-shared-data}"}},
    "services": {"store": svc(image="tinydb:3"), "cache": svc(image="tinycache:1")},
}


class TwoProjects(unittest.TestCase):
    def draw(self, *projects):
        return fm.stack_svg([fm.read_compose(json.dumps(p)) for p in projects], "T", "", "a test", "")[0]

    def test_a_variable_with_only_an_error_message_stays_a_name(self):
        self.assertEqual(fm.plain("${DATA_NET:?set it}"), "$DATA_NET")
        self.assertEqual(fm.plain("${EDGE_NET:-edge_default}"), "edge_default")

    def test_a_service_sits_in_its_own_network_not_one_it_joins(self):
        m = fm.read_compose(json.dumps(SITE))
        self.assertEqual(fm.home_network(m["services"]["engine"], m["networks"]), "default")
        self.assertNotIn("NETWORK: DATA", self.draw(SITE))

    def test_services_alike_but_for_their_names_are_drawn_once(self):
        m = fm.read_compose(json.dumps(SITE))
        drawn = fm.collapse(m["services"])
        self.assertIn("worker-*", drawn)
        self.assertEqual(drawn["worker-*"]["members"], ["worker-mail", "worker-images", "worker-feeds"])
        self.assertIn("engine", drawn, "a service something depends on is never folded")
        self.assertIn("\u00d73", self.draw(SITE))

    def test_waiting_for_a_job_to_finish_is_start_order_not_an_arrow(self):
        m = fm.read_compose(json.dumps(SITE))
        self.assertEqual(m["services"]["front"]["after"], ["unpack"])
        self.assertNotIn("unpack", m["services"]["front"]["depends"])
        out = self.draw(SITE)
        self.assertIn("RUNS ONCE, BEFORE THE REST", out)
        self.assertIn(">after unpack<", out)

    def test_an_entry_reached_over_an_outside_network_starts_the_path(self):
        m = fm.read_compose(json.dumps(SITE))
        for s in m["services"].values():
            s["outside"] = ["edge_default"] if "edge" in s["networks"] else []
        cols, _ = fm.stack_columns(["gate", "front", "engine"], m["services"])
        self.assertEqual(cols, [["gate"], ["front"], ["engine"]])

    def test_two_projects_join_on_the_variable_that_names_their_network(self):
        out = self.draw(SITE, DATA)
        self.assertIn("Reached from site over its data network, by engine and worker-* (\u00d73).", out)
        self.assertEqual(out.count('stroke-dasharray="8 5" fill="none"'), 1, "one line for the one joined network")
        self.assertIn(">edge_default<", out, "a network nothing here declares is named on the card")
        self.assertNotIn(">$DATA_NET<", out, "a joined network is drawn as a line, not named on cards")

    def test_alone_the_joined_network_is_named_on_the_cards_instead(self):
        self.assertIn(">$DATA_NET<", self.draw(SITE))

    def test_two_projects_with_one_label_never_overwrite_a_service(self):
        with self.assertRaisesRegex(fm.SpecError, "own label"):
            self.draw(dict(SITE, services={"db": svc()}), dict(DATA, name="site", services={"db": svc()}))

    def test_a_network_shared_through_a_chain_or_a_container_outside_the_file(self):
        c = {"name": "x", "networks": {"back": {"name": "x_back"}, "front": {"name": "x_front"}},
             "services": {"a": svc(networks={"back": {}}), "b": svc(network_mode="service:a"),
                          "c": svc(network_mode="service:b"), "d": svc(network_mode="container:elsewhere"),
                          "e": svc(networks={"front": {}})}}
        m = fm.read_compose(json.dumps(c))
        self.assertEqual(m["services"]["c"]["networks"], ["back"])
        self.assertEqual((m["services"]["d"]["networks"], m["services"]["d"]["mode"]), ([], "elsewhere's network"))

    def test_one_service_name_in_two_projects_is_drawn_twice_by_project(self):
        out = self.draw(SITE, dict(DATA, services={"engine": svc(), "store": svc()}))
        self.assertIn(">site/engine<", out)
        self.assertIn(">data/engine<", out)
        self.assertIn(">store<", out)

    def test_every_project_that_joins_a_network_is_named_on_it(self):
        admin = dict(SITE, name="admin", services={"panel": svc(networks={"data": {}})})
        out = self.draw(SITE, admin, DATA)
        self.assertIn("Reached from site over its data network", out)
        self.assertIn("Reached from admin over its data network, by panel.", out)

    def test_two_groups_that_would_fold_to_one_name_are_both_drawn_in_full(self):
        one = {n: svc(image="a:1") for n in ("queue-orders", "queue-mail", "queue-feeds")}
        two = {n: svc(image="b:1") for n in ("queue-audit", "queue-search", "queue-billing")}
        drawn = fm.collapse(fm.read_compose(json.dumps({"name": "x", "services": {**one, **two}}))["services"])
        self.assertEqual(len(drawn), 6)

    def test_host_networking_is_not_called_the_default_network(self):
        c = {"name": "x", "services": {"a": svc(network_mode="host"), "b": svc(network_mode="service:a")}}
        m = fm.read_compose(json.dumps(c))
        self.assertEqual(m["services"]["b"]["networks"], m["services"]["a"]["networks"])
        out = self.draw(c)
        self.assertIn("lives on the host&#x27;s network", out)
        self.assertNotIn("(default)", out)
        self.assertEqual(out.count(">host network<"), 2, "each card says so")

    def test_host_networking_keeps_a_service_in_its_profile_box(self):
        c = {"name": "x", "services": {"web": svc(ports=["80:80"], depends_on={"db": {}}), "db": svc(),
                                       "tool": svc(network_mode="host", profiles=["tools"])}}
        out = self.draw(c)
        self.assertIn("OPT-IN PROFILE: TOOLS", out)
        self.assertNotIn("NETWORK:", out)

    def test_services_with_no_connections_make_a_block_not_a_strip(self):
        c = {"name": "x", "services": {f"s{i:02}": svc() for i in range(12)}}
        m = fm.read_compose(json.dumps(c))
        cols, _ = fm.stack_columns(list(m["services"]), m["services"])
        self.assertEqual([len(col) for col in cols], [5, 5, 2])

    def test_the_legend_names_only_what_is_drawn(self):
        out = self.draw({"name": "x", "services": {"a": svc(), "b": svc()}})
        for absent in ("depends on", "a volume shared", "health check"):
            self.assertNotIn(absent, out)

    def test_a_long_name_widens_its_card(self):
        long = {"name": "x", "services": {"a-service-with-a-very-long-descriptive-name": svc()}}
        out = self.draw(long)
        width = float(re.search(r'<rect x="[\d.]+" y="[\d.]+" width="([\d.]+)" height="[\d.]+" rx="14"', out).group(1))
        self.assertGreater(width, len("a-service-with-a-very-long-descriptive-name") * 8.6)


class Drawing(unittest.TestCase):
    def test_svg_escapes_what_it_draws(self):
        s = spec_from(OUTLINE.replace("open a file", "open <b>&</b> a file"))
        out = fm.svg(s)
        self.assertIn("open &lt;b&gt;&amp;&lt;/b&gt; a file", out)
        self.assertNotIn("<b>", out)

    def test_a_colour_that_is_not_hex_is_refused_before_it_reaches_an_attribute(self):
        base = {"title": "T", "source": "s", "groups": [{"name": "G", "items": ["one"]}]}
        attack = 'red"/><script>alert(1)</script><text x="'
        for colour in (attack, "red", "#12345"):
            spec = json.loads(json.dumps(base))
            spec["groups"][0]["color"] = colour
            with self.assertRaises(fm.SpecError, msg=colour):
                fm.normalise(spec)
        spec = json.loads(json.dumps(base))
        spec["groups"][0]["color"] = "#0d9488"
        self.assertIn('fill="#0d9488"', fm.svg(fm.normalise(spec)))

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

    def test_input_that_is_read_but_cannot_be_drawn_exits_1_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = {"list.json": b"[]", "latin.md": "# Caf\u00e9\nsource: s\n## G\n- a\n".encode("latin-1"),
                     "noname.json": json.dumps({"title": "T", "source": "s", "groups": [{"items": ["a"]}]}).encode()}
            for name, data in cases.items():
                (Path(tmp) / name).write_bytes(data)
                r = self.run_tool("check", str(Path(tmp) / name))
                self.assertEqual(r.returncode, 1, name)
                self.assertNotIn("Traceback", r.stderr, name)
            (Path(tmp) / "null.json").write_text("null")
            r = self.run_tool("stack", str(Path(tmp) / "null.json"))
            self.assertEqual((r.returncode, "Traceback" in r.stderr), (1, False))

    def test_an_output_folder_that_does_not_exist_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.md"
            p.write_text(OUTLINE)
            for args in (("render", str(p)), ("stack", str(SHOP))):
                r = self.run_tool(*args, "-o", str(Path(tmp) / "missing" / "out.svg"))
                self.assertEqual((r.returncode, "Traceback" in r.stderr), (2, False), args)

    def test_a_stack_refuses_an_extension_it_cannot_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            for ext in ("txt", "mmd"):
                r = self.run_tool("stack", str(SHOP), "-o", str(Path(tmp) / f"out.{ext}"))
                self.assertEqual(r.returncode, 2, ext)
                self.assertFalse((Path(tmp) / f"out.{ext}").exists())

    def test_a_named_browser_that_is_missing_is_an_error_not_a_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.md"
            p.write_text(OUTLINE)
            r = subprocess.run([sys.executable, str(TOOL), "render", str(p), "-o", str(Path(tmp) / "o.png")],
                               capture_output=True, text=True, check=False,
                               env={"PATH": "/usr/bin:/bin", "FEATURE_MAP_BROWSER": "no-such-browser-here"})
        self.assertEqual(r.returncode, 3)
        self.assertIn("no-such-browser-here", r.stderr)

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
