"""Exercise the installed package, on the oldest Python we claim to support.

This is not a substitute for a test suite. It checks the things that would make
a release useless: that the module imports at all, that the bundled assets made
it into the wheel, and that the documented semantics hold.
"""

from __future__ import annotations

import sys

import searchselect
from searchselect import SearchSelect

print(f"python {sys.version.split()[0]}, searchselect from {searchselect.__file__}")

assets = searchselect.bundler_assets_dir
for name in ("main.js", "main.css"):
    path = assets / name
    assert path.exists(), f"{path} missing from the installed package"
    assert path.stat().st_size > 0, f"{path} is empty"

picker = SearchSelect(items=["apple", "Banana", "avocado", "apple"], selected=["apple"])

# Duplicates dropped, first occurrence wins, order otherwise preserved.
assert picker.items == ["apple", "Banana", "avocado"], picker.items

# An empty query means every item, not an empty list.
assert picker.filtered == picker.items, picker.filtered

# Matching runs here, so `filtered` is correct in the same breath as `query`.
picker.query = "av"
assert picker.filtered == ["avocado"], picker.filtered

# Filtering is not unselecting.
assert picker.selected == ["apple"], picker.selected

# The pattern is a Python regex, including syntax a JS engine would reject.
picker.regex = True
picker.query = r"(?P<fruit>^a)"
assert picker.query_error == "", picker.query_error
assert picker.filtered == ["apple", "avocado"], picker.filtered

# An unparseable pattern matches nothing and says why.
picker.query = "a("
assert picker.query_error, "an invalid pattern should report an error"
assert picker.filtered == []

# Reassigning items keeps ticks on items that still exist and drops the rest.
picker.query = ""
picker.regex = False
picker.selected = ["apple", "Banana"]
picker.items = ["Banana", "cherry"]
assert picker.selected == ["Banana"], picker.selected

print("OK  all smoke checks passed")
