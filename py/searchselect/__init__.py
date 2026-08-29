"""A searchable multi-select widget for picking strings from a list."""

from __future__ import annotations

import pathlib
import re
from typing import Callable

import anywidget
import traitlets

__all__ = ["SearchSelect"]

bundler_assets_dir = pathlib.Path(__file__).parent / "static"


def _dedupe(values: list[str]) -> list[str]:
    """Drop duplicates, preserving first-occurrence order."""
    return list(dict.fromkeys(values))


class SearchSelect(anywidget.AnyWidget):
    """A searchable, multi-select list picker.

    Give it a list of strings; the user searches, filters and ticks. Read the
    result back from :attr:`selected` (an explicit choice) or :attr:`filtered`
    (whatever the current query matches).

    >>> picker = SearchSelect(items=df.columns)
    >>> picker
    >>> df.select(picker.selected)

    Matching runs here, in Python, using :mod:`re`. That means the pattern typed
    into the search box is a Python regex: it can be pasted straight into your
    own code and it will behave identically. The trade-off is that searching
    needs a responsive kernel -- the search box will not update while a long
    cell is running.
    """

    _esm = bundler_assets_dir / "main.js"
    _css = bundler_assets_dir / "main.css"

    #: The strings on offer. Duplicates are dropped, first occurrence wins,
    #: order is otherwise preserved. Reassigning this keeps ticks on items that
    #: still exist and drops the rest.
    items = traitlets.List(traitlets.Unicode()).tag(sync=True)

    #: The items the user has explicitly ticked. Writable from Python; values
    #: not present in :attr:`items` are ignored. Filtering never changes it.
    selected = traitlets.List(traitlets.Unicode()).tag(sync=True)

    #: The text in the search box. Writable from Python, and applied
    #: immediately -- :attr:`filtered` is correct in the same cell.
    query = traitlets.Unicode("").tag(sync=True)

    #: Whether :attr:`query` is a regular expression rather than a substring.
    regex = traitlets.Bool(False).tag(sync=True)

    #: Whether matching distinguishes case.
    case_sensitive = traitlets.Bool(True).tag(sync=True)

    #: The items matching the current query. With an empty query this is every
    #: item, not an empty list. An unparseable query matches nothing.
    #:
    #: Deliberately *not* synced. The frontend is told the matches through
    #: `_matches`, which stays empty while the query is, so the resting state
    #: costs no list traffic -- echoing the full list back to say "everything"
    #: would be 22MB each way at a million items.
    filtered = traitlets.List(traitlets.Unicode())

    #: The error from compiling :attr:`query` as a regex, or "" if it is valid.
    #: Python's own `re.error` text, which is considerably more useful than a
    #: bare "invalid".
    query_error = traitlets.Unicode("").tag(sync=True)

    #: Python -> frontend. The matches to display, empty while the query is.
    #: Internal; read :attr:`filtered`.
    _matches = traitlets.List(traitlets.Unicode()).tag(sync=True)

    def __init__(
        self,
        items: list[str] | None = None,
        selected: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        # `items` must be assigned first: the `selected` validator filters
        # against it, and the matches are derived from it.
        super().__init__(
            items=_dedupe(list(items or [])),
            selected=list(selected or []),
            **kwargs,
        )
        self._rematch()

    @traitlets.validate("items", "selected", "_matches")
    def _dedupe_trait(self, proposal: dict) -> list[str]:
        return _dedupe(proposal["value"])

    @traitlets.validate("selected")
    def _restrict_selected(self, proposal: dict) -> list[str]:
        """Only ever select items that are actually on offer.

        `items` is assigned before `selected` in ``__init__``, and the observer
        below re-validates after any later change to it, so this always sees the
        current item list.
        """
        known = set(self.items)
        return [item for item in _dedupe(proposal["value"]) if item in known]

    @traitlets.observe("items")
    def _drop_unknown_items(self, change: dict) -> None:
        """Keep `selected` to items that still exist.

        The frontend does this too, but it must also hold with no frontend
        attached -- before the widget has rendered, or in a headless kernel --
        or `selected` would keep reporting items the widget no longer offers.
        """
        known = set(change["new"])
        selected = [item for item in self.selected if item in known]
        if selected != self.selected:
            self.selected = selected

    @traitlets.observe("items", "query", "regex", "case_sensitive")
    def _rematch(self, change: dict | None = None) -> None:
        """Recompute the matches for the current query."""
        if not self.query:
            # Everything matches, and the frontend already has the item list,
            # so it is told nothing rather than told everything.
            self.query_error = ""
            self._matches = []
            self.filtered = list(self.items)
            return

        try:
            predicate = self._predicate()
        except re.error as error:
            # An unparseable pattern matches nothing, which is distinct from an
            # empty query matching everything.
            self.query_error = str(error)
            self._matches = []
            self.filtered = []
            return

        self.query_error = ""
        matches = [item for item in self.items if predicate(item)]
        self._matches = matches
        self.filtered = matches

    def _predicate(self) -> Callable[[str], bool]:
        """Build the match test. Raises `re.error` for an invalid pattern."""
        if self.regex:
            pattern = re.compile(self.query, 0 if self.case_sensitive else re.IGNORECASE)
            return lambda item: pattern.search(item) is not None

        if self.case_sensitive:
            query = self.query
            return lambda item: query in item

        query = self.query.casefold()
        return lambda item: query in item.casefold()
