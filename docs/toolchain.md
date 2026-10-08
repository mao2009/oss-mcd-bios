# Build toolchain

Decision record: [ADR 0001](adr/0001-toolchain.md). Tracking issue: #2.

> A successful build proves only that original source assembles, links and passes
> structural checks. It does **not** prove the ROM boots on any emulator or hardware.

## Build

```sh
make          # first run: fetch + SHA-256-verify + build pinned binutils (~a few minutes, -j2)
              # then: assemble, link, pad, print ROM SHA-256, run structural validator
make test     # validator unit tests (Python stdlib only)
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

| Item | Value |
| --- | --- |
| Package | GNU binutils (gas, ld, objcopy only), target `m68k-elf` |
| Version | 2.42 |
| Source | `https://ftp.gnu.org/gnu/binutils/binutils-2.42.tar.xz` |
| SHA-256 | `f6e4d41fd5fc778b06b7891457b3620da5ecea1006c6a4a41ae998109f85a800` |
| License | GPL-3.0-or-later (tool only; see below) |

The hash was computed from downloads from both `ftp.gnu.org` and `mirrors.kernel.org`
(identical). `tools/build/toolchain.sh` refuses to build if the tarball hash differs.
Upgrading = change version + hash in that one script (the CI cache key follows the script hash).

## Pipeline

1. `src/boot/boot.s` -> `m68k-elf-as -m68000` -> `build/boot.o`
2. `tools/build/rom.ld` -> `m68k-elf-ld` -> `build/rom.elf`
3. `m68k-elf-objcopy -O binary` -> `build/rom.raw`
4. `tools/rom/mkrom.py` pads to `rom_size` with `fill_byte` from `tools/rom/rom-config.json`,
   writes the ROM and its SHA-256
5. `tools/rom/validate.py` runs structural checks

Determinism: no step embeds timestamps, paths or host data in the raw binary (ELF metadata is
dropped by `objcopy -O binary`). CI rebuilds from clean and compares the hash.

## UNVERIFIED layout values

Until the ROM-layout specification (Issue #1, `docs/specifications/`) confirms them, these are
placeholders, not requirements:

- ROM size 131072 (128 KiB) and fill byte 0xFF - `tools/rom/rom-config.json`
- Link address 0 (image seen by the CPU at address 0) - `tools/build/rom.ld`
- Initial SSP 0x00FFFE00 - `src/boot/boot.s`
- No Mega-CD header, checksum or region data is emitted.

## Structural validator

`python3 -I tools/rom/validate.py ROM [--config FILE] [--invariants FILE]`

- Built-in checks (toolchain/CPU-level only): ROM file readable; size equals the configured
  `rom_size` (build consistency, not a hardware claim); 68000 initial SSP and PC (offsets 0 and 4)
  readable as big-endian longwords and even.
- If `docs/specifications/invariants.json` exists, its checks are added. **Only entries with
  `"status": "CONFIRMED"` are enforced**; all others are printed as SKIP.
- A CONFIRMED entry with an unknown `kind` or bad parameters **fails** (fail closed).

Invariant entry schema (file is either a list or `{"invariants": [...]}`):

```json
{"id": "reset-pc-even", "status": "CONFIRMED", "kind": "u32_be_even", "offset": 4}
```

| kind | params |
| --- | --- |
| `size_equals` / `min_size` | `size` |
| `u32_be_even` | `offset` |
| `u32_be_equals` / `u16_be_equals` | `offset`, `value` |
| `bytes_equal` | `offset`, `hex` |

Numbers may be JSON integers or strings like `"0x1FE"`.

## Alternatives evaluated

See [ADR 0001](adr/0001-toolchain.md) for the comparison of vasm, GNU binutils and others.
