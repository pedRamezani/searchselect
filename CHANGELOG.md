# Changelog

## [0.1.0] - 2026-08-30

First release. Previously developed, unreleased, as `searchwidget`.

### Added

- `SearchSelect`: a searchable multi-select picker for any list of strings. It is
  deliberately domain-neutral — column names, category values, file paths, anything you
  have a list of.
- **`selected` and `filtered` as separate answers.** `selected` is an explicit choice —
  the items ticked — and survives the current query, so filtering never unselects.
  `filtered` is a query result, and with an empty search box it is every item rather
  than none. Both are useful, and a caller picks which question they are asking.
- **Matching runs in Python, using `re`.** The pattern typed into the search box is
  therefore a Python regex: `(?P<name>...)` works, `\d` and `\w` are Unicode as they are
  everywhere else in your code, and the pattern can be pasted straight into the next
  cell and behave identically. `query_error` carries Python's own message when a pattern
  will not parse.
- **A live control, not a form.** `items`, `selected` and `query` are all writable from
  Python and apply immediately. Selection is keyed on the item itself rather than its
  row position, so reassigning `items` keeps ticks on items that still exist and drops
  the rest. These rules hold with no frontend attached, so they are true in a headless
  kernel too.
- **A virtualised list.** Only the visible rows exist in the DOM, so scrolling is flat in
  the size of the list. The header retracts on the way down and returns on the way up,
  and its checkbox selects every match rather than only what is on screen. Sorting
  cycles A–Z, Z–A, then back to the order `items` was given in.
- **A theme that follows the host**, inferred from the notebook and overridable with
  `theme` (`"auto"`, `"light"`, `"dark"`). Prefer `"light"` in VS Code, which paints the
  widget output area white whatever the editor theme is.
- A copy pane rendering the current selection as a Python list or a Polars expression,
  for when pasting a literal beats referencing the widget.

### Notes

- The only runtime dependency is `anywidget`. There is no dataframe dependency of any
  kind; the widget hands back a plain `list[str]`.
- Requires Python 3.9 or newer, verified in CI against 3.9 and 3.13.
- Matching in the kernel means searching needs a responsive kernel: the search box will
  not update while a long cell is running. Filtering in the browser would stay live, but
  the pattern would then be a JavaScript regex and not reusable in your own code.
