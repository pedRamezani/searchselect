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

    #: The items the user has explicitly ticked. Writable from Python.
    #: Filtering the table does not change it.
    selected = traitlets.List(traitlets.Unicode()).tag(sync=True)

    #: The items matching the current search. With an empty search box this is
    #: every item, not an empty list.
    filtered = traitlets.List(traitlets.Unicode()).tag(sync=True)

    def __init__(
        self,
        items: list[str] | None = None,
        selected: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        _items = _dedupe(list(items or []))
        # `items` must be assigned first: the `selected` validator filters
        # against it. `filtered` starts as everything, matching the
        # empty-search-box rule, so it reads correctly before the frontend
        # has mounted.
        super().__init__(
            items=_items,
            selected=list(selected or []),
            filtered=list(_items),
            **kwargs,
        )

    @traitlets.validate("items", "selected", "filtered")
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
        """Keep `selected` and `filtered` to items that still exist.

        The frontend does this too, but it must also hold with no frontend
        attached — before the widget has rendered, or in a headless kernel —
        or `selected` would keep reporting items the widget no longer offers.
        """
        known = set(change["new"])

        selected = [item for item in self.selected if item in known]
        if selected != self.selected:
            self.selected = selected

        # Removed items cannot match any query, so intersecting is correct
        # whether or not one is active.
        filtered = [item for item in self.filtered if item in known]
        if filtered != self.filtered:
            self.filtered = filtered
