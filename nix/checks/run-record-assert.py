"""Assert one field of a --record JSON file against an expected value.

`python3 run-record-assert.py <path> <field> <expected>`. `expected` is
compared as text against the field's JSON value — `null`, `true` and
`false` spell themselves, so a check can assert `executed` is null
without a separate code path for it.
"""

from __future__ import annotations

import json
import sys


def _as_text(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def main() -> int:
    path, field, expected = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if field not in data:
        print(f"FAIL: {field!r} is missing from {path}: {data!r}")
        return 1
    actual = _as_text(data[field])
    if actual != expected:
        print(f"FAIL: {field} in {path} is {actual!r}, expected {expected!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
