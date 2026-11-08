jq Windows (MSVC) & DOS (OpenWatcom) Native Builds
==================================================

[![License](https://img.shields.io/badge/license-CC0%20OR%20Apache--2.0%20OR%20MIT-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/SamuelMarks/jq-windows/actions/workflows/ci.yml/badge.svg)](https://github.com/SamuelMarks/jq-windows/actions/workflows/ci.yml)
![Doc Coverage](https://img.shields.io/badge/doc%20coverage-100%25-brightgreen)
![Test Coverage](https://img.shields.io/badge/test%20coverage-100%25-brightgreen)

This repository provides **native Windows builds** (compiled with Microsoft Visual C++ / MSVC) and **32-bit Protected-Mode DOS builds** (compiled with OpenWatcom v2) of [jq](https://jqlang.org/) (`1.8.2`)—"the lightweight and flexible command-line JSON processor"—using CMake and [auto-win-msvc](https://github.com/SamuelMarks/auto-win-msvc).

While upstream `jq` distributes Windows binaries cross-compiled via MinGW-w64 (GCC) and does not provide DOS releases, `jq-windows` enables:
- **True Native MSVC Compilation (`jq.exe`):** Compiles cleanly under `cl.exe` (Static `/MT` or Shared `/MD` CRT) without MinGW/MSYS2/Cygwin runtime dependencies.
- **32-bit Protected-Mode DOS Compilation (`JQ.EXE`):** Compiles under OpenWatcom v2 (`wcl386`, `-bt=dos`, `DOS/4GW` / `CauseWay` flat 32-bit memory model) with single-threaded TLS and POSIX shims.

---

## Architecture: `auto-win-msvc` + C99-to-C89 AST Transformation

All POSIX system calls, time/date parsing (`strptime`, `gmtime_r`, `localtime_r`, `gettimeofday`), filesystem paths (`dirname`, `stat`, `isatty`), command-line option parsing (`getopt`, `getopt_long`), and thread-local storage (`pthread_key_create`, `pthread_once`) are backed directly by **[auto-win-msvc](https://github.com/SamuelMarks/auto-win-msvc)**.

- **Zero `.c`/`.h` Files in `jq-windows`:** No `.h` or `.c` files are stored in `jq-windows`. All POSIX/BSD/Linux polyfills and C99-to-C89 source transformations (`auto_win_msvc_transform_sources()`) live in `auto-win-msvc`, and build-time headers (`version.h`, `config.h`, `config_opts.inc`, `builtin.inc`) are generated deterministically by `scripts/generate_jq_headers.py`.
- **100% Tested & Strongly Typed:** 100% Python line, branch, function, and docstring coverage (`pytest --cov --cov-branch --cov-fail-under=100`, `mypy --strict`, `interrogate --fail-under=100`) alongside functional CTest verification suites covering JSON construction, array/math filters, ISO-8601 date parsing (`fromdateiso8601`), and Oniguruma regular expressions.

---

## Releases

Pre-compiled packages are available on the [Releases](../../releases) tab:
- **Standalone Windows Executable (`jq-*-X64.exe`):** Single-file native MSVC Windows binary.
- **NSIS Setup Installer (`jq-*-X64-setup.exe`):** Windows installer with option to add `jq` to the system `PATH`.
- **WiX MSI Installer (`jq-*-X64.msi`):** Windows Installer package for enterprise deployments.
- **Portable Windows ZIP Archive (`jq-*-X64.zip`):** Standalone archive for Windows.
- **32-bit DOS Executable & CPack ZIP (`jq-*-dos32.exe` / `jq-*-dos32.zip`):** OpenWatcom v2 32-bit DOS executable and portable archive bundling `DOS32A.EXE` and `DOS4GW.EXE`.
- **MS-DOS 1.25, 2.0, and 4.0 Ready-to-Run Archives (`jq-*-msdos-1.25.zip`, `jq-*-msdos-2.0.zip`, `jq-*-msdos-4.0.zip`):** Version-targeted DOS archives bundling `JQ.EXE` with the appropriate `DOS32A.EXE` runtime for MS-DOS 1.25, 2.0, and 4.0.

---

## Building Locally

### Native Windows (MSVC)

1. Clone `auto-win-msvc` and `jq-windows` side-by-side:
   ```cmd
   git clone https://github.com/SamuelMarks/auto-win-msvc.git
   git clone https://github.com/SamuelMarks/jq-windows.git
   ```

2. Configure, compile, and test in an MSVC Developer Command Prompt (or run `release.bat`):
   ```cmd
   cd jq-windows
   cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
   cmake --build build --config Release
   ctest --test-dir build -C Release --output-on-failure
   ```

### 32-bit Protected-Mode DOS (OpenWatcom v2)

Run `release_dos.bat` (or configure with `-G "Watcom WMake" -DCMAKE_SYSTEM_NAME=DOS`) with OpenWatcom v2 installed at `C:\usr\WATCOM`:
```cmd
release_dos.bat
```

### MS-DOS 1.25, 2.0, and 4.0 Vagrant Test Suite (`vagrant/dos/Vagrantfile`)

To cross-compile `jq` with OpenWatcom v2 (`wcl386`) and execute the CTest functional test suite inside Microsoft MS-DOS `1.25`, `2.0`, and `4.0` virtual machines (`bento/msdos-1.25`, `bento/msdos-2.0`, `bento/msdos-4.0`):

```sh
cd vagrant/dos
vagrant up msdos-1.25 --provider=qemu
vagrant up msdos-2.0 --provider=qemu
vagrant up msdos-4.0 --provider=qemu
```

---

## Quality & Coverage Gates

All Python build, codegen, and shield-maintenance modules enforce 100% docstring, type, line, branch, and function coverage via `pre-commit`:

```bash
pre-commit run --all-files
```

---

## License

This build system and integration packaging are tri-licensed under:
- [CC0 1.0 Universal](LICENSE-CC0)
- [Apache License 2.0](LICENSE-APACHE)
- [MIT License](LICENSE-MIT)

`jq` itself is licensed under the MIT License, and Oniguruma is licensed under the BSD 2-Clause License.
