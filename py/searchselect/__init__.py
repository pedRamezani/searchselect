"""A searchable multi-select widget for picking strings from a list."""

from __future__ import annotations

import pathlib

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

    #: The text in the search box. Writable from Python.
    #:
    #: Matching happens in the frontend -- it renders what the user sees, so it
    #: is the authority on what matched. That means `filtered` catches up one
    #: comm round trip after this is set, not synchronously. With no frontend
    #: attached (headless, or before the widget renders) nothing matches a
    #: non-empty query, because nothing is there to do the matching.
    query = traitlets.Unicode("").tag(sync=True)

    #: The items matching the current query. With an empty query this is every
    #: item, not an empty list.
    #:
    #: Deliberately *not* synced: it is derived locally from `_matches`, so an
    #: empty query costs no traffic at all. The frontend already has the full
    #: item list, so echoing it back would double the payload for nothing --
    #: 22MB each way at a million items.
    filtered = traitlets.List(traitlets.Unicode())

    #: Frontend -> Python. Only populated while a query is active; cleared to
    #: an empty list as soon as the query is. Internal; read `filtered`.
    _matches = traitlets.List(traitlets.Unicode()).tag(sync=True)

    def __init__(
        self,
        items: list[str] | None = None,
        selected: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        # `items` must be assigned first: the `selected` validator filters
        # against it, and `filtered` is derived from it.
        super().__init__(
            items=_dedupe(list(items or [])),
            selected=list(selected or []),
            **kwargs,
        )

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

    @traitlets.observe("items", "query", "_matches")
    def _recompute_filtered(self, change: dict) -> None:
        """Derive `filtered` from the query and the frontend's matches.

        An empty query matches everything, so `filtered` is the whole item list
        and no match data needs to cross the wire.
        """
        if not self.query:
            filtered = list(self.items)
        else:
            # Removed items cannot match any query, so intersecting keeps this
            # correct when `items` changes while a query is active.
            known = set(self.items)
            filtered = [item for item in self._matches if item in known]

        if filtered != self.filtered:
            self.filtered = filtered
