# searchselect

[![PyPI](https://img.shields.io/pypi/v/searchselect.svg)](https://pypi.org/project/searchselect/)
[![Python versions](https://img.shields.io/pypi/pyversions/searchselect.svg)](https://pypi.org/project/searchselect/)
[![License](https://img.shields.io/pypi/l/searchselect.svg)](https://github.com/pedRamezani/searchselect/blob/main/LICENSE)
[![CI](https://github.com/pedRamezani/searchselect/actions/workflows/ci.yml/badge.svg)](https://github.com/pedRamezani/searchselect/actions/workflows/ci.yml)

A searchable multi-select [anywidget](https://anywidget.dev) for notebooks. Give it a list
of strings; the user searches, filters and ticks; you read the result back in Python.

It is deliberately domain-neutral — it knows nothing but strings. Column names, category
values, file paths, feature names, whatever you have a list of.

![SearchSelect](https://raw.githubusercontent.com/pedRamezani/searchselect/main/assets/searchselect-light.png)

```sh
pip install searchselect
```

## Quickstart

```python
from searchselect import SearchSelect

picker = SearchSelect(items=df.columns)
picker
```

Then, in a later cell:

```python
df.select(picker.selected)
```

Works in JupyterLab, Jupyter Notebook, marimo Notebook, VS Code and anywhere else anywidget renders.

## API

`SearchSelect(items=None, selected=None)`

| Trait            | Direction    | Meaning                                           |
| ---------------- | ------------ | ------------------------------------------------- |
| `items`          | read / write | The strings on offer.                             |
| `selected`       | read / write | The items the user has explicitly ticked.         |
| `query`          | read / write | The text in the search box.                       |
| `regex`          | read / write | Treat `query` as a regex rather than a substring. |
| `case_sensitive` | read / write | Whether matching distinguishes case.              |
| `filtered`       | read         | The items matching the current query.             |
| `query_error`    | read         | Python's `re.error` text, or `""` if valid.       |
| `theme`          | read / write | `"auto"` (default), `"light"` or `"dark"`.        |

The distinction that matters: **`selected` is an explicit choice, `filtered` is a query
result.** They are independent, and both are useful.

```python
# Tick things by hand, then read them back.
picker.selected            # -> ['age', 'height']

# Or don't tick anything: type a pattern and take everything it matched.
picker.filtered            # -> ['lab_glucose', 'lab_sodium', ...]

# The query is writable too, so you can drive it from Python.
picker.query = "lab_"
```

The header checkbox selects **everything matching the current query**, not just
what's on screen — so `query` plus select-all is the click-free route to the same
set `filtered` reports.

### Rules

- **Filtering never unselects.** Ticking an item and then typing a search that excludes it
  leaves it in `selected`. The search box changes what you can _see_, not what you have
  _chosen_.
- **An empty search box means every item.** `filtered` is the full list when nothing is
  typed, not an empty list.
- **Duplicates are dropped.** First occurrence wins; order is otherwise preserved.
- **Selection is keyed on the item itself, not its position.** Reassigning `items` keeps
  ticks on items that still exist and drops the rest.
- **`selected` is writable.** Set it from Python to preselect or clear; the checkboxes
  follow. Values not present in `items` are ignored.
- **An unparseable query matches nothing.** Which is not the same as an empty query,
  which matches everything. `query_error` carries the reason.

## Searching

Two toggles sit next to the search box:

- **Case-insensitive** matching.
- **Regex** matching. An invalid pattern is reported inline, with Python's own error
  message, and matches nothing until it parses.

**Matching runs in Python, using `re`.** That means the pattern you type is a Python
regex — `(?P<name>...)` works, `\d` and `\w` are Unicode as they are everywhere else in
your code, and you can paste the pattern straight into the next cell and get identical
results:

```python
picker.regex = True
picker.query = r"^lab_(?P<assay>\w+)"

# the same pattern, same semantics, in your own code
[c for c in df.columns if re.match(picker.query, c)]
```

The trade-off is that searching needs a responsive kernel. If a long cell is running,
the search box will not update until it finishes. Filtering in the browser would stay
live, but it would mean a JavaScript regex — a different dialect that quietly rejects
`(?P<name>...)` and treats `\d` as ASCII-only — and a pattern you can't reuse.

## The list

The list is virtualised, so only the visible rows exist in the DOM however long it is.

- **The header retracts** as you scroll down and returns the moment you scroll back up,
  so a long list gets the whole box without putting the sort control out of reach.
- **Sorting cycles** A–Z, Z–A, then back to the original order — which is the order you
  passed `items` in, since that order is preserved.
- **The header checkbox selects every match**, not just what is on screen.

## Theme

By default the widget infers light or dark from the host notebook. That is
inference, not a lookup — there is no standard way for a host to announce its
theme — so pin it when the guess is wrong, when a notebook will be read by
someone whose OS setting you don't know, or simply out of preference:

```python
picker.theme = "light"   # or "dark", or "auto"
```

![SearchSelect in dark mode](https://raw.githubusercontent.com/pedRamezani/searchselect/main/assets/searchselect-dark.png)

**In VS Code, prefer `"light"`.** VS Code paints the widget output area white
whatever the editor theme is, and that area is outside the widget, so a dark
widget ends up sitting on a white surround. The widget can only paint up to its
own edge; `"light"` removes the mismatch.

## Copying out

Below the table is a panel rendering the current selection as a **Python list** or a
**Polars expression**, with a copy button — for when you would rather paste a literal
into your next cell than reference the widget. This is a convenience; `picker.selected`
is the real API, and the package has no dataframe dependency of any kind.

## Performance

The list is virtualised: only the rows on screen exist in the DOM, about 25 of them,
whether you pass two hundred items or a million. Scrolling and rendering are therefore
flat in the size of the list.

Two things are not flat, and they set the practical ceiling:

- **Transport.** Items are sent to the frontend once, as JSON over the Jupyter comm —
  roughly 22 MB at a million items. Matches travel back only while a query is active;
  an empty query means "everything", and the frontend already has that list, so the
  resting state costs nothing.
- **Matching.** Each query is a scan in Python: about 2 ms at ten thousand items, 60 ms
  at a hundred thousand, and up to 600 ms at a million for an expensive pattern. Input
  is debounced, so a keystroke does not become a request, but this is what you feel
  first on very large lists.

In practice: comfortable into the tens of thousands, usable past that, sluggish around a
million. If you need to go further, open an issue — pushing the search into DuckDB and
serving the visible window with `LIMIT`/`OFFSET` would break both ceilings at once,
though it would change the pattern dialect to RE2 and cost you the Python-regex property
above.

## Development

Development requires [`uv`](https://github.com/astral-sh/uv) and
[`pnpm`](https://pnpm.io/).

```sh
uv venv
uv pip install -e . --group dev
pnpm dev # start a development server
uv run jupyter lab notebooks/example.ipynb
```

`pnpm dev` and `pnpm build` write to the same directory, and the dev bundle is
unminified with an inline sourcemap — roughly six times the size. `pnpm build` empties
that directory first and the packaging hook runs it for the sdist, so `uv build` always
produces a real production bundle regardless of what a dev server left behind.

Releasing:

```sh
uv build
uvx twine upload dist/*
```

## License

MIT
