# searchselect

A searchable multi-select [anywidget](https://anywidget.dev) for notebooks. Give it a list
of strings; the user searches, filters and ticks; you read the result back in Python.

It is deliberately domain-neutral — it knows nothing but strings. Column names, category
values, file paths, feature names, whatever you have a list of.

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

| Trait      | Direction    | Meaning                                   |
| ---------- | ------------ | ----------------------------------------- |
| `items`    | read / write | The strings on offer.                     |
| `selected` | read / write | The items the user has explicitly ticked. |
| `query`    | read / write | The text in the search box.               |
| `filtered` | read         | The items matching the current query.     |

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
- **`filtered` lags `query` by one round trip.** The frontend does the matching, because
  it renders what you see and is therefore the authority on what matched. So setting
  `query` and reading `filtered` in the same cell gives you the previous value — read it
  from the next cell. With no frontend attached, nothing matches a non-empty query.

## Searching

Two toggles sit next to the search box:

- **Case-insensitive** matching.
- **Regex** matching. An invalid pattern is reported inline and matches nothing until
  it parses.

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
  roughly 22 MB at a million items. Matches only travel back while a query is active,
  since an empty query means "everything" and the frontend already has that list, so
  the common case costs nothing.
- **The row model.** Filtering runs in the browser, and the table builds one row object
  per item to do it. This is the real wall, somewhere past a few hundred thousand.

In practice: comfortable into the tens of thousands, usable past that, unpleasant around
a million. If you need to go further, open an issue — moving the search into the kernel
so items never leave Python is the known fix, and it would not change any of the API
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

Note that `pnpm dev` and `pnpm build` write to the same output directory. `pnpm dev`
produces an unminified bundle with an inline sourcemap, so always run `pnpm build`
before packaging a release.

## License

MIT
