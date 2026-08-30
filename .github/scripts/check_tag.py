"""Fail if the git tag disagrees with the version in pyproject.toml.

A tag that says one thing while the package says another produces a release
nobody can find, and PyPI will not let the version be uploaded twice.

Deliberately avoids `tomllib`, which is 3.11+, so this runs under whatever
interpreter the workflow happens to have.
"""

from __future__ import annotations

import pathlib
import re
import sys

tag_version = sys.argv[1]
text = pathlib.Path("pyproject.toml").read_text()

# The first `version = "..."` after the [project] table.
project = text.split("[project]", 1)[-1]
match = re.search(r'^version\s*=\s*"([^"]+)"', project, re.MULTILINE)
if not match:
    print("FAIL: could not find a version in pyproject.toml")
    sys.exit(1)

packaged = match.group(1)
if tag_version != packaged:
    print(f"FAIL: tag says {tag_version!r}, pyproject.toml says {packaged!r}")
    sys.exit(1)

print(f"OK  tag and pyproject.toml agree on {packaged}")
