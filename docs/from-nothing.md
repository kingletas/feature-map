# From nothing to a working feature-map

By the end of this, somebody who has never seen feature-map will have drawn a map of their own tool.

## Contents

- [What this is](#what-this-is)
- [Step 1: install it](#step-1-install-it)
- [Step 2: write an outline](#step-2-write-an-outline)
- [Step 3: draw it](#step-3-draw-it)
- [What you get for free](#what-you-get-for-free)
- [Where to go next](#where-to-go-next)

## What this is

**A command that draws a tool's features as one picture**, grouped by the job each one does, with the work that is not done yet drawn dashed.

It exists because a tool that keeps growing outgrows its README. The README says what every flag does; the map says what the tool is for, at a glance.

## Step 1: install it

```bash
git clone https://github.com/kingletas/feature-map && cd feature-map && make install
```

That puts `feature-map` in `~/bin`. Set `PREFIX` to install somewhere else: `make install PREFIX=/usr/local/bin`.

## Step 2: write an outline

The one setting that matters most is **`source:`**, the place your list of features came from. Without it the map is refused:

```text
feature-map: my-tool.md: the outline has no 'source:' line; a map says where its list came from
```

Copy `examples/notebook.md` to `my-tool.md` and change it; unchanged, it is the invented notes app the output below describes. Each `##` is a branch, each `-` is a feature, and `[planned]` marks what is not done yet.

## Step 3: draw it

```bash
feature-map check my-tool.md
```

```text
Quillnote: 5 groups, 14 items, 3 not done yet; drawn from the Quillnote README
```

Then draw it:

```bash
feature-map render my-tool.md -o my-tool.png
```

A PNG needs a Chromium-based browser. Without one, draw an SVG instead: `-o my-tool.svg`.

## What you get for free

- **A layout that never overlaps**: groups to either side of the centre, and planned work below it.
- **A map that says where it came from**, printed at the foot, so a reader can check it.
- **The same map as a Mermaid tree**, for a Markdown page: `-o my-tool.mmd`.

## Where to go next

- [The outline format, and what is refused](format.md)
- [README](../README.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
