# Changelog

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
