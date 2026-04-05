import pathlib

import anywidget
import traitlets

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from polars import pl

__all__ = ["Widget"]


def list_to_select_expr(value: list[str]) -> "pl.Expr":
    import polars as pl

    return pl.col(value)


bundler_assets_dir = pathlib.Path(__file__).parent / "static"


class Widget(anywidget.AnyWidget):
    _esm = bundler_assets_dir / "main.js"
    _css = bundler_assets_dir / "main.css"

    # Write and Read
    terms = traitlets.List(traitlets.Unicode()).tag(sync=True)

    # Read only
    filtered = traitlets.List(traitlets.Unicode()).tag(sync=True)
    selected = traitlets.List(traitlets.Unicode()).tag(sync=True)

    def __init__(self, terms: list[str] | None = None):
        _terms = terms or []
        super().__init__(terms=_terms)

    @property
    def filtered_as_pl_expr(self) -> "pl.Expr":
        return list_to_select_expr(self.filtered)

    @property
    def selected_as_pl_expr(self) -> "pl.Expr":
        return list_to_select_expr(self.selected)
