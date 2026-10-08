# Architecture (working design)

This is a design outline, **not a verified hardware specification**.

## Execution model

- Produce machine code executed by Mega-CD's 68000 subsystem; do not depend on emulator-only BIOS interception.
- Clearly separate reset/startup code, hardware abstraction, CD services, BIOS-compatible entry points and test fixtures.
- Keep region-specific policies/data isolated from the hardware-neutral core.
- Treat Main CPU / Sub CPU communications, memory mapping, vectors, exception handling and timing as individually testable concerns.

## To verify before first ROM release

- ROM size, header, mapping and reset-vector requirements per target hardware and emulator.
- Main/Sub CPU startup and communication protocol.
- Word RAM arbitration and ownership.
- CDD/CDC initialization and data-transfer semantics.
- BIOS API entry points and calling conventions used by homebrew/commercial software.
- Region differences and startup behavior.

A frequently cited 128 KiB size is a **hypothesis to verify** against target hardware rather than an accepted implementation requirement.

## Proposed source layout

- `src/boot/`: reset vectors and startup assembly
- `src/hw/`: memory mapped peripheral access
- `src/services/`: disc and BIOS-facing services
- `tests/`: self-contained synthetic test programs and emulator harnesses
- `tools/`: reproducible ROM build and validation scripts

Only add these directories once implementations exist; Git does not track empty directories.

## Verification principle

Do not claim a feature works based on compilation alone. Distinguish ROM construction, emulator load, trace-observed behavior, game boot and tested gameplay.
