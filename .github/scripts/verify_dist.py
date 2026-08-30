"""Check that the built distribution is one we would want to publish.

Every assertion here corresponds to something that has actually gone wrong in
this project or the template it came from. They are cheap; the failures they
catch are not, because a bad wheel on PyPI cannot be replaced, only superseded.
"""

from __future__ import annotations

import glob
import sys
import zipfile

EXPECTED = {
    "searchselect/__init__.py",
    "searchselect/static/main.js",
    "searchselect/static/main.css",
}

# A production bundle is a few hundred KB; the dev one is several MB and carries
# an inline sourcemap.
MAX_JS_BYTES = 1_500_000


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def main() -> None:
    wheels = glob.glob("dist/*.whl")
    sdists = glob.glob("dist/*.tar.gz")

    if len(wheels) != 1:
        fail(f"expected exactly one wheel, found {wheels}")
    if len(sdists) != 1:
        fail(f"expected exactly one sdist, found {sdists}")

    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        names = {n for n in archive.namelist() if ".dist-info/" not in n}

        # The sdist flattens `py/searchselect/` to `searchselect/`, and the wheel
        # is built from the unpacked sdist. Get the paths wrong and the wheel
        # installs cleanly while containing nothing at all.
        missing = EXPECTED - names
        if missing:
            fail(f"wheel is missing {sorted(missing)}; it contains {sorted(names)}")

        js = archive.read("searchselect/static/main.js")

        # `pnpm dev` and `pnpm build` share an output directory. A stale dev
        # bundle reaching a release is invisible until someone loads the widget.
        if b"sourceMappingURL" in js:
            fail("main.js carries a sourcemap -- this is a dev bundle, not a build")
        if len(js) > MAX_JS_BYTES:
            fail(f"main.js is {len(js):,} bytes, over the {MAX_JS_BYTES:,} limit")

        # The bundled webfont inlined seven base64 subsets, most of the stylesheet.
        css = archive.read("searchselect/static/main.css")
        if b"base64" in css:
            fail("main.css contains base64 data -- a font or image is inlined")

    print(f"OK  {wheel}")
    print(f"    {len(names)} package files, main.js {len(js):,} bytes, main.css {len(css):,} bytes")
    print(f"OK  {sdists[0]}")


if __name__ == "__main__":
    main()
