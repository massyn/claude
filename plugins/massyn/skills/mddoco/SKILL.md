---
name: mddoco
description: Write documents for mddoco, the CLI that turns a folder of Markdown files into one HTML or PDF document - file layout and ordering, the Markdown dialect it supports, Jinja2 .md.j2 templates fed by JSON and CSV data files, native graph charts, Mermaid and D2 diagrams, themes (including the site-* website themes), table of contents and the render command. Use whenever creating, editing or rendering an mddoco document, report, handbook or site, writing .md.j2 templates or graph blocks for one, or when the user mentions mddoco - even if they just say "build the report" or "render the docs" in a folder of numbered Markdown files.
---

# Writing mddoco documents

mddoco (`pip install mddoco`, source at github.com/massyn/mddoco) combines every Markdown file in a folder
into a single self-contained HTML file, or a PDF. A document is a **folder**, not a file: write content as
several small, numbered files in one input directory, then render the folder.

## 1. Lay out the folder

```
report/
  01_introduction.md
  02_findings.md.j2      <- Jinja2 template that produces Markdown
  03_appendix.md
  _macros.j2             <- leading underscore: not rendered, safe to {% import %}
  findings.csv           <- available to templates as {{ findings }}
  project.json           <- available to templates as {{ project }}
```

- **Order** is a plain sort of the full paths, `.md` and `.md.j2` together. Always use zero-padded numeric
  prefixes (`01_`, `02_` ... `10_`) - without padding `10_` sorts before `2_`.
- **Subfolders** are scanned recursively and sort by path, so `02_part/01_x.md` lands between `01_` and
  `03_` at the top level. Number folders the same way.
- **Excluded:** any file whose name starts with `_` (drafts, notes, macro files). This applies to file
  names only - a folder named `_drafts/` is still scanned, so prefix the files inside it too. Only `*.md` and `*.md.j2`
  are rendered; other files are ignored except data files (section 3).
- **One topic per file.** Each file becomes its own `<section>` and themes draw a divider between files,
  so split where a reader would expect a break. Start each file with a heading.
- **Headings:** `--title` already prints the document title above everything, so don't repeat it as an
  H1 in the first file. Use H1 for major sections (the `site-*` themes make each H1 a page) and H2/H3
  beneath them; keep heading levels unbroken so the TOC nests properly.

## 2. Markdown dialect - what works and what doesn't

mddoco uses Python-Markdown with only these extensions: `tables`, `fenced_code`, `attr_list` (plus `toc`
when `--toc` is on). Write to that dialect, not to GitHub Flavoured Markdown:

| Works | Does not work (renders literally or wrongly) |
|---|---|
| Pipe tables with a header row | Task lists `- [ ]` |
| Fenced code blocks with a language (highlighted by highlight.js) | `~~strikethrough~~` |
| `{#id .class}` attributes after headings, links, images | Footnotes `[^1]`, admonitions `!!!`, definition lists |
| Inline and block raw HTML | Auto-linked bare URLs - write `<https://...>` or `[text](url)` |
| ` ```mermaid `, ` ```d2 ` and ` ```graph ` fenced blocks | GitHub alerts `> [!NOTE]` |

Python-Markdown is stricter than GitHub about whitespace:

- Leave a **blank line** before every list, table, code fence and block quote.
- Indent nested list items and content inside list items by **4 spaces**, not 2.
- A blank line inside a table ends it - this matters most in templates (section 3).
- Images and links are relative to where the HTML file is opened, not to the Markdown file. Prefer
  absolute URLs, or keep images next to the output; the output is a single file and does not copy them.

Need a callout or page break? Use raw HTML, e.g. `<div style="page-break-before: always"></div>` for PDF.

## 3. Jinja2 templates (`.md.j2`) and data files

A `.md.j2` file is rendered with Jinja2 first, then converted like any `.md`. Use it whenever content comes
from data - never paste tables of figures by hand when a CSV or JSON can drive them.

**Data files** are loaded from the **top level of the input folder only** (not subfolders). Each file's stem
is a variable:

- `project.json` -> `project`, holding whatever the JSON contains.
- `team.csv` -> `team`, a list of row dicts keyed by the header, all values strings. A cell containing `;`
  becomes a **list** (`python;flask` -> `["python", "flask"]`) unless the cell is quoted. Guard for both:
  `{% if v is string %}{{ v }}{% else %}{{ v | join(", ") }}{% endif %}`.
- A `.json` and `.csv` with the same stem is an error - rename one.
- Rendering a single file (`mddoco report/02_x.md.j2`) still loads data from that file's folder.

**Template rules:**

- Autoescape is **off** - values go into the Markdown verbatim. A `|` in a value breaks a table row; use
  `{{ v | replace("|", "\\|") }}` where data might contain one.
- Control whitespace inside tables so no blank lines appear between rows: open loops with `-%}` and keep
  each row on one line:

  ```jinja
  | Name | Role |
  |------|------|
  {% for m in team -%}
  | {{ m.name }} | {{ m.role }} |
  {% endfor %}
  ```

- Aggregate in the template with standard filters (`selectattr`, `groupby`, `sum(attribute=...)`,
  `length`, `sort(attribute=...)`). Numbers from CSV are strings: use `| int` or `| float` before maths or
  numeric sorting.
- Shared macros go in an underscore file next to the template and are pulled in with `{% import "_macros.j2"
  as m %}` or `{% from "_macros.j2" import field %}`. **Never `{% include %}`** a macro file - included
  macros are not callable. Imports resolve relative to the template's own folder.
- To feed data into a `graph` block, emit JSON with `tojson`: `"x": {{ labels | tojson }}`.
- Only standard Jinja2 filters and tests exist - don't invent any. Render and check (section 6).

## 4. Charts and diagrams

**Charts:** a ` ```graph ` fenced block holding JSON is rendered at build time to a static SVG (no
JavaScript, so it works in PDF too). Only `data` is required; `x` is the category labels and every other
key is a series:

````markdown
```graph
{
  "title": "Findings by severity",
  "show_legend": false,
  "data": {
    "x": ["Critical", "High", "Medium", "Low"],
    "Count": [1, 2, 3, 2]
  },
  "series": [{ "label": "Count", "type": "bar", "colour": "#c0392b" }]
}
```
````

Every series list must be the same length as `x`, and each `series[].label` must match a `data` key. A bad
graph fails the whole render. Full schema (types `bar`/`line`/`line2`, orientation, sizing, axis bounds,
per-bar colours) is in [references/graph.md](references/graph.md).

**Diagrams:** a ` ```mermaid ` fenced block is drawn by Mermaid.js in the browser (loaded from a CDN only
when a diagram is present). Standard Mermaid syntax; flowcharts, sequence, Gantt and so on all work.

A ` ```d2 ` fenced block is compiled at build time by the separate `d2` command-line tool and embedded as
inline SVG, so it needs no JavaScript and prints cleanly to PDF. `d2` is not installed by `pip`; it is only
required when a document contains a `d2` block, and a missing tool or a block that fails to compile fails
the render. Install options, behaviour and when to prefer it over Mermaid are in
[references/d2.md](references/d2.md):

````markdown
```d2
direction: right
client -> server: request
server -> db: query
```
````

Choose a `graph` for numbers, `d2` or `mermaid` for structure and flow (`d2` when layout quality or PDF
output matters and the `d2` CLI is available, `mermaid` when no extra tool should be needed), a table when
exact values matter.

## 5. Render

```bash
mddoco <folder> [--title "Title"] [--toc] [--toc-depth 2] [--theme NAME] [--format html|pdf] [--output PATH]
```

- `--output` is a directory (default `.`; the file is named after the input folder, e.g. `report.html`)
  or an explicit file path when it has a suffix (`-o out/q3-review.pdf`).
- `--toc` builds a table of contents from headings; `--toc-depth` (1-6, default 3) limits it.
- `--format pdf` needs Playwright's Chromium (downloaded automatically on first use, ~150 MB, or run
  `playwright install chromium`). HTML needs nothing extra.

**Themes** (`--theme`, default `default`):

| Purpose | Theme |
|---|---|
| General docs | `default`, `default-wide` |
| Business report | `professional`, `professional-wide` |
| Technical docs, dark | `dark`, `dark-wide` |
| Formal / long-form, print | `academic`, `academic-wide` |
| Print-ready paginated PDF | `paged-professional` |
| Small website in one file (HTML only) | `site`, `site-professional`, `site-dark`, `site-terminal` |
| Bare HTML for custom CSS | `vanilla` |

`-wide` variants use the full viewport width. The `site-*` themes make each H1 a page in a side nav (its H2s
listed under it), ignore `--toc` and refuse `--format pdf`. `--theme` also accepts a path to a custom theme
file - the template contract is in [references/themes.md](references/themes.md).

When the user hasn't said, pick: `professional --toc` for reports, `site` for handbooks and multi-page
reference, `paged-professional --format pdf` when they need a printable PDF.

## 6. Verify

Always render before saying a document is done, writing output to a scratch directory rather than the
repo:

```bash
mddoco <folder> --title "..." --toc --output <scratch-dir>
```

- A non-zero exit means a Jinja error, bad JSON in a data file or graph, a stem clash, or a theme/format
  mismatch, a `d2` block with the `d2` CLI missing or failing to compile - the message says which. Fix and
  re-run.
- Then grep the HTML for signs of a dialect slip: literal `|---` or `| ` at line starts (a broken table),
  `{{` or `{%` (template text that leaked), `[ ]` or `~~` (unsupported GFM).
- Keep generated HTML/PDF out of version control unless the user wants it committed.
