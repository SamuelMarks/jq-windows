#!/usr/bin/env python3
"""Declarative, idempotent Git patch manager for upstream jq sources.

This module verifies and applies ordered unified diff patches from a local
``patches/`` directory against a target jq source directory using
``git apply``. If a patch has already been applied (detected via reverse
check ``git apply --reverse --check``), it is skipped cleanly so repeated
CMake configure/build invocations remain strictly idempotent.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def _clean_git_env(source_dir: Path | None = None) -> dict[str, str]:
    """Return a copy of ``os.environ`` with repository-scoping ``GIT_*`` variables removed.

    When ``apply_patches`` or its unit tests run inside a ``git commit`` hook
    (such as ``pre-commit``), Git exports ``GIT_DIR``, ``GIT_WORK_TREE``, and
    ``GIT_INDEX_FILE`` pointing to the parent repository. Stripping those
    variables and setting ``GIT_CEILING_DIRECTORIES`` ensures ``git -C <dir>``
    operates strictly on ``<dir>`` without inheriting parent ``.gitignore`` rules.

    Args:
        source_dir: Optional target source directory whose parent is set as
            ``GIT_CEILING_DIRECTORIES``.

    Returns:
        Sanitized environment dictionary safe for isolated ``git -C`` subprocesses.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    if source_dir is not None:
        env["GIT_CEILING_DIRECTORIES"] = str(source_dir.resolve().parent)
    return env


def is_patch_applied(source_dir: Path, patch_file: Path) -> bool:
    """Check whether a unified diff patch is already applied to the target tree.

    Args:
        source_dir: Path to the upstream jq source tree root.
        patch_file: Path to the ``.patch`` file to check in reverse.

    Returns:
        ``True`` if ``git apply --reverse --check`` succeeds, ``False`` otherwise.
    """
    result = subprocess.run(
        [
            "git",
            "-C",
            str(source_dir),
            "apply",
            "--reverse",
            "--check",
            "--ignore-space-change",
            "--ignore-whitespace",
            str(patch_file.resolve()),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_clean_git_env(source_dir),
    )
    return result.returncode == 0


def can_apply_patch(source_dir: Path, patch_file: Path) -> bool:
    """Check whether a unified diff patch can be cleanly applied forward.

    Args:
        source_dir: Path to the upstream jq source tree root.
        patch_file: Path to the ``.patch`` file to validate.

    Returns:
        ``True`` if ``git apply --check`` succeeds, ``False`` otherwise.
    """
    result = subprocess.run(
        [
            "git",
            "-C",
            str(source_dir),
            "apply",
            "--check",
            "--ignore-space-change",
            "--ignore-whitespace",
            str(patch_file.resolve()),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_clean_git_env(source_dir),
    )
    return result.returncode == 0


def apply_single_patch(source_dir: Path, patch_file: Path) -> bool:
    """Apply a single patch idempotently to the target jq source directory.

    Args:
        source_dir: Path to the upstream jq source tree root.
        patch_file: Path to the ``.patch`` file to apply.

    Returns:
        ``True`` if the patch was newly applied, or ``False`` if it was already
        present.

    Raises:
        RuntimeError: If the patch is neither already applied nor cleanly
            applicable.
    """
    if is_patch_applied(source_dir, patch_file):
        return False

    if not can_apply_patch(source_dir, patch_file):
        raise RuntimeError(f"Patch {patch_file.name} cannot be cleanly applied to {source_dir}")

    subprocess.run(
        [
            "git",
            "-C",
            str(source_dir),
            "apply",
            "--ignore-space-change",
            "--ignore-whitespace",
            str(patch_file.resolve()),
        ],
        check=True,
        env=_clean_git_env(source_dir),
    )
    return True


def apply_all_patches(source_dir: Path, patches_dir: Path) -> list[str]:
    """Apply all ``*.patch`` files in sorted order from ``patches_dir``.

    Args:
        source_dir: Path to the upstream jq source tree root.
        patches_dir: Directory containing ordered ``*.patch`` files (if present).

    Returns:
        List of patch filenames that were newly applied during this run.

    Raises:
        FileNotFoundError: If ``source_dir`` does not exist.
    """
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    if not patches_dir.is_dir():
        return []

    applied: list[str] = []
    patch_files = sorted(patches_dir.glob("*.patch"))
    for patch_file in patch_files:
        if apply_single_patch(source_dir, patch_file):
            applied.append(patch_file.name)
    return applied


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the patch manager CLI.

    Args:
        argv: Optional sequence of CLI arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed ``argparse.Namespace`` containing ``source_dir``,
        ``patches_dir``, and ``stamp_file``.
    """
    parser = argparse.ArgumentParser(description="Idempotently apply jq compatibility patches.")
    parser.add_argument(
        "source_dir",
        type=Path,
        help="Path to the upstream jq source tree",
    )
    parser.add_argument(
        "patches_dir",
        type=Path,
        help="Path to the directory containing .patch files",
    )
    parser.add_argument(
        "--stamp",
        dest="stamp_file",
        type=Path,
        default=None,
        help="Optional stamp file path to write upon completion",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the patch manager entry point.

    Args:
        argv: Optional sequence of CLI arguments.

    Returns:
        Exit status code (``0`` on success, ``1`` on failure).
    """
    args = parse_args(argv)
    try:
        applied = apply_all_patches(args.source_dir, args.patches_dir)
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Error applying patches: {exc}", file=sys.stderr)
        return 1

    if args.stamp_file is not None:
        nl = chr(10)
        args.stamp_file.parent.mkdir(parents=True, exist_ok=True)
        stamp_content = nl.join(applied)
        if applied:
            stamp_content += nl
        args.stamp_file.write_text(stamp_content, encoding="utf-8")

    print(f"Verified patches in {args.patches_dir} ({len(applied)} newly applied).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
