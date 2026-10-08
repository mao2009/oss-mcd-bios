# oss-mcd-bios

An open-source replacement BIOS project for the **Sega Mega-CD / Sega CD**.

> **Status: planning / bootstrap.** This repository does not yet provide a bootable BIOS ROM, game compatibility, or hardware support.

## Goals

- Produce a redistributable BIOS ROM using original or **license-audited, appropriately reused/adapted OSS** code and original or appropriately licensed assets.
- Prioritize **emulator compatibility**, while preserving the ability to run on real hardware.
- Target booting homebrew CD software first, then progressively improve commercial-game compatibility.
- Support regional Mega-CD / Sega CD variants when verified.
- Avoid emulator-specific hooks in the ROM itself. Emulator harnesses may be used for tests.

## Non-goals (initially)

- Recreating Sega's boot animation or copyrighted artwork.
- Byte-for-byte replication of proprietary BIOS ROMs.
- Claiming commercial-game compatibility before it has been independently verified.

## Development approach

1. Search existing OSS BIOS/runtime implementations first; audit the exact files and licenses before direct reuse, adaptation or reference-only use. Document observable behavior, register maps, timing assumptions and their sources.
2. Implement a minimal 68000 reset and boot path.
3. Verify CPU startup and inter-CPU communication with repeatable emulator tests.
4. Add disc detection, sector access and a minimal homebrew boot path.
5. Extend BIOS-facing service compatibility and test against multiple emulators and, later, hardware.

See [architecture](docs/architecture.md), [compatibility testing](docs/compatibility.md), [legal and provenance policy](docs/provenance.md) and [roadmap](docs/roadmap.md).

## Build

No functional BIOS implementation or supported ROM build command exists yet. A reproducible cross-assembler/toolchain and linker layout will be introduced and tested in a separate milestone. **Do not mistake a green documentation CI run for a bootable BIOS.**

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md). Contributions may contain independently authored code or audited, license-permitted OSS reused/adapted code. Never submit Sega BIOS dumps, extracted assets, copied disassembly or unapproved third-party code.

## License

Project-authored source code and original documentation are licensed under the [MIT License](LICENSE). Approved third-party code retains its **own** copyright, license and notice obligations; this repository's MIT license does not relicense it. Hardware documentation and third-party references retain their respective owners' rights.
