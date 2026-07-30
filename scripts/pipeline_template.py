#!/usr/bin/env python3
"""
Pipeline template — dependency-resolved step orchestrator.

This template provides a reusable pipeline skeleton with built-in
defensive I/O utilities for encoding detection, column matching,
directory creation, and NULL-safe value handling — all using
Python 3.10+ standard library only.

Usage:
    python3 scripts/pipeline.py --report          # run full report (includes clean)
    python3 scripts/pipeline.py --clean           # run clean step only (deprecated)
"""

import argparse
import codecs
import json
import math
import os
import re
import sys

# ── Defensive I/O utilities ────────────────────────────────────────────


def _detect_encoding(path: str) -> str:
    """Detect file encoding by trying common codecs in order.

    Tries utf-8 first, then common fallbacks. Returns the first encoding
    that can decode the first 1024 bytes without error.

    Args:
        path: Path to the file to inspect.

    Returns:
        An encoding name string (e.g. "utf-8", "gbk", "latin-1").

    Example:
        >>> enc = _detect_encoding("data/report.csv")
        >>> with codecs.open("data/report.csv", "r", encoding=enc) as f:
        ...     rows = list(csv.DictReader(f))
    """
    for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1", "cp1252"]:
        try:
            with codecs.open(path, "r", encoding=enc) as f:
                f.read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _normalize_column(name: str) -> str:
    """Normalize a column name for fuzzy matching.

    Lowercases, strips whitespace, and replaces any non-word character
    with an underscore.

    Args:
        name: Raw column name.

    Returns:
        Normalized, underscore-separated string.

    Example:
        >>> _normalize_column("  Sales Qty (Units) ")
        'sales_qty_units_'
    """
    name = name.strip().lower()
    name = re.sub(r"[^\w]", "_", name)
    return name


def _match_columns(expected: list[str], actual: list[str]) -> dict[str, str]:
    """Map expected column names to actual column names via normalized matching.

    Each expected name is matched against the actual column headers using
    ``_normalize_column``. If no match is found, the expected name is used
    as-is with a warning printed to stderr.

    Args:
        expected: List of column names the code expects.
        actual:   List of column names present in the data.

    Returns:
        Dict mapping each expected name to its matched actual name.

    Example:
        >>> _match_columns(["Sale ID", "Amount"], ["sale_id", "amount_usd"])
        {'Sale ID': 'sale_id', 'Amount': 'amount_usd'}
    """
    mapping: dict[str, str] = {}
    actual_norm = {_normalize_column(a): a for a in actual}
    for exp in expected:
        norm = _normalize_column(exp)
        mapping[exp] = actual_norm.get(norm, exp)
        if norm not in actual_norm:
            print(
                f"Warning: column '{exp}' not found in {actual}, using raw '{exp}'",
                file=sys.stderr,
            )
    return mapping


def _ensure_dir(path: str) -> None:
    """Create parent directories for *path* if they do not exist.

    Works for both file paths and directory paths. No-op if directories
    already exist.

    Args:
        path: Filesystem path whose parent (or self) should exist.

    Example:
        >>> _ensure_dir("output/2025/report.json")
        >>> with open("output/2025/report.json", "w") as f:
        ...     f.write(data)
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _safe(value, default=None, coerce=None):
    """Return *value* if it is not None, NaN, or empty; otherwise return *default*.

    Optionally coerces the value to a target type via the *coerce* callable.
    If coercion fails, *default* is returned.

    Args:
        value:   The value to inspect.
        default: Fallback value (default ``None``).
        coerce:  Optional callable to transform the value (e.g. ``int``, ``float``).

    Returns:
        The cleaned value, coerced value, or default.

    Example:
        >>> _safe(None, default=0.0)
        0.0
        >>> _safe("42", coerce=int)
        42
        >>> _safe("", default="N/A")
        'N/A'
        >>> _safe(float("nan"), default=0.0)
        0.0
    """
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    if coerce is not None:
        try:
            return coerce(value)
        except (ValueError, TypeError):
            return default
    return value


# ── Dependency graph & orchestration ───────────────────────────────────

STEPS = {
    "clean": [],
    "report": ["clean"],
}


def resolve_steps(target: str) -> list[str]:
    """Return ordered step list for target, including all dependencies."""
    visited = set()
    order = []

    def dfs(step: str) -> None:
        if step in visited:
            return
        visited.add(step)
        for dep in STEPS.get(step, []):
            dfs(dep)
        order.append(step)

    dfs(target)
    return order


def run_step(name: str) -> None:
    """Execute a single pipeline step."""
    print(f"[pipeline] Running step: {name}", file=sys.stderr)
    # TODO: replace with actual step logic; use defensive I/O helpers above.
    #   data_path = _detect_encoding("input.csv")
    #   _ensure_dir("output/report.json")
    print(json.dumps({"step": name, "status": "ok"}))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dependency-resolved pipeline orchestrator"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Run full report (resolves all prerequisite steps including clean)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="[deprecated] Run clean step only. Use --report instead.",
    )
    args = parser.parse_args()

    if args.report:
        steps = resolve_steps("report")
        for step in steps:
            run_step(step)
    elif args.clean:
        run_step("clean")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
