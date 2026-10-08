# Roadmap

Milestones are **proposals**, not release commitments. Release numbers depend on objective evidence.

## M0 — Project foundation

- [x] README, license and contribution policy
- [x] Architecture, provenance and compatibility documentation
- [ ] Verify ROM mapping, header and memory requirements against documented sources
- [ ] Select a reproducible 68000 assembler/linker toolchain with a pinned version
- [ ] Define CI test fixture and ROM structural validation

## M1 — Minimal ROM

- [ ] Build ROM image with reset vector and deterministically reproducible hash
- [ ] Boot to a measured checkpoint in a pinned emulator
- [ ] Verify startup behavior with automated emulator traces
- [ ] Document limitations; no commercial-game claims

## M2 — Homebrew CD boot

- [ ] Verify inter-CPU communication and Word RAM ownership
- [ ] Implement essential disc detection and sector reads
- [ ] Boot an independently authored minimal CD program
- [ ] Reproduce on at least two independently implemented emulators

## M3 — BIOS compatibility

- [ ] Identify and implement game-facing BIOS interfaces by observed behavior
- [ ] Track title-level compatibility with versioned test evidence
- [ ] Add region-dependent behavior only when verified

## M4 — Physical hardware

- [ ] Define safe flashing/loading method and recovery precautions
- [ ] Validate boot and CD handling on supported Mega-CD hardware
- [ ] Record model/region-specific limitations

**Current status: M0, documentation only.**
