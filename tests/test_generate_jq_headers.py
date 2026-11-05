"""Unit tests for ``scripts.generate_jq_headers``."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from scripts.generate_jq_headers import (
    format_hex_byte_lines,
    generate_jq_build_files,
    main,
    parse_args,
)


def test_format_hex_byte_lines() -> None:
    """Verify byte array formatting across single and multiple lines."""
    res = format_hex_byte_lines(b"ABC", bytes_per_line=2)
    assert "0x41, 0x42," in res
    assert "0x43," in res


def test_generate_jq_build_files_and_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify header generation, CLI argument parsing, error paths, and ``__main__`` execution.

    Args:
        tmp_path: Pytest temporary directory fixture.
        capsys: Pytest stdout/stderr capture fixture.
    """
    nl = chr(10)
    builtin_jq = tmp_path / "builtin.jq"
    builtin_jq.write_text(f"def halt: halt;{nl}", encoding="utf-8")
    out_dir = tmp_path / "gen"

    parsed = parse_args(
        ["--builtin-jq", str(builtin_jq), "--out-dir", str(out_dir), "--version", "1.8.2"]
    )
    assert parsed.version == "1.8.2"

    rc_ok = main(["--builtin-jq", str(builtin_jq), "--out-dir", str(out_dir)])
    assert rc_ok == 0
    assert (out_dir / "version.h").is_file()
    assert (out_dir / "src" / "version.h").is_file()
    assert (out_dir / "config.h").is_file()
    assert (out_dir / "config_opts.inc").is_file()
    assert (out_dir / "src" / "config_opts.inc").is_file()
    assert (out_dir / "builtin.inc").is_file()
    assert (out_dir / "src" / "builtin.inc").is_file()

    missing_path = tmp_path / "missing.jq"
    with pytest.raises(FileNotFoundError, match="builtin.jq not found"):
        generate_jq_build_files(missing_path, out_dir)

    rc_err = main(["--builtin-jq", str(missing_path), "--out-dir", str(out_dir)])
    assert rc_err == 1
    assert "builtin.jq not found" in capsys.readouterr().err

    old_argv = sys.argv
    sys.argv = [
        "generate_jq_headers.py",
        "--builtin-jq",
        str(missing_path),
        "--out-dir",
        str(out_dir),
    ]
    try:
        script_path = Path(__file__).resolve().parent.parent / "scripts" / "generate_jq_headers.py"
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path(str(script_path), run_name="__main__")
        assert exc_info.value.code == 1
    finally:
        sys.argv = old_argv
    capsys.readouterr()
