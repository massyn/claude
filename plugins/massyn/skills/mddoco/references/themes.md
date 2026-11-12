# Custom themes

`--theme` takes a built-in name or a path to an HTML file. A theme is a Jinja2 template (autoescape on)
that receives:

| Variable | Type | Meaning |
|---|---|---|
| `title` | str or None | `--title` value |
| `toc_html` | str or None | Merged `<ul>` table of contents, present only with `--toc` |
| `sections` | list of `(path, body)` | One entry per input file, in order; `body` is rendered HTML |
| `has_mermaid` | bool | Any Mermaid diagram present - load Mermaid.js only then |
| `has_code` | bool | Any code block present - load highlight.js only then |

Output HTML must use `| safe` for `toc_html` and each `body`. Minimal skeleton:

```jinja
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ title or "Document" }}</title>
  <style>/* your CSS */</style>
  {% if has_mermaid %}
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({ startOnLoad: true });</script>
  {% endif %}
</head>
<body>
  {% if title %}<h1>{{ title }}</h1>{% endif %}
  {% if toc_html %}<nav>{{ toc_html | safe }}</nav>{% endif %}
  <main>
    {% for path, body in sections %}
      {% if not loop.first %}<hr>{% endif %}
      <section>{{ body | safe }}</section>
    {% endfor %}
  </main>
</body>
</html>
```

The template is loaded from its own folder, so it may `{% extends %}` or `{% include %}` files beside it.
To restyle a built-in theme, copy it from the installed package (`mddoco/themes/` in site-packages) - and
copy the theme it extends too: the `-wide` themes extend their base theme and the `site-*` themes extend
`_site_base.html`.

A screen-only theme opts out of PDF by setting, at the top level of the template:

```jinja
{% set pdf_supported = false %}
```

`--format pdf` then fails with an error instead of producing a PDF.

Rendered fragments use these hooks for styling: Mermaid diagrams are `<div class="mermaid">`, charts are
`<div class="graph"><svg ...></div>`, and code blocks are `<pre><code class="language-xxx">`.
