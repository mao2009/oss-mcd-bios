# Mega-CD specifications (Issue #1)

Evidence-labelled notes on the Mega-CD / Sega CD ROM layout, boot requirements, memory map and BIOS-facing interfaces. Each claim records where it comes from and how sure we are. **Nothing here is a verified hardware specification until it is marked CONFIRMED.** Even CONFIRMED items still need emulator and hardware tests before release (see [compatibility](../compatibility.md)).

| File | Contents |
| --- | --- |
| [rom-layout.md](rom-layout.md) | BIOS ROM window, image size, reset vectors, header area, regions/models, boot sequence |
| [memory-map.md](memory-map.md) | Main/Sub CPU maps, Word RAM, PRG-RAM, gate-array registers, interrupts, CDC/CDD |
| [bios-api.md](bios-api.md) | Sub-CPU BIOS entry points, user calls, Main-side jump table |
| [open-questions.md](open-questions.md) | Contradictions, unknowns and proposed independent verification programs |
| [test-invariants.md](test-invariants.md) | Human-readable ROM structural invariants |
| [invariants.json](invariants.json) | Machine-readable invariants for the ROM validator |

## Evidence labels

| Label | Meaning |
| --- | --- |
| **CONFIRMED** | An official document (Sega manual or CPU vendor manual) states it, and at least one independent source (emulator source at a pinned commit, or an independent technical document) agrees, with no contradicting source found. We also use CONFIRMED for a claim scoped to an emulator (`scope: emulator:<name>`) when we have read the behaviour in that emulator's source at the pinned commit. An emulator-scoped claim **never** implies hardware behaviour. Purely logical consequences of CONFIRMED facts are marked "CONFIRMED (derived)". |
| **ESTIMATED** | Supported by only one class of source (emulators only, independent documents only, or an official page whose relevant part is unreadable), or inferred from other evidence. Plausible, but not cross-checked against official documents or measurement. |
| **UNCONFIRMED** | No adequate source, sources contradict each other, or the source is inaccessible. |

Only CONFIRMED invariants may be `enforceable: true` in `invariants.json`.

## Source register

Classes: **official** (Sega or the CPU vendor), **independent** (independent technical document or SDK), **emulator** (emulator implementation), **measured** (reproducible measurement on real hardware). This PR contains **no measured results of our own**. Some emulator comments say a behaviour was "verified on real hardware". We treat those as second-hand claims made inside emulator sources, not as measurements.

| ID | Source | Class | Version / commit | Access check (2026-10-08) | Licence / reuse |
| --- | --- | --- | --- | --- | --- |
| S-HW | *Mega-CD Hardware Manual: The Hardware*, page scans indexed at <https://www.megadrive.org/elbarto/megacd/Official%20Sega%20CD%20Manual/segacd_toc.html> (pages `MegaCD/Hardware/Cdh-NN.gif`) | official (third-party hosted scan) | Page footer "VER 1.0 1991/10/14" | HTTP 200. **Incomplete**: the outline page 4 is listed as "page missing" and page 45 is absent. Some scans are cropped, e.g. the high byte of `$A12002` on p.57 is blank. Pages carry "CONFIDENTIAL / PROPERTY OF SEGA" and a third-party watermark. | Proprietary. **Cite only**: do not reproduce text, tables or figures. Paraphrased facts only. |
| S-BIOS | *Mega-CD BIOS Manual*, same archive (`MegaCD/Bios/Bios-NN.gif`) | official (third-party hosted scan) | Page footer "Ver 2.00 Feb. 24 '92" | HTTP 200. The TOC lists sections 1–7 on pp.1–45. | Proprietary. Cite only. |
| S-SDM | *Mega-CD Software Development Manual*, same archive (`MegaCD/Soft-dev/Sdm-NN.gif`) | official | not read in this PR | TOC accessible. Pages **not reviewed**. | Proprietary. Cite only. |
| S-FMT | *Mega-CD Disc Format Specifications*, same archive (`MegaCD/Format/Fmt-NN.gif`) | official | not read in this PR | TOC accessible. Pages **not reviewed**. | Proprietary. Cite only. |
| S-M68K | *M68000 8-/16-/32-Bit Microprocessors User's Manual*, Motorola ©1993, <https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf> | official (CPU vendor) | ©1993 edition (revision string not extracted) | HTTP 200 (PDF) | Proprietary. Cite only. |
| O-SEGAJP | Sega corporate history page <https://www.sega.jp/history/hard/mega-cd/> | official (corporate) | n/a | **Inaccessible**: HTTP 403 (Cloudflare JavaScript challenge) from WebFetch and curl. Content **not verified**. A human needs to check it in a browser. | n/a |
| I-MEGADEV | MegaDev, <https://github.com/drojaazu/megadev> | independent (SDK + docs, partly reverse-engineered) | commit `7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef` (2026-05-10) | Cloned read-only | MIT (LICENSE: "Copyright (c) 2021 Damian Rogers"). MIT-compatible, but **nothing copied**. Facts only. |
| I-RHOPE | "Sega CD Development", <https://rhope.retrodev.com/segacd.html> | independent | Page footer "Copyright 2002-2004 by Michael Pavone" | **TLS certificate mismatch**: the certificate is for `www.retrodev.com`, and plain HTTP returns 502. Content was fetched with certificate verification disabled, so its integrity is **not guaranteed**. | No licence stated. Cite only. The page offers `base.img`, a dump of commercial-game boot data. **We did not download or use it.** |
| I-RETROSIX | "Hardware Overview (Sega Mega CD)", <https://retrosix.wiki/wiki/hardware-overview-sega-mega-cd> | independent | "Updated Apr 27, 2026" | **Inaccessible**: the article body requires a login. No claims are taken from it. | No licence stated |
| E-GPGX | Genesis Plus GX, <https://github.com/ekeeke/Genesis-Plus-GX> | emulator | commit `49c584764893b0505ac7f768a754f97330fa4392` (2026-10-06) | Cloned read-only | Non-commercial licence (see `core/cd_hw/scd.h` header). **Incompatible with MIT. Cite only, never copy.** |
| E-PICO | PicoDrive, <https://github.com/notaz/picodrive> | emulator | commit `26ecb2b6358fefba24e3d68b9eb2efba7f10d5ee` (2025-04-03) | Cloned read-only | Non-commercial licence (`COPYING`). **Incompatible with MIT. Cite only, never copy.** |

We used upstream `ekeeke/Genesis-Plus-GX` rather than the `mao2009` fork named in [reuse-from-projects.md](../reuse-from-projects.md). The harness issue should pin whichever revision it actually runs.

No Sega BIOS binary, dump or disassembly was obtained, read or used in preparing these notes.
