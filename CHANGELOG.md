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
- **A group's colour must be a hex colour.** It was written into the drawing as it stood, so a JSON outline from someone else could close the attribute and add a script to the SVG, the HTML and the page the PNG is taken from.
- **`drift` no longer hides a removed command inside a longer word**: a map's `up` used to pass because `update` exists. A name now matches a command whole, or as its first or last words, so `up` still counts while `scale up` exists.
- **A fresh draft doesn't drift from its own source.** `sync push|pull` on the map now covers both commands, as it does in the help.
- **Options, examples and lines starting with `-` are never drafted as commands.**
- **The planned row under the centre is spaced from its own pills**, so long planned items no longer overlap.
- **Settings are checked**: an unknown `word:` line before the first group is refused instead of vanishing. A bold name needs its colon, and any other `**` at the start of an item is refused instead of drawn with its asterisks. A line that starts like a setting but belongs to the paragraph gets advice to rewrap it, and a URL is never taken for one. A feature is its bold name when it has one, so the same name twice is refused however it's described.
- **Stacks:** `network_mode` is read, following a chain of `service:` modes, so host networking isn't called the default network; two projects can both have a service called `db`; every project that joins a network is named on it; two groups that would fold to one name are both drawn in full; services with no connections make a block rather than one long row; and the legend leaves out depends-on, shared volumes and health checks when the drawing has none.
- **Exit codes keep their promise.** Unreadable input exits 1 and a missing output folder exits 2, without a traceback. A stack refuses an extension it can't write. A browser named in `FEATURE_MAP_BROWSER` that doesn't exist is an error, not a quiet fallback, and an old PNG no longer passes for a new one.
- **The workflows keep no token in the checkout, and the release reads its version from the environment rather than pasting it into the script.** CI and the release both lint, and the lint now covers the tool itself: ruff skips a file with no `.py` extension unless it's named.
- **A next hop that ends a line is no longer taken for a data store.** A store is now used by a service that needs two or more ends of the line at once, so a debug web server behind the same proxy as a cache stays on the path beside it.
- **The same stack draws the same SVG every run.** The data column's arrows used to follow a set's order, which changes from one process to the next.

## 0.3.0 (2026-09-26)

- **`stack` draws a Docker Compose stack**, experimental. It reads `docker compose config --format json`, so it needs no YAML library and doesn't run anything. Boxes are networks when there is more than one, and Compose profiles otherwise. Services run left to right along the request path, with the data stores in the last column behind one shared connector, ports and volumes as small tags, and a dot for a health check. No line passes behind a card.

## 0.2.0 (2026-09-26)

- **`draft` writes an outline from a tool's own help text or Makefile**, grouped under the help's own headings, for a person to curate. It reads a file or standard input and doesn't run a command.
- **`drift` compares a map with its source**: every command the source has that the map neither shows nor declares, and every name the map shows that the source no longer has. Silent and exit 0 when nothing drifted; exit 1 with the list when something did. Planned work is exempt.
- **`omit:` declares what a map leaves out on purpose**, so leaving something out is a decision the outline states rather than a gap `drift` keeps finding.

## 0.1.0 (2026-09-26)

- **Draw a tool's features as one picture** from a Markdown outline or JSON: a title, grouped branches around a centre, and planned work dashed in red.
- **Four outputs**: SVG, HTML with web fonts, PNG through a Chromium-based browser, and a Mermaid tree.
- **Refuses a map that cannot be checked**: no `source:`, the same feature twice, an empty group, or a stray line inside a group.
- **Pills never overlap**, checked by the tests on a crowded map.
