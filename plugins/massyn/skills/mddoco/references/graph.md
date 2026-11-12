# `graph` block schema

A ` ```graph ` fenced block holds one JSON object, rendered with matplotlib to an inline SVG at build time.
Strict JSON is preferred; Python-style literals (single quotes, `True`/`False`/`None`) are also accepted.

## Top-level fields

| Field | Required | Default | Description |
|---|---|---|---|
| `data.x` | yes | - | Category labels (list) |
| `data.<name>` | yes | - | Values for one series (list, same length as `x`); one key per series |
| `title` | no | none | Chart title |
| `orientation` | no | `vertical` | `vertical` or `horizontal` (anything else is an error) |
| `show_legend` | no | `true` | Legend in the upper left; turn off for a single series |
| `width_px` | no | `640` | Width in pixels |
| `height_px` | no | `480` | Height in pixels |
| `min` / `max` | no | auto | Value-axis bounds (y when vertical, x when horizontal); either may be given alone |
| `series` | no | auto | List of series definitions. When omitted, every `data` key except `x` becomes a `line` series |

## Series fields

When `series` is given, only the series listed are drawn, in that order.

| Field | Default | Description |
|---|---|---|
| `label` | - | Required; must match a key in `data` |
| `type` | `line` | `bar`, `line` (solid) or `line2` (dotted). Any other value draws nothing |
| `colour` | palette | Colour string; for `bar`, may be a list with one colour per bar |
| `marker` | `false` | Point markers on line types |

Default palette, in order: `#2d6cbe`, `#e74c3c`, `#27ae60`, `#e67e22`, `#8e44ad`, `#16a085`, `#2c3e50`,
`#d35400`.

## Patterns

Bar plus target line:

```json
{
  "title": "Sales vs Target",
  "data": {
    "x": ["Jan", "Feb", "Mar"],
    "Sales":  [85, 92, 78],
    "Target": [90, 90, 90]
  },
  "series": [
    { "label": "Sales",  "type": "bar",  "colour": "#3498db" },
    { "label": "Target", "type": "line2", "colour": "#e74c3c" }
  ]
}
```

Horizontal bar with a colour per bar (e.g. severity):

```json
{
  "orientation": "horizontal",
  "show_legend": false,
  "data": { "x": ["Critical", "High", "Medium", "Low"], "Count": [1, 2, 3, 2] },
  "series": [{ "label": "Count", "type": "bar",
               "colour": ["#8e0000", "#c0392b", "#e67e22", "#f1c40f"] }]
}
```

Data-driven from a `.md.j2` template (build lists in Jinja, emit with `tojson`):

```jinja
{% set order = ["Critical", "High", "Medium", "Low"] %}
{% set counts = [] %}
{% for sev in order %}{% set _ = counts.append(findings | selectattr("severity", "equalto", sev) | list | length) %}{% endfor %}
```

````markdown
```graph
{
  "data": { "x": {{ order | tojson }}, "Count": {{ counts | tojson }} },
  "series": [{ "label": "Count", "type": "bar" }],
  "show_legend": false
}
```
````

Bars sharing an axis are drawn on top of each other, not side by side - for grouped comparisons use one
bar series plus line series, or separate charts.
