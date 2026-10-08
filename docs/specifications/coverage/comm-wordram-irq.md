# Coverage audit: Main/Sub communication, Word RAM, interrupts (prefix COM-)

> [!WARNING]
> Research notes only. Nothing here is an implementation basis until a maintainer accepts it. The official Sega manuals (S-HW, S-BIOS) are CONFIDENTIAL / PROPERTY OF SEGA scans. Issue #17 has not decided their status, so this audit records them as **leads only**. They are **excluded** whenever we judge "implementable from public material only". Emulator behaviour is not hardware truth. MegaDev is partly reverse-engineered.

Audit date: 2026-10-08. Scope: gate-array registers for Sub-CPU reset and bus request, communication flags, command and status words, and Main/Sub handshakes. Also: Word RAM 1M/2M modes and ownership (DMNA/RET), the PRG-RAM bank and write protect, interrupt sources and vectors on both CPUs, the stopwatch and timer, the graphics ASIC only as far as a BIOS must care, and timing constraints. CDC/CDD internals, subcode, PCM and backup RAM belong to other audit areas. They appear here only where they raise an interrupt or touch Word RAM or PRG-RAM.

Evidence labels follow [../README.md](../README.md): **CONFIRMED**, **ESTIMATED** and **UNCONFIRMED**. "CONFIRMED (scope: emulator)" means we read the behaviour in that emulator's source at the pinned commit. It says nothing about hardware.

## 0. Source register (this audit)

Every `path:line` below is relative to the URL base given here, at the pinned commit. Each repository was shallow-cloned (depth 1) into the session scratchpad, outside this repository. Nothing was copied from any source into this repository. Facts are paraphrased.

| ID | Source and URL base | Class | Commit / date | Licence / usage terms | Excluded from "public only"? |
| --- | --- | --- | --- | --- | --- |
| E-GPGXF | Genesis Plus GX fork, `https://github.com/mao2009/Genesis-Plus-GX/blob/87dd8b80802ff5217ab2f765202b6b14ecd23f94/` | emulator | `87dd8b80802ff5217ab2f765202b6b14ecd23f94` (2026-08-21) | Non-commercial licence. Cite facts only, never copy. Line numbers are those of this **fork** (the PR #15 harness pin), not the upstream `49c5847` used in [../memory-map.md](../memory-map.md). `scd.c` and `mem68k.c` are shifted (OQ-20). | No (scope: emulator) |
| E-PICO | PicoDrive, `https://github.com/notaz/picodrive/blob/26ecb2b6358fefba24e3d68b9eb2efba7f10d5ee/` | emulator | `26ecb2b6358fefba24e3d68b9eb2efba7f10d5ee` (2025-04-03) | Non-commercial (`COPYING`). Cite only. | No |
| E-CLOWN | clownmdemu-core, `https://github.com/mao2009/clownmdemu-core/blob/15c6cba32bdaab3320056ff762e159951f85367a/` | emulator | `15c6cba32bdaab3320056ff762e159951f85367a` (2026-06-07) | AGPL-3.0 (`LICENCE.txt`). Incompatible with MIT for code reuse. Cite facts only. It embeds a binary boot ROM (`source/mega-cd-boot-rom.c`, referenced at `source/bus-main-m68k.c:18-21`) built from I-CLOWNBOOT. Disc boot and Sub-BIOS calls are high-level emulated (`source/clownmdemu.c:496-527`, `source/bus-sub-m68k.c:64-327`). | No |
| I-CLOWNBOOT | clownmdemu-mcd-boot, `https://github.com/Clownacy/clownmdemu-mcd-boot/blob/ebdf03cda77383bda3d1c9e4d69f89a1d19d7233/` | independent (an existing open replacement boot ROM) | `ebdf03cda77383bda3d1c9e4d69f89a1d19d7233` (2025-09-07) | ISC/0BSD-style permissive (`LICENSE`, "Copyright (c) 2025 Devon Artmeier and Clownacy"). MIT-compatible in principle, but the **knowledge provenance is not stated**: it may derive from the official manuals or from original-BIOS disassembly. The README says it targets ClownMDEmu specifically. **New lead, not in the README source register.** | No, with provenance caveat |
| I-MEGADEV | MegaDev, `https://github.com/drojaazu/megadev/blob/7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef/` | independent SDK (Main-BIOS parts are RE per `docs/main_bios.md:12`) | `7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef` (2026-05-10) | MIT. Facts only. | No (RE-derived parts flagged) |
| S-M68K | Motorola M68000 UM, <https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf> | official (CPU vendor) | ©1993 | Proprietary, cite only | No |
| S-HW / S-BIOS | Official Mega-CD Hardware / BIOS manual scans (see [../README.md](../README.md)) | official, CONFIDENTIAL-marked | VER 1.0 1991/10/14; Ver 2.00 1992-02-24 | Proprietary, CONFIDENTIAL | **Yes (lead only, Issue #17)** |
| L-VERIF | krikzz "mcd-verificator" hardware test tool, announced at <https://gendev.spritesmind.net/forum/viewtopic.php?p=36642> | measured (third-party HW test program) | not pinned | Licence unknown. Binary and source **not obtained or run**. Known only through E-GPGXF comments ("verified on real hardware, cf. Krikzz's mcd-verificator") and E-PICO `pico/cd/memory.c:458`. | No, but second-hand |
| L-GD | SpritesMind forum threads cited by E-CLOWN: <https://gendev.spritesmind.net/forum/viewtopic.php?p=15269>, <https://gendev.spritesmind.net/forum/viewtopic.php?p=16388> | independent (forum) | n/a | No licence. **Not fetched in this audit.** | No (second-hand) |
| O-SEGAJP | <https://www.sega.jp/history/hard/mega-cd/> | official (corporate) | n/a | **Retried 2026-10-08 via WebFetch: HTTP 403 Forbidden.** Content not verified. | n/a |

Official page scans exist in the session scratchpad (`manual/Cdh-12,13,14,16,17,30,56,57.gif`, `Bios-04,30,31,33,35.gif`), downloaded by an earlier agent. They were **not used** in this audit; only their existence is recorded. No Sega BIOS binary, dump or disassembly was obtained, read or used.

## 1. Enumerated required behaviours

Level = the minimum level that needs the behaviour. **LA** = minimal BIOS boot (both CPUs up, own code runs). **LB** = boots a homebrew CD program (IP/SP load and run, with comms, Word RAM and interrupts usable). **LC** = commercial-game-compatible BIOS.

**A. Main-side Sub-CPU control (`$A12000-$A12003`)**
- COM-01 (LA) Writing SRES (`$A12001` bit 0) = 0 holds the Sub CPU in reset. 1 releases it, and a reset pulse occurs on the 0→1 transition.
- COM-02 (LA) SRES read-back reports reset state, so the BIOS can poll for completion.
- COM-03 (LA) SBRQ (`$A12001` bit 1) requests the Sub bus. Read-back acknowledges the halt.
- COM-04 (LA) Power-on value of `$A12000-$A12003` (Sub in reset, bus requested, 2M mode, Main owns Word RAM).
- COM-05 (LC) Writing SRES = 0 forces SBRQ to read 1.
- COM-06 (LC) SBRQ ack stays 0 while the Sub CPU is stopped by the STOP instruction.
- COM-07 (LA) Main access to the PRG-RAM window `$020000-$03FFFF` works only while the Sub is bus-requested or held in reset.
- COM-08 (LA) BK0/BK1 (`$A12003` bits 6-7) select which 128 KiB PRG-RAM bank appears in the window.
- COM-09 (LA) Write protect WP0-7 (`$A12002`) blocks **Sub** writes below WP×512 bytes of PRG-RAM.
- COM-10 (LC) WP is written only from the Main side. The Sub reads it at `$FF8002`. A Sub byte write to `$FF8002` acts on the memory-mode bits.
- COM-11 (LB) IFL2 (`$A12000` bit 8) write 1 raises Sub level 2, but only if IEN2 is set.
- COM-12 (LB) IEN2 (`$A12000` bit 15) on the Main side mirrors Sub mask bit IEN2.
- COM-13 (LC) IFL2 read-back and clearing semantics (cleared by Sub acknowledge; whether writing 0 cancels it).
- COM-14 (LA) Access-width constraint: only BTST is said to be safe on `$A12000`, so read-modify-write could have side effects.
- COM-15 (LC) Main register block `$A12000-$A1203F` mirrored up to `$A120FF`.

**B. H-INT vector, stopwatch**
- COM-16 (LB) `$A12006` supplies the low word of the H-INT vector, overriding the ROM word at `$72`.
- COM-17 (LC) High word of the H-INT vector (ROM `$70`) (cross-ref R-17 / OQ-1).
- COM-18 (LC) Stopwatch `$A1200C`/`$FF800C`: 12-bit, 30.72 µs per tick, a Sub write clears it, the Main side can only read it.
- COM-19 (LC) Stopwatch phase on clear (is the 384-cycle prescaler reset?).

**C. Communication registers**
- COM-20 (LA) `$A1200E`: Main flag byte, read/write from Main, read-only from Sub.
- COM-21 (LA) `$A1200F` / `$FF800F`: Sub flag byte, written by Sub, read-only from Main.
- COM-22 (LC) A byte write to either half of the flag word updates only the writer's own half (/LDS, /UDS and /LWR are ignored).
- COM-23 (LA) `$A12010-$A1201F`: eight command words, Main→Sub. Sub writes are ignored.
- COM-24 (LA) `$A12020-$A1202F`: eight status words, Sub→Main. Main writes are ignored.
- COM-25 (LB) Byte-granular reads and writes of command and status words.
- COM-26 (LB) Comm registers are cleared at power-on and are not cleared by a Sub peripheral reset (`$FF8001` RES0).
- COM-27 (LB) The BIOS leaves the comm registers in a defined (cleared) state at IP/SP entry.
- COM-28 (LC) Behaviour when both CPUs access the same register at once. No hardware lock exists.
- COM-29 (LC) Wait states and latency of gate-array register accesses from each CPU.

**D. Handshake protocols**
- COM-30 (LA) Our own BIOS-internal boot handshake between Main and Sub (design freedom, built on COM-20 to COM-24).
- COM-31 (LB) The Main BIOS default V-INT handler raises IFL2 every frame, which drives the Sub level-2 cadence.
- COM-32 (LB) The Sub BIOS level-2 handler calls the SP "usercall2" entry.
- COM-33 (LB) The Sub BIOS main loop calls the SP init and main entries ("usercall0/1") in step with level 2, under a return-code contract.
- COM-34 (LB) The Main BIOS waits until the Sub BIOS and SP are ready before jumping to the IP.
- COM-35 (LC) The original Main-BIOS library's "predefined comm flag semantics" (COMM_SYNC and related calls) used by some games.
- COM-36 (LC) Comm-register contents and flag bits that commercial software expects at IP/SP entry and during BIOS-driven disc access.

**E. Word RAM ownership and modes**
- COM-37 (LA) At power-on, Word RAM is in 2M mode and owned by Main.
- COM-38 (LB) 2M mode: Main writes DMNA = 1, ownership passes to Sub, and RET reads 0.
- COM-39 (LB) 2M mode: Sub writes RET = 1, ownership returns to Main, and DMNA clears.
- COM-40 (LC) 2M mode: Main writing DMNA = 0 has no effect.
- COM-41 (LC) Non-owner access in 2M mode. Main: unmapped or open bus. Sub: stalls with no /DTACK (OQ-4).
- COM-42 (LC) Latency of an ownership change, and the observable transient values of DMNA and RET.
- COM-43 (LB) The Sub MODE bit switches 2M↔1M, and data is re-arranged between the interleaved 2M layout and the two 1M banks.
- COM-44 (LB) 1M mode: RET selects which bank belongs to Main and which to Sub.
- COM-45 (LC) 1M mode: Main writes DMNA = **0** to request a bank swap, and DMNA reads 1 until the Sub completes the swap.
- COM-46 (LC) 1M mode: Main writing DMNA = 1 is remembered and gives Word RAM to Sub on return to 2M.
- COM-47 (LC) Which CPU owns Word RAM after a 1M→2M switch.
- COM-48 (LC) 1M mode: Main-side cell-image view at `$220000-$23FFFF`.
- COM-49 (LC) 1M mode: Sub-side dot-image view at `$080000-$0BFFFF`, with PM0/PM1 priority write modes.
- COM-50 (LB) 1M mode: Sub-side bank at `$0C0000-$0DFFFF`.
- COM-51 (LC) The Main read of `$A12003` masks PM0/PM1, and the Sub read of `$FF8003` masks BK0/BK1.
- COM-52 (LB) Word RAM mode and owner at IP/SP entry.
- COM-53 (LC) A CDC DMA to Word RAM or PRG-RAM is suspended or resumed when ownership or SBRQ changes.
- COM-54 (LC) A graphics operation needs 2M mode with Word RAM owned by Sub.

**F. PRG-RAM use by the BIOS**
- COM-55 (LA) The Main BIOS copies the Sub BIOS into PRG-RAM through the bank window before releasing Sub reset.
- COM-56 (LA) The Sub CPU fetches its reset SSP/PC from PRG-RAM `$000000`.
- COM-57 (LB) The SP is placed at PRG-RAM `$6000` and the BIOS area is write-protected.
- COM-58 (LC) Mode 1 (cartridge) software finds and loads the Sub BIOS from the boot ROM by a signature or format convention.

**G. Sub-side gate-array housekeeping**
- COM-59 (LC) `$FF8000` LED control bits.
- COM-60 (LA) `$FF8001` RES0: writing 0 resets the CD peripherals; the register reads back 1.
- COM-61 (LC) `$FF8000-1` version field.
- COM-62 (LC) Sub register decode uses A1-A8, so `$FF8000-$FF81FF` is mirrored.
- COM-63 (LB) The Sub BIOS sets the Word RAM mode and owner during its own initialisation.

**H. Sub-CPU interrupts**
- COM-64 (LA) Mask register `$FF8033`: bit n enables level n (n = 1..6).
- COM-65 (LA) The highest pending enabled level is presented on the IPL lines and taken as an autovector.
- COM-66 (LC) Pending-latch semantics while masked: a request is either dropped or latched and taken later on unmask.
- COM-67 (LB) Acknowledge clears the pending request. A level-2 acknowledge also clears IFL2.
- COM-68 (LC) Clearing IEN1 discards a pending level 1.
- COM-69 (LC) Level 1: graphics operation complete.
- COM-70 (LB) Level 2: Main CPU software interrupt (IFL2).
- COM-71 (LB) Level 3 timer `$FF8031`: period (n or n+1) × 30.72 µs, writing 0 stops it, it auto-reloads.
- COM-72 (LB) Level 4: CDD status at 75 Hz while CDD communication is enabled (`$FF8037` bit 2).
- COM-73 (LB) Level 5: CDC /INT falling edge.
- COM-74 (LC) Level 6: subcode buffer complete.
- COM-75 (LA) Level 7, spurious interrupt and unused vectors need safe handlers.
- COM-76 (LB) Sub exception vectors route through a RAM jump table at about `$5F40-$5FFF` that the SP may patch.
- COM-77 (LC) Sub interrupt latency and its cycle timing relative to the source events.

**I. Main-CPU interrupts**
- COM-78 (LA) The VDP raises V-INT at level 6 and H-INT at level 4 (standard Mega Drive).
- COM-79 (LB) Main vectors route through a RAM jump table at `$FFFD00` (6-byte JMP entries) at fixed slots that the IP patches.
- COM-80 (LB) The Mega-CD has no Sub→Main hardware interrupt, so the Main CPU must poll. Level 2 is the external port only.
- COM-81 (LB) CPU state at IP entry: SR/IPL, VDP V-INT enable, stack pointer, registers.
- COM-82 (LC) Behaviour of the default Main V-INT and H-INT handlers that games rely on.

**J. Timing and initialisation**
- COM-83 (LB) Sub CPU clock is 12.5 MHz (50 MHz / 4). The gate-array timer base is 384 Sub clocks = 30.72 µs.
- COM-84 (LA) Latency from releasing Sub reset to the Sub executing its first instruction.
- COM-85 (LC) Main/Sub polling races, such as a game checking Word RAM ownership just after the Sub hands it back.
- COM-86 (LA) Whether the gate array needs a "forced reset" or initialisation sequence at boot (OQ-10).

**K. Graphics ASIC (BIOS-relevant only)**
- COM-87 (LC) The BIOS leaves the graphics unit idle at SP entry. A write to `$FF8066` starts an operation.
- COM-88 (LC) Font/1bpp conversion registers `$FF804C-$FF8057`. The BIOS does not need them.
- COM-89 (LC) Stamp, rotation and scaling semantics. This is hardware, not BIOS behaviour, but it is needed for the test harness.
## 2. Coverage table

Abbreviations: G = E-GPGXF, P = E-PICO, C = E-CLOWN, CB = I-CLOWNBOOT, MD = I-MEGADEV. "Implementable": **Y** = non-excluded sources define a testable behaviour without conflict. **Cond** = defined, but single-source, conflicting or design-dependent. **N** = no usable non-excluded definition.

| ID | Required behavior | Level | Existing material (Y/N/partial) | Exact reference URL + location | Provenance & usage terms | Implementable from public material only? (Y/Cond/N + why) | Specific missing information | Coverable by own test? | Verifiable in emulator only? | Real hardware needed? | Blocker? (Y/N + why) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COM-01 | SRES hold/release, reset on 0→1 | LA | Y | G `core/mem68k.c:1055-1086`; P `pico/cd/memory.c:183-202`; C `source/bus-main-m68k.c:1122-1151`; CB `src/main/main.asm:75-77,91-93`; MD `lib/main/gate_arr.def.h:25-52`; S-HW §4-1 p.56 (excluded) | Emulators non-commercial/AGPL (facts only); CB permissive; MD MIT | Y: three emulators, MD and CB agree. CONFIRMED (scope: emulator) | Edge-trigger vs level-trigger on hardware | Y | Y (for LA) | Y (before release) | N |
| COM-02 | SRES read-back | LA | Y | MD `lib/main/gate_arr.def.h:38-40`; C `source/bus-main-m68k.c:679-680`; CB `src/main/main.asm:75-77` (polling loop) | as above | Y: ESTIMATED | Delay before read-back changes | Y | Y | Y | N |
| COM-03 | SBRQ request and ack | LA | Y | G `core/mem68k.c:1064-1077`; P `pico/cd/memory.c:183-208`; MD `lib/main/gate_arr.def.h:41-43`; CB `src/main/main.asm:79-81,95-97` | as above | Y: ESTIMATED | Ack latency (emulators make it immediate) | Y | Y | Y | N |
| COM-04 | Power-on register state | LA | Y | G `core/cd_hw/scd.c:1814-1816` (`$0002`/`$0001`); P `pico/cd/mcd.c:76-79` ("cold reset state (tested)") | emulators | Y: two emulators agree, P claims a test. ESTIMATED (OQ-13) | Cold-boot probe on hardware | Y | N | Y | N (BIOS writes known values instead of relying on them) |
| COM-05 | SRES=0 forces SBRQ=1 | LC | partial | G `core/mem68k.c:1079-1086` ("verified on real hardware"); P `pico/cd/memory.c:186-187` (same rule commented out) | emulators | Cond: emulators disagree. UNCONFIRMED | Hardware read-back after SRES=0 | Y | N | Y | N |
| COM-06 | SBRQ ack 0 while Sub STOPped | LC | partial | G `core/mem68k.c:1088-1092` ("verified on real hardware") | single emulator | Cond: single source. ESTIMATED | Independent confirmation | Y | N | Y | N |
| COM-07 | PRG-RAM window only while bus-requested or reset | LA | Y | G `core/mem68k.c:1094-1128`; P `pico/cd/memory.c:1115-1124`; C `source/bus-main-m68k.c:525`; memory-map.md §1 | emulators | Y: CONFIRMED (scope: emulator) | Value read otherwise (open bus vs fault) | Y | Y | Y | N |
| COM-08 | BK0-1 bank select | LA | Y | G `core/mem68k.c:1172-1174`; P `pico/cd/memory.c:215-219,1119`; C `source/bus-main-m68k.c:1177`; MD `lib/main/gate_arr.def.h:106,110,179` | emulators + MD | Y: bits 6-7 agreed by three emulators and MD. ESTIMATED (OQ-14) | Hardware bit check | Y | Y | Y | N |
| COM-09 | WP blocks Sub writes below WP×512 | LA | Y | G `core/cd_hw/scd.c:158-184`; P `pico/cd/memory.c:828-837,1267-1268`; MD `lib/main/gate_arr.def.h:123-124`; CB `src/main/main.asm:83,89` (writes 0, later `$2A`) | emulators + MD + CB | Y: ESTIMATED | Whether Main or CDC-DMA writes are also blocked (emulators: no) | Y | Y | Y | N |
| COM-10 | WP writable only from Main; Sub byte write to `$FF8002` hits mode bits | LC | partial | G `core/cd_hw/scd.c:857-858` (/LDS and /UDS ignored, "verified … mcd-verificator"); P `pico/cd/memory.c:391`; MD `lib/sub/gate_arr.def.h:84-98` | emulators + MD | Cond: ESTIMATED | Whether a Sub word write to the high byte is ignored on hardware | Y | N | Y | N |
| COM-11 | IFL2 raises Sub L2 if IEN2 | LB | Y | G `core/mem68k.c:1149-1164`; P `pico/cd/memory.c:171-182`; C `source/bus-main-m68k.c:1127,1144-1148`; MD `lib/main/gate_arr.def.h:44-46`; S-HW §4-1 p.56 (excluded) | as above | Y: CONFIRMED (scope: emulator), three emulators | none for LB | Y | Y | Y | N |
| COM-12 | IEN2 mirror on Main | LB | Y | G `core/cd_hw/scd.c:1120-1121`; P `pico/cd/memory.c:117-118`; MD `lib/main/gate_arr.def.h:47-48,91` | as above | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-13 | IFL2 read and clear semantics | LC | partial | G `core/cd_hw/scd.c:2379-2384` (cleared on ack; writing 0 ignored at `core/mem68k.c:1149-1164`); P `pico/cd/memory.c:178-181` (writing 0 clears and cancels the IRQ); MD `lib/main/gate_arr.def.h:46` | as above | Cond: emulators **conflict** on writing 0. UNCONFIRMED | Does writing 0 cancel a pending L2 on hardware? | Y | N | Y | N |
| COM-14 | BTST-only on `$A12000`; RMW side effects | LA | partial | MD `lib/main/gate_arr.def.h:50`; CB uses BSET/BCLR on `$A12001`/`$A12000` (`src/main/main.asm:76-96`, `src/main/interrupt.asm:134-135`) | MD (origin unstated), CB | Cond: the safe subset is known (plain byte writes), the hazard is not. UNCONFIRMED | Whether a BSET on `$A12001` disturbs `$A12000` on hardware | Y | N | Y | N (avoid RMW) |
| COM-15 | Register mirroring to `$A120FF` | LC | partial | G `core/mem68k.c:370-371,1048-1049` | single emulator | Cond: CONFIRMED (scope: emulator) only | Hardware decode | Y | N | Y | N |
| COM-16 | `$A12006` H-INT low word | LB | Y | G `core/mem68k.c:553-557,1279-1283`; P `pico/cd/memory.c:129-131,235-242`; C `source/bus-main-m68k.c:692-695,1185-1190`; MD `lib/main/gate_arr.def.h:248-266`; CB `src/main/interrupt.asm:113-119` | as above | Y: ESTIMATED (R-16) | Byte-access behaviour | Y | Y | Y | N |
| COM-17 | H-INT high word at ROM `$70` | LC | partial | G `core/cd_hw/scd.c:1810-1812`; P `pico/cd/mcd.c:80-81`; MD `lib/main/gate_arr.def.h:261-262` | as above | Cond: three sources **conflict** (OQ-1); our ROM picks the value. UNCONFIRMED | Hardware probe (OQ-1) | Y | N | Y | N (our ROM controls `$70`) |
| COM-18 | Stopwatch: 12-bit, 30.72 µs, cleared by Sub | LC | Y | G `core/mem68k.c:559-567`, `core/cd_hw/scd.c:692-697,1443-1452,2005-2012`, `core/cd_hw/scd.h:60,67`; P `pico/cd/memory.c:100-106,444-449`; MD `lib/main/gate_arr.def.h:295-313`, `lib/sub/gate_arr.def.h:239-254`; CB `src/sub/main.asm:40` | as above | Y: ESTIMATED | none for the BIOS (only a clear is needed) | Y | Y | Y | N |
| COM-19 | Stopwatch prescaler phase on clear | LC | partial | P `pico/cd/memory.c:447` (open question in a comment) | single emulator | N: unknown | Whether a clear resets the 384-cycle prescaler | Y | N | Y | N |
| COM-20 | Main flag byte | LA | Y | G `core/mem68k.c:1292-1299`, `core/cd_hw/scd.c:562-570`; P `pico/cd/memory.c:246-249`; C `source/bus-main-m68k.c:1201-1211`; MD `lib/main/gate_arr.def.h:320-331`; CB `src/main/communication.asm:21-28` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-21 | Sub flag byte | LA | Y | G `core/cd_hw/scd.c:1087-1096,1454-1461`, `core/mem68k.c:396-406`; MD `lib/sub/gate_arr.def.h:262-275`; CB `src/sub/main.asm:22-23` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-22 | Byte write to either half updates the writer's own half | LC | partial | G `core/mem68k.c:934-941` ("!LWR is ignored", Space Ace, Dragon's Lair), `core/cd_hw/scd.c:1087-1088` ("verified … mcd-verificator"); P `pico/cd/memory.c:246-248` | emulators | Cond: two emulators agree. ESTIMATED | Hardware confirmation | Y | N | Y | N |
| COM-23 | Command words Main→Sub; Sub writes ignored | LA | Y | G `core/mem68k.c:1301-1309`, `core/cd_hw/scd.c:1151-1156,1576-1581`; P `pico/cd/memory.c:520-524`; C `source/bus-main-m68k.c:713-717`; MD `lib/sub/gate_arr.def.h:278-335` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-24 | Status words Sub→Main; Main writes ignored | LA | Y | G `core/cd_hw/scd.c:1142-1149,1570-1574`, `core/mem68k.c:575-587`; P `pico/cd/memory.c:517-518`; C `source/bus-main-m68k.c:719-723`; MD `lib/sub/gate_arr.def.h:338-391` | as above | Y: CONFIRMED (scope: emulator) | Effect of a Main write on hardware | Y | Y | Y | N |
| COM-25 | Byte access to command and status words | LB | Y | G `core/mem68k.c:409-425,959-964`, `core/cd_hw/scd.c:643-651,1167-1177`; P `pico/cd/memory.c:252-253`; CB `include/mcd_main.inc:46-77` | as above | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-26 | Comm registers cleared on power-on, kept on RES0 | LB | Y | G `core/cd_hw/scd.c:1804-1805,1867-1874` (msu-md-sample observation); P `pico/cd/mcd.c:69,88-105` | emulators | Y: ESTIMATED | Power-on contents on hardware (may be random) | Y | N | Y | N (BIOS clears them anyway) |
| COM-27 | BIOS clears comm registers before IP/SP | LB | partial | CB `src/main/main.asm:61`, `src/main/communication.asm:21-28`, `src/sub/main.asm:22-27` | CB (provenance unstated) | Y: our design choice. Compatibility ESTIMATED | Whether the original leaves non-zero values that software reads (COM-36) | Y | Y | N | N |
| COM-28 | Simultaneous access / tearing | LC | N | Not found in G, P, C, MD, CB (only emulator polling-sync code, e.g. G `core/cd_hw/scd.c:437-509`) | n/a | N: no source | Arbitration on concurrent access | Y (stress test) | N | Y | N (BIOS uses single-writer conventions) |
| COM-29 | Gate-array access wait states | LC | N | Not found in the sources examined. Emulators add ad-hoc delays (P `pico/cd/memory.c:264-270`, "Silpheed") | n/a | N | Cycle-level access cost | Y | N | Y | N |
| COM-30 | Own BIOS boot handshake | LA | Y (design) | Built on COM-20 to COM-24. Reference design: CB `src/main/main.asm:75-102` (no comm handshake; Main jumps to the IP after releasing Sub) | our design | Y: design freedom | none | Y | Y | Y | N |
| COM-31 | Main default V-INT raises IFL2 each frame | LB | Y | CB `src/main/interrupt.asm:21-23,134-135`; MD `docs/main_bios.md:692-698` (RE description of the original); S-HW §3-5 p.30 (excluded) | CB permissive; MD RE | Y: as our design. Compatibility ESTIMATED | Exact point in V-INT (before or after the user handler) | Y | Y | Y | N |
| COM-32 | Sub L2 handler calls usercall2 | LB | Y | CB `src/sub/interrupt.asm:21-29`; MD `lib/sub/sp_header.s:23`, `docs/boot.md:19-26`, `lib/sub/cdrom.macro.s:23`; S-BIOS (excluded) | CB, MD | Cond: register/stack contract (CB clears a5) has one non-excluded source | Preserved or cleared registers, IPL during the call, re-entrancy | Y | Y (LB) | Y (LC) | **Y (LC)**: authoritative contract only in excluded S-BIOS |
| COM-33 | Sub main loop usercall0/1 and return-code contract | LB | partial | CB `src/sub/main.asm:58-85` (init at SR `$2200`, loop on L2-driven VSync, -1 re-inits); CB `src/sub/module.asm:25-93` (header type parsing); MD `docs/boot.md:19-26` | CB, MD | Cond: one implementation plus SDK header | Official return codes, SR and timing | Y | Y (LB) | Y (LC) | **Y (LC)**: same root as COM-32 |
| COM-34 | Main waits for Sub ready before IP | LB | partial | CB `src/main/main.asm:91-102` (does **not** wait); C HLE-loads the IP (`source/clownmdemu.c:496-527`) | CB, emulator | Y: our design (add a flag handshake) | none | Y | Y | Y | N |
| COM-35 | Original Main-BIOS comm-flag semantics | LC | partial | MD `docs/main_bios.md:359-368,680-732` (RE, "not well understood") | MD MIT but **RE-derived** (cf. OQ-7) | N: only an RE source, flagged uncertain by its author | Meaning of Main/Sub flag bits 0, 1, 2 and 6; which games depend on them | Y (black-box) | N | Y | **Y (LC)**: no clean source |
| COM-36 | Comm state expected by games at IP/SP entry and during disc access | LC | N | Not found in G, P, C, MD, CB, or L-VERIF (as reported) | n/a | N | Values and flag bits the original leaves | Y (X-9, needs legal decision) | N | Y | **Y (LC)** |
| COM-37 | Power-on 2M, Main owns | LA | Y | G `core/cd_hw/scd.c:1814-1839`; P `pico/cd/mcd.c:79`; memory-map.md W-01 | emulators | Y: ESTIMATED (W-01's CONFIRMED relies on excluded S-HW) | Hardware probe | Y | Y | Y | N |
| COM-38 | 2M: DMNA=1 gives to Sub, RET→0 | LB | Y | G `core/mem68k.c:1195-1271`; P `pico/cd/memory.c:221-231`; C `source/bus-main-m68k.c:1161-1175`; MD `lib/main/gate_arr.def.h:114-117` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-39 | 2M: Sub RET=1 returns to Main, DMNA clears | LB | Y | G `core/cd_hw/scd.c:1001-1048`; P `pico/cd/memory.c:398-402,420`; C `source/bus-sub-m68k.c:1146-1161`; MD `lib/sub/gate_arr.def.h:93-96` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-40 | 2M: DMNA=0 is a no-op | LC | Y | G `core/mem68k.c:1197`; P `pico/cd/memory.c:222-231` | emulators | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-41 | Non-owner access (Main unmapped; Sub stalls) | LC | partial | G `core/cd_hw/scd.c:80-116,1036-1043`, `core/mem68k.c:1205-1214`; P `pico/cd/memory.c:1131-1136` (Sub "sleeps"); C `source/bus-sub-m68k.c:902-905` (TODO citing S-HW p.24: CPU hangs) | emulators; C cites excluded S-HW | Cond: emulators agree on a stall; hardware UNCONFIRMED (OQ-4) | Hardware behaviour (hang, timeout or bus error) | Y | N | Y | N (BIOS never does it) |
| COM-42 | Switch latency, transient DMNA/RET | LC | partial | P `pico/cd/memory.c:264-270` (24-cycle delay hack, Silpheed) | emulator | N | Real latency | Y | N | Y | N |
| COM-43 | 2M↔1M switch and data re-arrangement | LB | Y | G `core/cd_hw/scd.c:748-808,867-1000`; P `pico/cd/memory.c:404-421`; C `source/bus-sub-m68k.c:1155`; MD `lib/sub/gate_arr.def.h:90-92` | as above | Y: CONFIRMED (scope: emulator); word-alternating interleave per G `scd.c:758-762` | Hardware check of interleave granularity | Y | Y | Y | N |
| COM-44 | 1M: RET selects banks | LB | Y | G `core/cd_hw/scd.c:877-952`; P `pico/cd/memory.c:1179-1195`; C `source/bus-sub-m68k.c:922`; MD `lib/main/gate_arr.def.h:134-136` | as above | Y: agreement (RET=0 → bank 0 to Main). ESTIMATED | none | Y | Y | Y | N |
| COM-45 | 1M swap request by DMNA=0 | LC | Y | G `core/mem68k.c:1185-1193`; P `pico/cd/memory.c:226-228`; C `source/bus-main-m68k.c:1165-1175` (+ L-GD p=16388, "contrary to the official documentation"); MD `lib/main/gate_arr.def.h:118-119` (**worded differently**) | emulators + forum | Cond: three emulators agree; MD wording and (per C) the official docs differ. ESTIMATED | Hardware confirmation | Y | N | Y | N |
| COM-46 | 1M: DMNA=1 remembered for 2M | LC | partial | G `core/mem68k.c:1180-1184`, `core/cd_hw/scd.c:966-998`; P `pico/cd/memory.c:221-225` (`dmna_ret_2m`) | emulators | Cond: the two emulators model it differently. ESTIMATED | Hardware | Y | N | Y | N |
| COM-47 | Owner after 1M→2M | LC | partial | G `core/cd_hw/scd.c:958-999`; P `pico/cd/memory.c:414-421`; C `source/bus-main-m68k.c:1156` (TODO, + L-GD p=15269) | emulators | Cond: UNCONFIRMED (C marks it unknown) | Hardware | Y | N | Y | N |
| COM-48 | Main cell-image view | LC | Y | G `core/cd_hw/scd.c:887-896`, `core/cd_hw/gfx.c:249-300`; P `pico/cd/memory.c:1187-1190`, `pico/cd/cell_map.c` | emulators | Y: ESTIMATED | none (formula in the emulators) | Y | Y | Y | N |
| COM-49 | Sub dot-image view and PM0/PM1 | LC | Y | G `core/cd_hw/scd.c:899-906`, `core/cd_hw/gfx.c:154-248,359-372`; P `pico/cd/memory.c:896-931,1191-1194`; MD `lib/sub/gate_arr.def.h:86,89` | emulators + MD | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-50 | 1M Sub bank at `$0C0000` | LB | Y | G `core/cd_hw/scd.c:908-912`; P `pico/cd/memory.c:1186`; C `source/bus-sub-m68k.c:1115-1123`; CB `include/mcd_sub.inc:23` | as above | Y: ESTIMATED (P maps to `$0EFFFF`, G to `$0DFFFF`) | Extent of the mirror | Y | Y | Y | N |
| COM-51 | Read masks: PM (Main side), BK (Sub side) | LC | Y | G `core/mem68k.c:373-380,533-540`, `core/cd_hw/scd.c:553-560,670-677`; P `pico/cd/memory.c:122,333` | emulators | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-52 | Word RAM mode and owner at IP/SP entry | LB | partial | CB `src/sub/main.asm:32-38` (Sub BIOS sets **1M** and RET=1); G and P power-on is 2M/Main (COM-37); not stated in MD | CB vs emulators | Cond: sources **conflict**. Original behaviour UNCONFIRMED | What the original leaves, and what homebrew SDKs and games assume | Y | N | Y | **Y (LB/LC)**: a wrong state breaks software that does not set the mode itself |
| COM-53 | CDC DMA suspend/resume on ownership or SBRQ change | LC | partial | G `core/mem68k.c:1110-1145,1254-1269`, `core/cd_hw/scd.c:1011-1020` | single emulator | Cond: ESTIMATED | Hardware | Y | N | Y | N |
| COM-54 | Gfx needs 2M, Sub-owned | LC | partial | G `core/cd_hw/gfx.c:604-676` (comment at 676) | single emulator | Cond: ESTIMATED | Behaviour if violated | Y | N | Y | N |
| COM-55 | Main loads Sub BIOS into PRG-RAM before reset release | LA | Y | CB `src/main/main.asm:75-97` | CB permissive | Y: own design, proven in ClownMDEmu | none | Y | Y | Y | N |
| COM-56 | Sub reset vectors from PRG-RAM 0 | LA | Y | CB `src/sub/header.asm:21-22`; G `core/cd_hw/scd.c:1859-1862`; S-M68K §6 (reset exception) | CB, emulator, CPU official | Y: CONFIRMED (derived: S-M68K reset + mapping in memory-map.md §2) | none | Y | Y | Y | N |
| COM-57 | SP at `$6000`, BIOS area protected | LB | Y | MD `docs/boot.md:3`; C `source/clownmdemu.c:498-527`; CB `src/sub/main.asm:58-60`, `src/main/main.asm:89` | MD, CB, emulator | Y: ESTIMATED | The original's WP value (CB uses `$2A`, i.e. up to `$5400`) | Y | Y | Y | N |
| COM-58 | Mode-1 Sub-BIOS detection signature | LC | partial | CB `README.md:20-28` ("SEGA" at offset `$6D` of the Kosinski-compressed Sub BIOS); P `pico/cd/memory.c:1220-1223` (R-20) | CB (provenance unstated) | Cond: single source | Which software scans how; exact format | Y | N | Y | **Y (LC, Mode 1)**: single unverified source |
| COM-59 | LED bits | LC | Y | MD `lib/sub/gate_arr.def.h:21-62`; G `core/cd_hw/scd.c:839-844` | MD, emulator | Y: ESTIMATED | Hardware polarity | Y | N | Y | N |
| COM-60 | RES0 peripheral reset; reads 1 | LA | Y | G `core/cd_hw/scd.c:599-604,846-855,1867-1874`; P `pico/cd/memory.c:330,387-389`, `pico/cd/mcd.c:88-105`; CB `src/sub/main.asm:29`; MD `lib/sub/gate_arr.def.h:31-34` | as above | Y: ESTIMATED; scope of the reset UNCONFIRMED (G TODO at `scd.c:1869`) | What RES0 resets | Y | N | Y | N |
| COM-61 | Version field | LC | partial | MD `lib/sub/gate_arr.def.h:29,41-42,64-71`; P `pico/cd/memory.c:330` ("ver = 0") | MD, emulator | Cond: ESTIMATED | Values per model | Y | N | Y | N |
| COM-62 | Sub register A1-A8 decode/mirror | LC | partial | G `core/cd_hw/scd.c:550-551,667-668` | single emulator | Cond: CONFIRMED (scope: emulator) | Hardware | Y | N | Y | N |
| COM-63 | Sub BIOS sets Word RAM mode at init | LB | partial | CB `src/sub/main.asm:32-38` | CB | Cond: see COM-52 | as COM-52 | Y | N | Y | N (covered by COM-52) |
| COM-64 | Mask `$FF8033` bits 1-6 | LA | Y | G `core/cd_hw/scd.c:1115-1129,1482-1499`; P `pico/cd/memory.c:463-475`; C `source/bus-sub-m68k.c:1224-1233`; MD `lib/sub/gate_arr.def.h:401-419`; CB `src/sub/main.asm:30,56` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-65 | Highest pending level, autovector | LA | Y | G `core/m68k/s68kcpu.c:31-42,207-216`, `core/cd_hw/scd.c:2370-2390`; S-M68K §6.3 (autovectored interrupts) | emulator + CPU official | Y: CONFIRMED (derived from S-M68K priority rules) | Whether the gate array asserts /VPA for every level on hardware | Y | Y | Y | N |
| COM-66 | Pending latch while masked | LC | partial | G: L1/L2/L3/L6 set pending only if enabled (`core/cd_hw/gfx.c:727-735`, `core/mem68k.c:1153`, `core/cd_hw/scd.c:1978-1986`, `core/cd_hw/cdd.c:1771-1778`), L4 always latched (`scd.c:1953-1965`); P raises L4 on unmask (`pico/cd/memory.c:466-471`) | emulators | N: emulators **conflict** and neither cites hardware. UNCONFIRMED | Per-level latch behaviour | Y | N | Y | **Y (LC)**: affects game and BIOS interrupt paths; no reliable source |
| COM-67 | Ack clears pending; L2 ack clears IFL2 | LB | Y | G `core/cd_hw/scd.c:2376-2389`; C `source/bus-sub-m68k.c:387-391` | emulators | Y: CONFIRMED (scope: emulator) | Hardware | Y | Y | Y | N |
| COM-68 | IEN1 off discards pending L1 | LC | partial | G `core/cd_hw/scd.c:1123-1124,1493-1494` ("Batman Returns"); C `source/bus-sub-m68k.c:1232-1233` | emulators | Cond: two emulators agree. ESTIMATED | Hardware | Y | N | Y | N |
| COM-69 | L1 graphics done | LC | Y | G `core/cd_hw/gfx.c:727-735`; C `source/bus-sub-m68k.c:1324-1326`; MD `lib/sub/memmap.def.h:73` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-70 | L2 from Main | LB | Y | see COM-11; MD `lib/sub/memmap.def.h:74`; CB `src/sub/header.asm:50` | as above | Y | none | Y | Y | Y | N |
| COM-71 | L3 timer period | LB | Y | G: period n×384 Sub cycles (`core/cd_hw/scd.c:1098-1113,1463-1480,1968-1988`); P: (n+1)×384, "mcd-verificator results suggest d+1" (`pico/cd/memory.c:453-462`, `pico/cd/mcd.c:207-217`); C: (n+1) (`source/bus-sub-m68k.c:1215-1219`); memory-map.md cites S-HW as (n+1) (excluded) | emulators + L-VERIF hint | Cond: two of three emulators plus a hardware-test hint say (n+1); G differs. ESTIMATED | Hardware period measurement | Y | N | Y | N (BIOS does not depend on it; games may) |
| COM-72 | L4 CDD 75 Hz gated by `$FF8037` bit 2 | LB | Y | G `core/cd_hw/scd.c:1541-1546,1943-1966`; P `pico/cd/memory.c:479-491`, `pico/cd/mcd.c:197-200`; MD `lib/sub/memmap.def.h:76` | as above | Y: CONFIRMED (scope: emulator); rate ESTIMATED | Phase relative to the CDD frame | Y | Y | Y | N |
| COM-73 | L5 CDC /INT falling edge | LB | Y | G `core/cd_hw/cdc.c:306-313`; MD `lib/sub/memmap.def.h:77` | as above | Y: ESTIMATED (CDC details belong to the CD area) | CDC chip interrupt conditions | Y | Y | Y | N |
| COM-74 | L6 subcode | LC | Y | G `core/cd_hw/cdd.c:1771-1778`; MD `lib/sub/memmap.def.h:78` | as above | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-75 | L7, spurious and unused vector safety | LA | Y | S-M68K Table 6-2; CB `src/sub/header.asm:35-55` | CPU official, CB | Y | none | Y | Y | N | N |
| COM-76 | Sub RAM jump table `$5F40-$5FFF` | LB | Y | MD `lib/sub/memmap.def.h:64-95`, `docs/megacd_dev.md:13`; CB `src/sub/header.asm:24-72` (`_LEVELn` symbols) | MD (partly RE), CB | Cond: two non-excluded sources; exact slots ESTIMATED | Official slot list (only in excluded S-BIOS §1-4) | Y | Y (LB with a MegaDev SP) | Y | N (LB: MegaDev defines it; the LC risk is tracked in COM-32) |
| COM-77 | Sub IRQ latency | LC | N | Not found in the sources examined | n/a | N | Cycle timing | Y | N | Y | N |
| COM-78 | VDP V-INT L6, H-INT L4 | LA | Y | S-M68K Table 6-2; G `core/system.c:486,514`; MD `lib/main/memmap.def.h:69-74` | CPU official, emulator, MD | Y: standard Mega Drive (R-14) | none | Y | Y | Y | N |
| COM-79 | Main RAM jump table `$FFFD00` | LB | Y | MD `lib/main/memmap.def.h:69-97`, `docs/megacd_dev.md:7-17,85`; CB `include/mcd_main.inc:83-100` (JMP at `$FFFD06`/`$FFFD0C`/`$FFFD12`; operands at +2 match MD's `$FFFD08`/`$FFFD0E`/`$FFFD14`) | MD (RE), CB | Cond: two sources agree on slots (possibly not independent). ESTIMATED (R-15) | Official statement (none in non-excluded sources) | Y | Y | Y | N (LB) |
| COM-80 | No Sub→Main IRQ; Main L2 = external only | LB | partial | Not found in the sources examined. G Main IRQ call sites are VDP and lightgun only (`core/system.c:486,514,661,839,867,1002`, `core/input_hw/lightgun.c:135`); MD `docs/megacd_dev.md:11` | emulator, MD | Cond: inferred from absence in emulators. UNCONFIRMED (hardware) | Whether the gate array can drive Main /IPL | Y | N | Y | N |
| COM-81 | CPU state at IP entry | LB | partial | CB `src/main/main.asm:99-102` (all registers zeroed, SR `$2700`); MD `docs/megacd_dev.md:21,29,89` (stack, self-inconsistent, OQ-2) | CB, MD | Cond: conflicting or underspecified | SR, SP and VDP state the original leaves | Y | N | Y | N (LB homebrew sets its own state; LC risk via COM-36) |
| COM-82 | Default Main handler side effects games rely on | LC | partial | MD `docs/main_bios.md:224-238,388-416` (RE); CB `src/main/interrupt.asm:21-137` | MD (RE), CB | N: only RE plus one reimplementation | Original handler side effects (flags, counters, IFL2 timing) | Y | N | Y | **Y (LC)**: shares a root with COM-35 |
| COM-83 | 12.5 MHz Sub clock, 384-cycle timer base | LB | Y | G `core/cd_hw/scd.h:60,67`, `core/cd_hw/scd.c:1943`; P `pico/cd/mcd.c:82` (12500000/75); MD `lib/sub/gate_arr.def.h:252` | as above | Y: ESTIMATED | Crystal tolerance (real clocks drift) | Y | N | Y | N |
| COM-84 | Reset-release → first Sub instruction latency | LA | partial | P `pico/cd/memory.c:200-201` (+40 cycles); G immediate (`core/mem68k.c:1059-1062`) | emulators | Cond: ESTIMATED | Real latency (BIOS should poll a flag, not assume a delay) | Y | N | Y | N |
| COM-85 | Polling races | LC | partial | P `pico/cd/memory.c:79-84,264-270`; G `core/mem68k.c:399-400,581-582`, `core/cd_hw/scd.c:732-733` (sync fixes for named games) | emulators | N: emulator workarounds only | Real-hardware timing | Y | N | Y | N (hardware, not BIOS) |
| COM-86 | Gate-array forced reset/init at boot | LA | partial | S-HW §4-1 p.56 (excluded); CB performs none (`src/main/main.asm:21-102`) | excluded / CB | Cond: CB shows it is unnecessary **in ClownMDEmu only**; no non-excluded hardware statement | Whether real hardware needs it (OQ-10) | Y | N | **Y** | **Y (LA on real hardware)**: unknown until measured |
| COM-87 | Gfx unit idle at SP entry | LC | partial | G `core/cd_hw/scd.c:1559-1566`, `core/cd_hw/gfx.c:604-735`; MD `lib/sub/gate_arr.def.h:527-617` | emulator, MD | Y: BIOS never writes `$FF8066` (design) | none | Y | Y | Y | N |
| COM-88 | Font/1bpp registers | LC | Y | G `core/cd_hw/scd.c:606-628`; P `pico/cd/memory.c:310-318,357-368`; CB `include/mcd_sub.inc:120-122` | as above | Y: ESTIMATED (G and P encode it differently; equivalence to be checked) | none for the BIOS | Y | Y | Y | N |
| COM-89 | Stamp, rotation and scaling semantics | LC | Y | G `core/cd_hw/gfx.c:302-735`; C `source/bus-sub-m68k.c:1272-1326` (priority TODO at 1306); MD `lib/sub/gate_arr.def.h:527-617` | as above | Cond: hardware feature, not BIOS. ESTIMATED | Edge cases (C does not implement priority) | Y | N | Y | N (not BIOS) |
## 3. Per-level summary

"Spec defined" = rows whose "Implementable from public material only?" is **Y** or **Cond**. Non-excluded sources then state a concrete, testable behaviour, possibly pending hardware confirmation.

| Level | Items enumerated | Spec defined from non-excluded sources (Y + Cond) | No spec (N) | Blockers |
| --- | --- | --- | --- | --- |
| LA | 23 | 23 (Y 20, Cond 3) | 0 | COM-86 (real hardware only) |
| LB | 28 | 28 (Y 19, Cond 9) | 0 | COM-52; COM-32 and COM-33 block only at LC |
| LC | 38 | 28 (Y 10, Cond 18) | 10 (COM-19, 28, 29, 35, 36, 42, 66, 77, 82, 85) | COM-35, COM-36, COM-58, COM-66, COM-82 (+ COM-32, COM-33, COM-52 from lower levels) |
| **Total** | **89** | **79** | **10** | **9 distinct IDs** |

Reading of the figures: for **LA** and **LB**, every behaviour has a public, non-excluded definition. Much of that is "emulator-agreed", which is not hardware truth, so hardware confirmation (§4) is still owed before release. The only LA risk is real hardware (COM-86). **LC** is where the gaps are. They concentrate on the *original BIOS's* observable conventions (comm-flag protocol, IP/SP entry state, usercall contract, Main handler side effects), not on the gate-array hardware itself.

Blockers (Y in the Blocker column), most severe first:

1. **COM-86** (LA on real hardware): it is unknown whether the gate array needs an initialisation or "forced reset" sequence. The only statement is in excluded S-HW. I-CLOWNBOOT shows only that an emulator does not need it.
2. **COM-52** (LB/LC): Word RAM mode and owner at IP/SP entry. I-CLOWNBOOT leaves 1M mode, while the emulators' power-on state is 2M/Main. The original's choice is not in any non-excluded source.
3. **COM-36** (LC): comm-register contents and flags that commercial games expect at IP/SP entry and during disc access. Not found in any source examined.
4. **COM-35 / COM-82** (LC): the original Main-BIOS comm-flag protocol and default V-INT handler side effects. The only source is RE-derived I-MEGADEV, which itself flags it as uncertain.
5. **COM-32 / COM-33** (LC): the exact Sub-BIOS usercall dispatch contract (registers, SR, return codes, cadence). It is authoritative only in excluded S-BIOS. LB is covered by the MegaDev SP header plus our own design.
6. **COM-66** (LC): per-level latch semantics for masked Sub interrupts. The emulators conflict.
7. **COM-58** (LC, Mode 1): the Mode-1 Sub-BIOS detection signature. The only source is the I-CLOWNBOOT README.

## 4. Feasible legal independent experiments (design only)

All experiments use **our own code** and run from a flash cartridge (Mode 1) or our own CD-R. No Sega code, dumps or commercial software go into the repository or CI. There is no hardware-damage risk: the experiments use only register accesses the system already supports, with no overclocking, no external bus drivers and no voltage changes. Results are recorded as clean-room behaviour notes. Clock-derived constants stay configurable, because real crystals drift.

| Exp | Closes | Design |
| --- | --- | --- |
| X-1 Gate-array cold-state probe | COM-04, 05, 06, 26, 37, 61; OQ-13 | Mode-1 cartridge. The first instructions after power-on copy `$A12000-$A1202F` to Work RAM and display them. Repeat over 20 cold boots per model (Model 1 and 2). Write SRES=0 and re-read SBRQ (COM-05). Load a Sub stub that executes STOP, request the bus, and read the ack (COM-06). |
| X-2 Init necessity | COM-86; OQ-10 | Two builds of our Mode-1 loader: (a) no gate-array init, (b) "write known values" init only. Each loads a Sub stub, releases reset, and checks a comm-flag heartbeat over 1000 cold and warm boots. Compare failure rates. The official sequence is not used. |
| X-3 IFL2 / IEN2 / latch matrix | COM-11, 12, 13, 66, 67, 68 | The Sub stub counts each level's handler entries in the status words. Main toggles IFL2 with the mask on and off, writes IFL2=0 while pending, then unmasks. For L3 and L4, mask during an event window, unmask, and see whether a late interrupt is taken. |
| X-4 Timer period | COM-71, 83, 18, 19 | Sub writes `$FF8031` = 1, 2 and 255. The L3 handler samples the stopwatch and increments a status word. Main times it with the VDP H/V counter over 10 s. Fit to n×T vs (n+1)×T. Record the measured drift. |
| X-5 Word RAM ownership state machine | COM-38 to 47, 51; OQ-4 | Script every write sequence of DMNA, RET and MODE from both sides. Log `$A12003`/`$FF8003` and the stopwatch after each write. For OQ-4, the Sub touches Word RAM while Main owns it. If the Sub's L3 heartbeat stops, Main recovers by resetting the Sub (safe). |
| X-6 Byte-lane and RMW semantics | COM-10, 14, 15, 22, 25, 62 | Byte, word and BSET/BCLR writes to each half of `$A12000`, `$A1200E`, `$FF8002`, `$FF800E` and the comm words. Read back all registers after each write. Probe mirrors at `$A12040-$A120FF` and `$FF8200+`. |
| X-7 PRG-RAM write protect and bank | COM-08, 09; OQ-14 | Main sets WP=k for k ∈ {0, 1, `$2A`, `$FF`}. The Sub writes at k×512 ± 2. Main reads back through BK=0..3. |
| X-8 Latencies | COM-42, 84, 29 | Count cycles from a DMNA write to the RET/DMNA read-back change, and from SRES 0→1 to the Sub's first comm-flag write. Use tight Main polling loops calibrated with S-M68K instruction timings. |
| X-9 Black-box interface observation | COM-36, 52, 81, 35, 82 | **Needs a maintainer/legal decision first (as OQ-7).** In an emulator outside the repository, with a lawfully owned original BIOS and disc, record only register-level observations (comm registers, `$A12003`, SR and SP at IP entry) via emulator event hooks (e.g. E-GPGXF `HOOK_CPU` events at `core/mem68k.c:362,403`). No code inspection or disassembly, and nothing copied into the repository. A separate team writes the spec from the logs. |
| X-10 Mode-1 detection survey | COM-58 | Survey freely licensed Mode-1 homebrew sources (e.g. MSU-MD drivers) for how they locate the Sub BIOS. Build our ROM with and without the signature and test in emulators. |

## 5. Not investigated

- CDC (LC8951-compatible) register semantics, DMA modes and the `$A12004`/`$A12008` host-data protocol beyond interrupt and DMA-halt aspects (CD area).
- CDD command/status protocol and HOCK timing (`$FF8036-$FF804B`) beyond L4 gating (CD area, OQ-11).
- Subcode buffer `$FF8068-$FF817F`, PCM, backup RAM and the CD fader (other areas).
- Other independent emulators: BlastEm (`https://www.retrodev.com/repos/blastem/`, `segacd.c`) and MAME `segacd`. **Not cloned or read**; licences not checked.
- krikzz mcd-verificator binary and source (L-VERIF): not obtained. Its test list is likely the most valuable hardware-derived evidence available.
- SpritesMind forum threads L-GD (p=15269, p=16388) and other gendev posts on DMNA/RET: not fetched.
- I-RETROSIX (login wall) and O-SEGAJP (HTTP 403 again on 2026-10-08): unreadable.
- Official S-HW §3 pp.22-55 and §4 pp.56-60, S-BIOS §1-5, S-SDM: excluded pending Issue #17. They appear to cover COM-01 to COM-29, COM-37 to COM-54, COM-64 to COM-76 and COM-86 (register bit tables, the Word RAM switching procedure, interrupt sources, the forced-reset pattern), plus the usercall contract in S-BIOS. They are recorded as leads for X-1 to X-8 only.
- I-CLOWNBOOT was read only in the files cited. Its Main call table and library (`src/main/call_table.asm`, `src/main/function_table.asm`, `src/main/vdp.asm`) were not audited, for content or for provenance.
- 32X, CDX, Wondermega and LaserActive variants of gate-array behaviour.
- The Main-side `$000280` jump table (OQ-7): outside this area.