# Build toolchain

Decision record: [ADR 0001](adr/0001-toolchain.md). Tracking issue: #2.

> A successful build proves only that original source assembles, links and passes
> structural checks. It does **not** prove the ROM boots on any emulator or hardware.

## Build

```sh
make          # first run: fetch + SHA-256-verify + build pinned binutils (~a few minutes, -j2)
              # then: assemble, link, pad, print ROM SHA-256, run structural validator
make test     # validator unit tests (Python stdlib only); same as:
              #   python3 -I -B -m unittest discover -s tools/rom -p "test_*.py" -v
make clean    # remove build products (keeps build/toolchain)
```

Host requirements: Linux (or WSL) with `bash`, `make`, a C compiler, `curl`, `xz`, `tar`,
`sha256sum`, `python3` (3.8+). No texinfo, bison or flex needed. Peak memory stays low because
the toolchain builds with `-j2` (override with `JOBS=N`). Use a prebuilt pinned toolchain
elsewhere with `make TC=/path/to/prefix`.

Outputs (all under `build/`, which is git-ignored):

| File | Content |
| --- | --- |
| `build/oss-mcd-bios.bin` | padded ROM image |
| `build/oss-mcd-bios.bin.sha256` | `sha256sum`-format hash, also printed by `make` |

## Pinned toolchain

The single source of truth is [`tools/build/toolchain.lock`](../tools/build/toolchain.lock), plain
`key=value` lines shared with the other tool pins (`name`, `version`, `sha256`, `url`, `command`,
`version_cmd`; plus `target`, used by the build). `toolchain.sh` and the `Makefile` read it; the
doctor tool can read it too. `command` is expected on `PATH` only if you add
`build/toolchain/bin` to `PATH`; the Makefile itself calls the tools by full path.

| Item | Value (from the lock file) |
| --- | --- |
| Package | GNU binutils (gas, ld, objcopy only), target `m68k-elf` |
| Version | 2.42 |
| Source | `https://ftp.gnu.org/gnu/binutils/binutils-2.42.tar.xz` |
| SHA-256 | `f6e4d41fd5fc778b06b7891457b3620da5ecea1006c6a4a41ae998109f85a800` |
| License | GPL-3.0-or-later (tool only; see below) |

The hash was computed from downloads from both `ftp.gnu.org` and `mirrors.kernel.org`
(identical). `tools/build/toolchain.sh` refuses to build if the tarball hash differs.
Upgrading = change `version`, `url` and `sha256` in the lock file (the CI cache key follows it).

## Pipeline

1. `src/boot/boot.s` -> `m68k-elf-as -m68000` -> `build/boot.o`
2. `tools/build/rom.ld` -> `m68k-elf-ld` -> `build/rom.elf`
3. `m68k-elf-objcopy -O binary` -> `build/rom.raw`
4. `tools/rom/mkrom.py` pads to `rom_size` with `fill_byte` from `tools/rom/rom-config.json`,
   writes the ROM and its SHA-256
5. `tools/rom/validate.py` runs structural checks

Determinism: no step embeds timestamps, paths or host data in the raw binary (ELF metadata is
dropped by `objcopy -O binary`). CI rebuilds from clean on the same runner and compares the hash.

Cross-machine reproducibility is **not continuously gated**: no expected hash is committed, because
it would change with every source edit. It was observed once: for commit `f1fbc76`, a local WSL
Ubuntu build and CI run 37743550988 (ubuntu-24.04) both produced
`7e377b24226b7d2bfeb265b0ecb463258e5ab6147b1bd09d3508877e1ea297f5`. Other hosts and toolchain
builds remain unverified.

## UNVERIFIED layout values

Until the ROM-layout specification (Issue #1, `docs/specifications/`) confirms them, these are
placeholders, not requirements:

- ROM size 131072 (128 KiB) and fill byte 0xFF - `tools/rom/rom-config.json`
- Link address 0 (image seen by the CPU at address 0) - `tools/build/rom.ld`
- Initial SSP 0x00FFFE00 - `src/boot/boot.s`
- No Mega-CD header, checksum or region data is emitted.

PR #16 (Issue #1) proposes 128 KiB as CONFIRMED (INV-001). Once its `invariants.json` is merged,
the validator enforces that from the specification; the config value stays the build input.

## Structural validator

`python3 -I -B tools/rom/validate.py ROM [--config FILE] [--invariants FILE]`

- The invariant schema (`schema_version` 2) and check vocabulary are owned by
  `docs/specifications/test-invariants.md` (Issue #1); the validator implements that document.
  When `docs/specifications/invariants.json` exists it is loaded.
- A malformed file is rejected before any check runs (exit 1): unsupported `schema_version`,
  missing/invalid fields, duplicate ids, unknown `check.type`, missing check parameters, or an
  entry that breaks the enforceability rule (`enforceable: true` only for `CONFIRMED` +
  `hardware` scope, or `PROJECT-RULE`).
- `enforceable: true` entries PASS or FAIL; a FAIL fails the build.
- `enforceable: false` entries are printed as SKIP with status, scope and the advisory
  outcome. They never count as PASS and never fail the build.
- A read past the end of the image fails that check.
- Built-in checks (always run, toolchain/CPU level only): size equals the configured `rom_size`
  (build consistency; the value itself is UNVERIFIED), and the 68000 initial SSP and PC longwords
  at offsets 0 and 4 are readable and even.

Supported `check.type` values: `size_equals`, `u32_even`, `u32_range`, `u32_in_ranges`,
`u32_even_each`, `u32_each_in_ranges`, `u16_in`, `bytes_equal`, `bytes_equal_any`, `bytes_not_in`.
`tools/rom/testdata/invariants-issue1.json` is a copy of the Issue #1 file used as a test fixture.

## Alternatives evaluated

See [ADR 0001](adr/0001-toolchain.md) for the comparison of vasm, GNU binutils and others.
