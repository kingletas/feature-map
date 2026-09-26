# The outline format

A map is drawn from a Markdown outline: a title, a few settings, then one `##` heading per group and one `-` item per feature. The whole of [`examples/notebook.md`](../examples/notebook.md) is a working example.

```markdown
# Quillnote
> A notebook that files itself
Quillnote keeps plain-text notes and tells you when two notes disagree.

source: the Quillnote README
date: 1 March 2026

## Write
- **capture**: a new note from anywhere
- **templates**: start from a saved shape

## Not done yet [planned]
- Sync between devices
```

## The parts

| Line | Means |
| --- | --- |
| `# Title` | The map's title, and the label in the middle unless `center:` says otherwise |
| `> text` | The subtitle under the title |
| Any other line before the first group | The short paragraph under the subtitle. A line that looks like a setting (`word: text`) but isn't one of the settings below is refused, so a typo like `sorce:` can't vanish into the paragraph |
| `source: text` | **Required.** Where the list of features came from. It is printed at the foot of the map |
| `date: text` | When the list was read. Printed beside the source |
| `center: text` | The label inside the hexagon, if it should differ from the title |
| `center-sub: a · b` | Small lines under the centre label, split on ` · ` |
| `omit: a, b` | Commands the map leaves out on purpose, so `drift` does not report them |
| `planned-label: text` | The legend's wording for dashed items. Default `not done yet` |
| `## Group` | A branch. Groups are coloured in order from a fixed palette |
| `## Group [planned]` | A branch of work that is not done, or will not be. Drawn in red and dashed. The first one sits below the centre |
| `- **name**: what it does` | A feature with a bold name and a short description. Any other use of `**` at the start of an item is refused, since the asterisks would be drawn as they are |
| `- text` | A feature with a description only |
| `- text [planned]` | One planned item inside a shipped group |

## What is refused

The map's only worth having while it's true, so `feature-map` exits 1 instead of drawing when:

- **there is no `source:` line.** A map that cannot say where its list came from cannot be checked against it;
- **the same feature appears twice**, under any groups. A feature with a bold name is that name, so `**save**` twice is refused even when the two descriptions differ;
- **a group has no items**;
- **a line inside a group is neither an item nor a heading.** A stray line is more likely a mistake than something to leave out quietly.

## JSON

The same map can be written as JSON, for a tool that generates it:

```json
{
  "title": "Quillnote",
  "source": "the Quillnote README",
  "groups": [
    {"name": "Write", "items": [{"head": "capture", "text": "a new note from anywhere"}]},
    {"name": "Not done yet", "planned": true, "items": ["Sync between devices"]}
  ]
}
```

A group can carry its own `"color"`, which must be a hex colour such as `#2563eb`. Anything else is refused, since the colour is written into the drawing as it stands.

## Drafting from a tool, and checking a map against it

A map drawn by hand drifts: the tool gains a command and nobody redraws. Two commands keep the outline honest against the tool's own description, and neither one runs anything on your behalf. They skip the usage, options, examples, exit-code and environment sections of a help text, and a line starting with `-` is never taken for a command.

```bash
mytool --help | feature-map draft help - --title Mytool --source-name "mytool --help"
```

writes an outline with one group per heading in the help text and one item per command. **It's a draft**: regroup it, shorten the descriptions, and move anything unfinished under a `[planned]` group. A Makefile whose targets carry `## description` comments works the same way with `draft make Makefile`.

```bash
mytool --help | feature-map drift mytool.md help -
```

prints nothing and exits 0 when the map and the help agree. Otherwise it lists each command the map neither shows nor names in `omit:`, and each bold name on the map the help no longer has, and exits 1. **A bold name covers every command it lists**: `**up, down and restart**` covers all three. Plain items without a bold name are descriptions, not commands, and aren't checked. A bold name matches a command whole, or as its first or last words, so `**scale**` still counts while `scale up` exists, but a removed `up` isn't hidden by `update`. Run it in CI and a map can no longer fall behind its tool quietly.
