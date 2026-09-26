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
| Any other line before the first group | The short paragraph under the subtitle |
| `source: text` | **Required.** Where the list of features came from. It is printed at the foot of the map |
| `date: text` | When the list was read. Printed beside the source |
| `center: text` | The label inside the hexagon, if it should differ from the title |
| `center-sub: a · b` | Small lines under the centre label, split on ` · ` |
| `planned-label: text` | The legend's wording for dashed items. Default `not done yet` |
| `## Group` | A branch. Groups are coloured in order from a fixed palette |
| `## Group [planned]` | A branch of work that is not done, or will not be. Drawn in red and dashed. The first one sits below the centre |
| `- **name**: what it does` | A feature with a bold name and a short description |
| `- text` | A feature with a description only |
| `- text [planned]` | One planned item inside a shipped group |

## What is refused

The map is only worth having while it is true, so `feature-map` exits 1 instead of drawing when:

- **there is no `source:` line.** A map that cannot say where its list came from cannot be checked against it;
- **the same feature appears twice**, under any groups;
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
