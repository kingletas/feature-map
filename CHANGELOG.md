# Changelog

## Unreleased

- **`stack` draws several Compose projects as one picture.** Pass each as `LABEL=FILE`. A network one project declares and another joins as external is drawn as one dashed line into the declaring project's box, with the services that use it named there. The two are matched on the variable that names the network, or on its default, so `${DATA_NET:?}` in one file meets `${DATA_NET:-shared}` in the other.
- **A service sits in the network its own project owns.** It used to sit in whichever of its networks sorted first, which could be an external one it only joins.
- **Waiting for a job to finish is start order, not a path.** A `depends_on` with `service_completed_successfully` becomes an "after" line on the card, and the jobs waited on get their own "runs once, before the rest" box, instead of every service drawing an arrow to them.
- **Three or more services alike but for their names are drawn once**, as `prefix-*` with a count, when nothing depends on them and none publishes a port. Hovering the card lists them.
- **An entry can be reached over a network, not only a port**, so a cache behind a shared reverse proxy starts the request path.
- **Each column follows the order of what points into it**, so parallel pairs run level instead of crossing.
- **Cards widen to fit their longest line**, and a network the drawing does not show is named on the cards that join it.
- **The legend lists only what the drawing uses.**
- `${VAR:?message}` reads as `$VAR`; it used to be printed whole.

## 0.3.0 (2026-09-26)

- **`stack` draws a Docker Compose stack**, experimental. It reads `docker compose config --format json`, so it needs no YAML library and runs nothing. Boxes are networks when there is more than one, and Compose profiles otherwise. Services run left to right along the request path, with the data stores in the last column behind one shared connector, ports and volumes as small tags, and a dot for a health check. No line passes behind a card.

## 0.2.0 (2026-09-26)

- **`draft` writes an outline from a tool's own help text or Makefile**, grouped under the help's own headings, for a person to curate. It reads a file or standard input and never runs a command.
- **`drift` compares a map with its source**: every command the source has that the map neither shows nor declares, and every name the map shows that the source no longer has. Silent and exit 0 when nothing drifted; exit 1 with the list when something did. Planned work is exempt.
- **`omit:` declares what a map leaves out on purpose**, so leaving something out is a decision the outline states rather than a gap `drift` keeps finding.

## 0.1.0 (2026-09-26)

- **Draw a tool's features as one picture** from a Markdown outline or JSON: a title, grouped branches around a centre, and planned work dashed in red.
- **Four outputs**: SVG, HTML with web fonts, PNG through a Chromium-based browser, and a Mermaid tree.
- **Refuses a map that cannot be checked**: no `source:`, the same feature twice, an empty group, or a stray line inside a group.
- **Pills never overlap**, checked by the tests on a crowded map.
