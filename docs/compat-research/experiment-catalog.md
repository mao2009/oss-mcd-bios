# Experiment catalog — proposals, not completed tests

The test descriptions below are **designs**. Do not manufacture selector numbers, memory addresses, constant timings, emulator traces or pass results.

| ID | Focus | Synthetic stimulus | Measure | Parent |
| --- | --- | --- | --- | --- |
| E-BOOT-01 | Reset and startup | Original minimal 68000 reset program | Initial vectors, SP/PC, checkpoints, exceptions, power-cycle behavior | #22 |
| E-ABI-01 | BIOS API contract | Canary-filled saved registers and buffer; one verified service call | Register/flag preservation, output buffers, synchronous/asynchronous return, errors | #23 |
| E-CD-01 | CD detection and sectors | Original disc with one/multiple tracks and repeat/invalid reads | Status transitions, TOC, data integrity, completion ordering, no-disc path | #24 |
| E-MEM-01 | CPU and Word RAM | Monotonic Main/Sub handshake across owner changes | Ownership, acknowledgment, missing writes, DMA boundaries | #25 |
| E-IRQ-01 | VSYNC and interrupts | Change IRQ mask/ack/reset schedule deterministically | Delivery order, wake-from-wait, pending state, callbacks | #26 |
| E-BURAM-01 | Save storage | Disposable synthetic saves and corrupt/overfull cases | Return status, content, error and persistence after power cycle | #27 |
| E-AUDIO-01 | CD-DA/PCM/fader | Synthetic tone CD tracks, PCM samples | Output/audio control, fader transitions and scheduler dependencies | #28 |
| E-REGION-01 | JP/US/EU profiles | Verified software paths under a controlled console matrix | Region acceptance, NTSC/PAL timing, model variation | #29 |
| E-GAME-01 | JP retail game | Locally and lawfully available user-owned reference | First divergence and menu/play/save/load checkpoints | #22–#29 |
| E-SNATCHER-01 | HLE-derived questions | Self-authored status/IRQ/DMA/save microprogram | CDBSTAT-like status fields, wait vsync, CD read pace, DMA stalls and boundary | #23–#28 |

## Common test protocol

- Fix firmware and emulator commit or hardware model; record hashes and versions.
- Reset to a known state. Repeat with one changed variable and retain control runs.
- Explicitly mark PASS / FAIL / SKIP / BLOCKED.
- Store only original fixture contents and sanitized traces, never third-party BIOS or game binaries.
- Compare **ordered events** before guessing cycle-perfect tolerances.
- Distinguish an author's reported observation from something executed by the oss-mcd-bios team.
- Use an independent reviewer to promote contracts; unresolved provenance remains tracked under #17.

## Special cautions

For backup RAM, use disposable state and backups; never perform destructive tests on user saves. For physical hardware, establish a safe loading and recovery process before testing. The candidate Word RAM DMA offset is a question for measurement, **not an implementation instruction**.
