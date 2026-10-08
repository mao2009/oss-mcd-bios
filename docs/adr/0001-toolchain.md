# ADR 0001: 68000 build toolchain

- Status: Proposed (Issue #2)
- Date: 2026-10-08

## Context

The BIOS ROM must be built from original source by a pinned, redistributable, open toolchain
that runs reproducibly on Linux CI and locally. The project is MIT-licensed and aims to
distribute the ROM, so the toolchain license must place no restriction on the output or on
commercial redistribution of the output.

## Options

| Criterion | GNU binutils `m68k-elf` (gas + ld) | vasm (m68k, mot syntax) + vlink | Ubuntu `binutils-m68k-linux-gnu` package | asmx / other small assemblers |
| --- | --- | --- | --- | --- |
| License | GPL-3.0-or-later; output is not covered by the GPL | Custom freeware license by the author: free for non-commercial use; commercial use and distribution of modified versions require the author's written permission (re-check current text before relying on this summary) | GPL-3.0-or-later | Varies; some unclear or unmaintained |
| Fit with MIT, redistributable ROM | Good | Questionable: "commercial use" restriction is ambiguous for third parties who may sell media containing the ROM | Good | Case by case |
| Pinning | Versioned GNU release tarballs; SHA-256 pinned in-repo | Release tarballs exist, but the commonly linked download is an unversioned "latest" archive; must pin a tagged archive explicitly | Version tied to Ubuntu release + archive snapshot; weaker pin | Often git-only |
| Linux CI reproducibility | Builds from source in a few minutes with stock compiler, cacheable | Very fast to build (small C program) | apt install, fast, but changes with Ubuntu updates | Varies |
| Linker / object format | ELF objects, full linker scripts, `objcopy -O binary` | vlink supports linker scripts and raw binary output | Same as binutils | Often single-file, no linker |
| Motorola syntax | MIT/Motorola mixed GAS syntax (`%d0` registers, vertical-bar comments); not classic Motorola | Native Motorola syntax (devpac-like), familiar to Mega Drive developers | Same as binutils | Usually Motorola |
| Ecosystem | Same object format as m68k-elf-gcc if C is ever used for host-independent parts | Popular in Amiga/Mega Drive homebrew | Same as binutils | Small |

## Decision

Use **GNU binutils 2.42, target `m68k-elf`**, built from the pinned source tarball
(SHA-256 `f6e4d41fd5fc778b06b7891457b3620da5ecea1006c6a4a41ae998109f85a800`) by
`tools/build/toolchain.sh` from the pin in `tools/build/toolchain.lock`, invoked through a single
`make` command.

Reasons: unambiguously free license with no output restriction, exact source pinning with a
hash check, ELF + linker scripts for later multi-file layout, and a straightforward CI build.
Only the toolchain binary is used; no binutils code is copied into this repository.

## Consequences

- Sources use GAS m68k syntax, not classic Motorola syntax. Contributors familiar with vasm/asm68k
  syntax must adapt.
- First CI run builds binutils (minutes); later runs use the Actions cache keyed on the script and lock-file hashes.
- Upgrading the toolchain is a single reviewed change of version, URL and SHA-256 in `toolchain.lock`.
- vasm may be reconsidered if its author grants clear permission compatible with redistributing
  the ROM commercially; switching would require rewriting syntax-dependent sources.
- Not decided here: ROM layout, size, header and mapping (Issue #1). Those values remain
  UNVERIFIED configuration (see `docs/toolchain.md`).
