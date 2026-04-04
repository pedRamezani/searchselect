import pathlib

import anywidget
import traitlets

bundler_assets_dir = pathlib.Path(__file__).parent / "static"


class Widget(anywidget.AnyWidget):
    _esm = bundler_assets_dir / "main.js"
    _css = bundler_assets_dir / "main.css"
    terms = traitlets.List([]).tag(sync=True)
