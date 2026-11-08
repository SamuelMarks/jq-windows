#!/usr/bin/env python3
"""Generate version.h, config.h, config_opts.inc, and builtin.inc for jq CMake builds."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path


def format_hex_byte_lines(raw_bytes: bytes, bytes_per_line: int = 16) -> str:
    """Format raw bytes as a newline-separated C hex byte initializer sequence.

    Args:
        raw_bytes: Raw input byte sequence from ``src/builtin.jq``.
        bytes_per_line: Number of byte literals per output line.

    Returns:
        Formatted C hex byte array initializer string ending with a newline.
    """
    nl = chr(10)
    chunks: list[str] = []
    for idx in range(0, len(raw_bytes), bytes_per_line):
        chunk = raw_bytes[idx : idx + bytes_per_line]
        chunks.append(", ".join(f"0x{byte:02x}" for byte in chunk) + ",")
    return nl.join(chunks) + nl


def generate_jq_build_files(builtin_jq_path: Path, out_dir: Path, version: str = "1.8.2") -> None:
    """Generate ``version.h``, ``config.h``, ``config_opts.inc``, and ``builtin.inc``.

    Args:
        builtin_jq_path: Path to upstream ``src/builtin.jq``.
        out_dir: Output directory where generated files and ``src/`` subdirectory are written.
        version: Semantic version string for ``JQ_VERSION``.

    Raises:
        FileNotFoundError: If ``builtin_jq_path`` does not exist.
    """
    if not builtin_jq_path.is_file():
        raise FileNotFoundError(f"builtin.jq not found: {builtin_jq_path}")

    dq = chr(34)
    nl = chr(10)
    src_subdir = out_dir / "src"
    src_subdir.mkdir(parents=True, exist_ok=True)

    version_text = f"#define JQ_VERSION {dq}{version}{dq}{nl}"
    for ver_target in (out_dir / "version.h", src_subdir / "version.h"):
        ver_target.write_text(version_text, encoding="utf-8")

    config_opts_text = f"#define JQ_CONFIG {dq}--with-oniguruma=builtin{dq}{nl}"
    for cfg_target in (out_dir / "config_opts.inc", src_subdir / "config_opts.inc"):
        cfg_target.write_text(config_opts_text, encoding="utf-8")

    config_h_text = nl.join(
        [
            "/* Generated config.h for jq via auto-win-msvc */",
            "#ifndef JQ_AUTO_WIN_MSVC_CONFIG_H",
            "#define JQ_AUTO_WIN_MSVC_CONFIG_H",
            f"#define JQ_VERSION {dq}{version}{dq}",
            "#undef HAVE_MEMMEM",
            "#define HAVE_STRPTIME 1",
            "#define HAVE_STRFTIME 1",
            "#define HAVE_GMTIME 1",
            "#define HAVE_GMTIME_R 1",
            "#define HAVE_LOCALTIME 1",
            "#define HAVE_LOCALTIME_R 1",
            "#define HAVE_GETTIMEOFDAY 1",
            "#define HAVE_ISATTY 1",
            "#define HAVE_SETENV 1",
            "#define HAVE_SETLOCALE 1",
            "#define HAVE_ATEXIT 1",
            "#define HAVE_PTHREAD_KEY_CREATE 1",
            "#define HAVE_PTHREAD_ONCE 1",
            "#define HAVE_LIBONIG 1",
            "#define HAVE_ONIGURUMA 1",
            "#define USE_DECNUM 1",
            "#define IEEE_8087 1",
            "#define ONIG_STATIC 1",
            "#define HAVE_ACOS 1",
            "#define HAVE_ACOSH 1",
            "#define HAVE_ASIN 1",
            "#define HAVE_ASINH 1",
            "#define HAVE_ATAN 1",
            "#define HAVE_ATAN2 1",
            "#define HAVE_ATANH 1",
            "#define HAVE_CBRT 1",
            "#define HAVE_CEIL 1",
            "#define HAVE_COPYSIGN 1",
            "#define HAVE_COS 1",
            "#define HAVE_COSH 1",
            "#define HAVE_ERF 1",
            "#define HAVE_ERFC 1",
            "#define HAVE_EXP 1",
            "#define HAVE_EXP2 1",
            "#define HAVE_EXPM1 1",
            "#define HAVE_FABS 1",
            "#define HAVE_FDIM 1",
            "#define HAVE_FLOOR 1",
            "#define HAVE_FMA 1",
            "#define HAVE_FMAX 1",
            "#define HAVE_FMIN 1",
            "#define HAVE_FMOD 1",
            "#define HAVE_FREXP 1",
            "#define HAVE_HYPOT 1",
            "#define HAVE_ILOGB 1",
            "#define HAVE_LDEXP 1",
            "#define HAVE_LGAMMA 1",
            "#define HAVE_LOG 1",
            "#define HAVE_LOG10 1",
            "#define HAVE_LOG1P 1",
            "#define HAVE_LOG2 1",
            "#define HAVE_LOGB 1",
            "#define HAVE_MODF 1",
            "#define HAVE_NEARBYINT 1",
            "#define HAVE_NEXTAFTER 1",
            "#define HAVE_NEXTTOWARD 1",
            "#define HAVE_POW 1",
            "#define HAVE_REMAINDER 1",
            "#define HAVE_RINT 1",
            "#define HAVE_ROUND 1",
            "#define HAVE_SCALBLN 1",
            "#define HAVE_SCALBN 1",
            "#define HAVE_SIN 1",
            "#define HAVE_SINH 1",
            "#define HAVE_SQRT 1",
            "#define HAVE_TAN 1",
            "#define HAVE_TANH 1",
            "#define HAVE_TGAMMA 1",
            "#define HAVE_TRUNC 1",
            "#endif",
            "",
        ]
    )
    (out_dir / "config.h").write_text(config_h_text, encoding="utf-8")

    raw_bytes = builtin_jq_path.read_bytes()
    inc_text = format_hex_byte_lines(raw_bytes)
    for inc_target in (out_dir / "builtin.inc", src_subdir / "builtin.inc"):
        inc_target.write_text(inc_text, encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for ``generate_jq_headers``.

    Args:
        argv: Optional sequence of CLI arguments.

    Returns:
        Parsed ``argparse.Namespace``.
    """
    parser = argparse.ArgumentParser(
        description="Generate version.h, config.h, config_opts.inc, and builtin.inc for jq."
    )
    parser.add_argument(
        "--builtin-jq",
        type=Path,
        required=True,
        help="Path to upstream src/builtin.jq.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for generated headers.",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.8.2",
        help="jq version string (default: 1.8.2).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``generate_jq_headers`` CLI entry point.

    Args:
        argv: Optional sequence of CLI arguments.

    Returns:
        Exit status code (``0`` on success, ``1`` on error).
    """
    args = parse_args(argv)
    try:
        generate_jq_build_files(args.builtin_jq, args.out_dir, args.version)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
