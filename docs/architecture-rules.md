# Architecture rules

The layer separation proposed in [architecture](architecture.md) is enforced by a small, repository-specific static check:

- Rules: `arch/rules.toml`
- Checker: `tools/arch/arch_check.py` (Python 3.11+, stdlib only)
- CI: `.github/workflows/arch.yml`

Run locally with `python -I -B tools/arch/arch_check.py`, and run the tests with `python -I -B -m unittest discover -s tools/arch -v`. Exit code `0` means no violation was detected, `1` means violations were found, and `2` means the rules or git state could not be read or validated. CI treats every non-zero exit as failure (fail closed).

The idea of executable architecture contracts comes from ArchitectureAnalyzer and ArchLintCpp. Their Roslyn and Clang analyzers **do not apply** to 68000 assembly and are not used here. Language-specific linters can be added if a native C/C++ or .NET host component is introduced later.

## Layers and allowed dependencies

| Layer | Paths | May depend on |
| --- | --- | --- |
| `boot` | `src/boot/` | `hw`, `services` |
| `hw` | `src/hw/` | nothing else |
| `services` | `src/services/` | `hw` |
| `harness` | `tests/` | `boot`, `hw`, `services` |

A layer may always depend on itself. Every other edge is denied by default. `boot`, `hw` and `services` are **ROM layers**: their files are ROM build inputs and they must never depend on `tests/`, `tools/` or any other unlayered path. Every tracked file under `src/` must belong to a layer.

This graph is a working design and has not been checked against verified hardware behavior. If you change it, explain the reason in a dedicated pull request. **Do not add an edge just to make a failing check pass.**

## What is checked

Files are listed with `git ls-files`.

- **Assembly** (`*.s`, `*.S`, `*.asm`, `*.inc`, `*.i`): `include`, `.include`, `incbin`, `.incbin` and `binclude` directives, case-insensitive and optionally preceded by a label. Comment lines starting with `;` or `|` are ignored.
- **Build scripts inside layers** (`Makefile`, `*.mk`, `*.ld`, `*.lds`, `*.cmake`, `CMakeLists.txt`): tokens that start with a layer root (for example `src/hw/...`) or with `../`. Directory references such as `-I src/hw` count as edges to that layer. These are resolved relative to the script's directory first, then the repository root.
- **Include resolution vs. GNU as**: assembly includes are resolved relative to the repository root first, because the GNU as manual says the current directory is searched first and the build runs from the root. They are then resolved relative to the including file's directory. GNU as instead searches the `-I` directories after the current directory. The checker does not read `-I` flags, and its file-directory fallback is not GNU as behavior. A path that only `-I` would resolve is therefore reported as unresolved (fail closed), never silently accepted.
- A reference that escapes the repository, is absolute, or does not resolve to a tracked file or directory is a violation.
- **Emulator-specific references**: every file in a ROM layer, comments included, is searched for the case-insensitive patterns in `[rom].forbidden_patterns`. These cover Genesis Plus GX / gpgx, clownmdemu, BlastEm, Kega, PicoDrive, MAME, libretro and RetroArch, including `-DGPGX`-style flags. The ROM must not contain emulator detection, hooks or workarounds. Emulator names are allowed in `tests/`.

## ROM build graph (`[rom_build]`)

The real ROM build entry points live outside the layers (the top-level `Makefile` and `tools/build/rom.ld`), so they are checked separately. Starting from `[rom_build].targets` (currently `build/oss-mcd-bios.bin`) in each tracked `[rom_build].makefiles` entry, the checker walks:

- explicit-rule prerequisites, including order-only ones, after expanding simple `$(VAR)` / `${VAR}` variables (`=`, `:=`, `?=`, `+=`);
- `%` pattern rules;
- path tokens in the recipes of the rules it reaches (`-I`, `-T` and `-L` prefixes are stripped);
- `INPUT`, `GROUP`, `INCLUDE` and `STARTUP` entries in linker scripts that it reaches.

Every tracked file or directory that is reached must be in a ROM layer or match `[rom_build].tools` (`tools/build/*`, `tools/rom/*`). Anything else is a violation, so `build/boot.o: src/boot/boot.s tests/x.s` is rejected. Reached tool files and rule text, both raw and expanded, are searched for emulator-specific names.

The following are also violations (fail closed):
- a prerequisite that is neither tracked nor a target;
- a ROM target that is not defined;
- a make function such as `$(wildcard ...)` in a reached rule;
- any makefile `include` directive.

Rules outside the ROM closure, such as `test:`, may use `tests/` and emulator names. If a listed makefile is not tracked yet, it is skipped.

## Limitations

- This is a textual check, not an assembler, `make` or linker. It does not expand assembler macros, evaluate conditional assembly, follow computed or symbol-based include paths, evaluate make conditionals (all branches are read, and the last variable assignment wins), or interpret linker semantics beyond the directives listed above. Anything it cannot see is not checked.
- Build systems other than the listed makefiles (CMake, shell scripts) are not walked as a graph. The ROM target name in `arch/rules.toml` must be kept in sync with the Makefile; if it drifts, the check fails rather than passing.
- The emulator name list is a hand-maintained list of known names. It cannot detect emulator-specific behavior that is written without naming the emulator.
- `src/` does not exist yet, so the check currently passes trivially. It becomes meaningful once source files are added.
