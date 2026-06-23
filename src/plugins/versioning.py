"""Tiny, dependency-free version parsing and comparison.

Just enough to support plugin dependency specifiers like ``"foo>=1.2"`` without
pulling in ``packaging``.  Versions are dotted numeric strings; trailing
non-numeric segments (e.g. ``"1.2.0rc1"``) fall back to ``0`` so comparisons
stay total instead of raising.
"""

from __future__ import annotations

import re

_SPEC_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+?)\s*(==|>=|<=|>|<|~=)?\s*([0-9][0-9A-Za-z.\-]*)?\s*$")


def parse_version(value: str) -> tuple[int, ...]:
    """Parse a dotted version string into a comparable tuple of ints."""
    parts: list[int] = []
    for segment in str(value).split("."):
        match = re.match(r"\d+", segment)
        parts.append(int(match.group()) if match else 0)
    return tuple(parts) or (0,)


def _pad(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    length = max(len(a), len(b))
    return a + (0,) * (length - len(a)), b + (0,) * (length - len(b))


def satisfies(version: str, operator: str, target: str) -> bool:
    """Return whether ``version <operator> target`` holds."""
    left, right = _pad(parse_version(version), parse_version(target))
    if operator == "==":
        return left == right
    if operator == ">=":
        return left >= right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == "<":
        return left < right
    if operator == "~=":
        # Compatible release: same leading components, not below target.
        prefix = right[:-1]
        return left[: len(prefix)] == prefix and left >= right
    raise ValueError(f"Unsupported version operator: {operator!r}")


def parse_requirement(spec: str) -> tuple[str, str | None, str | None]:
    """Split ``"foo>=1.2"`` into ``("foo", ">=", "1.2")``.

    A bare ``"foo"`` yields ``("foo", None, None)`` (presence-only requirement).
    """
    match = _SPEC_RE.match(spec)
    if not match:
        raise ValueError(f"Invalid plugin requirement: {spec!r}")
    name, operator, target = match.groups()
    if operator and not target:
        raise ValueError(f"Requirement {spec!r} has an operator but no version")
    return name, operator, target
