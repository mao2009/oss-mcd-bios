# Contributing

Thank you for supporting a redistributable replacement BIOS.

## Before writing code

- Read [provenance/reuse rules](docs/provenance.md), the [candidate inventory](docs/reuse-inventory.md), and [architecture](docs/architecture.md).
- Search existing OSS BIOS/runtime code first; prefer audited direct reuse, then audited adaptation, then behavior/test references, then new code. Open an issue explaining the target behavior, reuse choices/rejections, public references, observed evidence and expected tests.
- Keep contributions focused and testable. Do not include proprietary ROM material or copyrighted extracts.
- For functional changes, supply reproducible build commands, emulator/firmware versions and test evidence.
- For uncertain specifications, label them explicitly as hypotheses.

## Pull requests

Include:

- Why the change is needed and what is newly supported.
- Exact URL/commit/file/hash, rights holder, file-level license, dependency rights, modification records and source/binary NOTICE duties for any incorporated third-party code, with human approval before merge. An unclear license is a blocked import.
- Exact testing environment, commands and results.
- Known regressions and remaining limitations.

## Review gates

- Correctness and traceability come before speed.
- Documentation CI checks formatting and links only; they do not prove BIOS correctness.
- No compatibility or hardware-support claims without reproducible verification.
