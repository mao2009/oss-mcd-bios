# Priorities and decision gates

**Product goal:** Commercial Mega-CD / Sega CD game compatibility without an original Sega BIOS, Japan required, US/EU and multi-region desirable, real hardware eventually, all titles aspirational.

## Gate G0 — source validity

Issue #17 governs confidential scans, reverse-engineering-derived documents and permissions. Technical plausibility is not provenance approval. Do not transplant emulator, HLE or decompiled game code into MIT BIOS.

## Gate G1 — observability before compatibility

Pin actual toolchain and real GPGX test-core revisions, run true emulator smoke tests (not only mocks) and record artifacts. Builds do not prove boot; boot does not prove a game works.

## Gate G2 — one legal JP commercial path

Define one Japanese retail title edition and sequence (boot, disc transfer, API, menu, input, audio, save/load). Trace earliest mismatch against a permitted reference environment and reduce it to a synthetic repro. If reference environment or disc is unavailable, mark BLOCKED.

## Gate G3 — behavior and breadth

Continue improving the general API/CPU/CD/IRQ/storage/audio behavior as measured in multiple titles. Never assert support for untested game editions. Keep US Snatcher observations distinct from JP game expectations.

## Gate G4 — region and hardware

Track game release region, virtual console region, PAL/NTSC video mode, BIOS profile and physical model separately. An emulator's region-free setting does not automatically prove a standalone universal BIOS ROM works on physical hardware.

## Decision examples

| Observation | Next action |
| --- | --- |
| ROM builds but no actual emulator startup trace | Finish #3/#5/#19 integration before claims |
| Game is blocked before first API call | Inspect boot/region/CPU/CD handoff |
| Unknown API invocation | Add contract under #23 or owning functional parent |
| Call returns but game stalls | Investigate wait/IRQ/timing/status and memory side effects |
| Game works only with emulator HLE | Identify hardware services HLE hides; design independent 68000 implementation |
| Emulator A/B disagree | Independent synthetic experiment; check shared ancestry |
| Code/data origin unclear | Hold dependent implementation, send to #17 |

Avoid chasing specification-count increases without a demonstrable retail-game critical path. Source read, test proposed, test executed, and implementation verified are different states.
