# Contributing

Thank you for supporting a redistributable replacement BIOS.

## Before writing code

- Read [provenance rules](docs/provenance.md) and [architecture](docs/architecture.md).
- Open an issue explaining the target behavior, public references, observed evidence and expected tests.
- Keep contributions focused and testable. Do not include proprietary ROM material or copyrighted extracts.
- For functional changes, supply reproducible build commands, emulator/firmware versions and test evidence.
- For uncertain specifications, label them explicitly as hypotheses.

## Pull requests

Include:

- Why the change is needed and what is newly supported.
- Sources/provenance for protocol details and any incorporated third-party code.
- Exact testing environment, commands and results.
- Known regressions and remaining limitations.

## Review gates

- Correctness and traceability come before speed.
- Documentation CI checks formatting and links only; they do not prove BIOS correctness.
- No compatibility or hardware-support claims without reproducible verification.
