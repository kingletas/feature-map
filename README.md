# feature-map

**Draw what a tool does as one picture, from a plain outline.**

A tool that keeps growing gets hard to hold in your head. Its README lists every flag, and nobody reads a README to learn what it's for. A feature map is the other view: every capability grouped by the job it does, around the tool's name, with the work that is not done yet drawn in dashes beside the rest.

![A feature map for an invented notes app, with four coloured branches and a dashed branch of planned work](docs/example.png)

**It refuses to draw a map that cannot be checked.** Every outline says where its list came from, and that source is printed on the map. A map with no source, or one that names the same feature twice, isn't drawn: you get an error instead.

## Try it

You'll need Python 3 and nothing else. Drawing a PNG also needs a Chromium-based browser.

```bash
make example
```

That draws the bundled example into `local.d/`. To draw your own:

```bash
bin/feature-map render my-tool.md -o my-tool.png
```

## Write an outline

```markdown
# Quillnote
> A notebook that files itself
One line about what it is for.

source: the Quillnote README
date: 1 March 2026

## Write
- **capture**: a new note from anywhere
- **daily**: one note per day, made for you

## Not done yet [planned]
- Sync between devices
```

Each `##` is a branch and each `-` is a feature. `**name**:` gives a feature a bold name. `[planned]` draws a branch or an item dashed, in red. **The full format, and what is refused, is in [docs/format.md](docs/format.md).**

## Keep it true

A map drawn by hand falls behind its tool. `draft` writes a first outline from the tool's own help text, and `drift` tells you when the two disagree, silently when they don't. **Neither runs anything for you**: pipe the help in.

```bash
mytool --help | feature-map drift mytool.md help -
```

Details are in [docs/format.md](docs/format.md#drafting-from-a-tool-and-checking-a-map-against-it).

## Outputs

| Format | For | Needs |
| --- | --- | --- |
| `svg` | A standalone image, or embedding in a page | nothing |
| `html` | The SVG with its web fonts, for viewing in a browser | nothing |
| `png` | Posting, slides, a README | a Chromium-based browser on `PATH`, or its path in `FEATURE_MAP_BROWSER` |
| `mermaid` | The same map as a tree, for Markdown that renders Mermaid | nothing |

The format follows the output file's extension (`.svg`, `.html`, `.png`, `.mmd`), or `--format` says it. Without `-o`, `svg` and `mermaid` go to standard output.

```bash
bin/feature-map check my-tool.md
```

prints what the outline holds, and exits 1 if it would be refused.

## Commands

| Command | Does |
| --- | --- |
| `make help` | The list |
| `make check` | Compile, lint if `ruff` is installed, and run the tests |
| `make example` | Draw the bundled example into `local.d/` |
| `make map SPEC=… OUT=…` | Draw one outline |
| `make install` | Put `feature-map` in `PREFIX`, default `~/bin` |
| `feature-map draft help -` | Draft an outline from a tool's help text on standard input |
| `feature-map drift MAP help -` | Say what the tool has that the map doesn't show, and the reverse |

**Exit codes:** 0 done, 1 the outline is refused, 2 bad usage, 3 the PNG could not be drawn.

## What it does not do

- **It doesn't read your code.** It reads what the tool says about itself: its help text or its Makefile. The map is as true as the outline, which is why it prints its source and why `drift` exists.
- **The layout is automatic and fixed in style**: groups to the left and right of the centre, the first planned group below it. There's no theme option yet.
- **Text widths are estimated**, so a pill can come out a little wide. Pills never overlap, and the tests check that on a crowded map.

## Licence

MIT. See [LICENSE](LICENSE).
