# Snatcher Sega CD HLE: source-backed case study

**Status:** external author's public report, not a verified oss-mcd-bios test. No game data or HLE code is incorporated.

## Sources

- [bgyss/snatcher-port](https://github.com/bgyss/snatcher-port) — research project using user-supplied disc data and its own tools.
- [Author's report, October 5 2026](https://www.reddit.com/r/decomps/comments/1wygdej/im_reverseengineering_snatcher_sega_cd_into_a/) — Sega CD 1994 **US edition**, native PC program progress.
- [Repository readme](https://github.com/bgyss/snatcher-port/blob/main/README.md) and documentation are additional research starting points, not a license to reuse reconstructed proprietary materials.

## What the author actually reported

The author's program runs game 68000 code for Main/Sub CPUs through a core/translation path and handles Sega CD BIOS calls in **host-side C++ HLE**, without requiring a BIOS file. The author reports an intro and transition into the first in-game scene with audio. This is **not** a claim that the entire game completes, that Japanese games work, or that a standalone m68k BIOS ROM already exists.

## Candidate compatibility requirements (NOT proven hardware contracts)

| Case | Author-reported difficulty | Independent test question | Parent |
| --- | --- | --- | --- |
| SN-01 | CDBSTAT returned time/status fields | Which CD status fields and update ordering does software observe? | #24, #23 |
| SN-02 | BURAM result/status | Which save operation statuses and persistence rules matter? | #27 |
| SN-03 | V-INT relative to VBLANK | What is the ordering of VBLANK, IRQ and handler processing? | #26 |
| SN-04 | CD read speed | What completion/polling sequence and latency behavior does the caller require? | #24 |
| SN-05 | _WAITVSYNC pausing the Sub CPU | Which precise wait/awake conditions are observable? | #26, #25 |
| SN-06 | DMA stalls | Can transferring data stall CPU work or delay completion? | #25, #24 |
| SN-07 | Word RAM DMA offset by one word | Is it a hardware effect, emulator model detail, or particular flow assumption? | #25 |

These entries are *questions generated from a third-party report*, not adopted selector tables, registers, code, cycle constants, proprietary game code or observed results of this project.

## How to apply without contaminating oss-mcd-bios

1. Use this case study to prioritize questions, not to copy the HLE implementation or the game's translated program.
2. Review its source provenance separately, including whether any derived observations can be used under Issue #17.
3. Build independently authored synthetic status-poll, IRQ, BURAM and Word RAM/DMA tests.
4. Compare permitted independent emulators and authorized reference BIOS environment when available.
5. Only accept a contract after source permission review and independent validation.
6. Avoid creating a US Snatcher game-title-specific behavior in BIOS unless there is a defensible and independently tested need.

The report is valuable because it names plausible classes of hidden game/BIOS dependencies. It does not by itself increase the 47.5% specification coverage metric.
