# Spec-coverage audit: ROM, CPU startup, memory mapping (Area A, prefix `ROM-`)

**Question.** Is public material enough to implement this area of a Mega-CD-compatible BIOS without the original BIOS?

**Short answer.** For level **LA** (minimal boot): yes. Every LA item has a verifiable specification from non-excluded sources. Most rest only on agreement between emulators and independent SDKs, so they still need hardware confirmation before release. For **LB** (boot a homebrew CD program): yes, with conditions. The Main/Sub system-area layouts and jump tables are public only through SDKs, and those SDKs ultimately derive from the excluded official manual. For **LC** (commercial compatibility), this area has five blockers (see §4).

This audit reuses and re-checks PR #16 (`docs/specifications/*`, base `c2abc36`). It does not repeat it. Evidence labels (CONFIRMED / ESTIMATED / UNCONFIRMED) follow [../README.md](../README.md). Research and documentation only: no BIOS code, no policy change.

## 0. Sources examined (2026-10-08)

| ID | Source | Pinned version | Licence / usage terms | Use in this audit |
| --- | --- | --- | --- | --- |
| M68K | Motorola *M68000 8-/16-/32-Bit Microprocessors User's Manual*, Ninth Edition, <https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf> | HTTP 200, 2,318,145 bytes, SHA-256 prefix `89b690b1923f8a3c` | Proprietary, publicly downloadable. Cite only. | CPU behaviour only. Page numbers are the printed numbers ("6-11"). |
| GPGX-F | `mao2009/Genesis-Plus-GX` (the fork the PR #15 harness pins) | `87dd8b80802ff5217ab2f765202b6b14ecd23f94` (2026-08-21) | Non-commercial licence (`LICENSE.txt`). Not MIT-compatible. **Cite only.** | Every GPGX `path:line` here refers to **this fork**. Line numbers in `scd.c`/`mem68k.c` differ from the upstream numbers in PR #16 (OQ-20). |
| PICO | `notaz/picodrive` | `26ecb2b6358fefba24e3d68b9eb2efba7f10d5ee` (2025-04-02) | Non-commercial (`COPYING`). Cite only. | Same SHA as PR #16; the PR #16 lines re-checked here still match. |
| CLOWN | `mao2009/clownmdemu-core` | `15c6cba32bdaab3320056ff762e159951f85367a` (2026-06-07) | **AGPL-3.0** (`LICENCE.txt`). Not MIT-compatible. Cite only. | New in this audit. HLE-loads the IP/SP and HLE-implements BURAM calls. Embeds the MCDBOOT binary (`source/bus-main-m68k.c:18-21`). One comment cites the excluded hardware manual (`source/clownmdemu.c:105`). |
| MCDBOOT | `Clownacy/clownmdemu-mcd-boot` (found through CLOWN; not on the brief's list) | `ebdf03cda77383bda3d1c9e4d69f89a1d19d7233` (2025-09-07) | **0BSD** ("Copyright (c) 2025 Devon Artmeier and Clownacy"). The licence is MIT-compatible. **Provenance caveat:** symbol names match Sega's official names (`_EXCPT`, `_LEVEL6`, `_CODERR`, `_NOCOD0`, `_USERCALL0`), and the Mode-1 layout facts are given without a stated origin. Nothing copied; facts only. | **Prior art:** an independently written, MIT-compatible, minimal 128 KiB Mega-CD boot ROM. It does not drive the CD drive itself; CLOWN loads the disc (HLE). |
| MEGADEV | `drojaazu/megadev` | `7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef` (2026-05-10) | MIT. Partly reverse-engineered (`docs/main_bios.md:12`). `docs/main_bios.md:56-60` quotes text attributed to official Sega documentation. Facts only. | |
| O-SEGAJP | <https://www.sega.jp/history/hard/mega-cd/> | — | — | **Retried 2026-10-08 with curl and a browser User-Agent: HTTP 403.** The body is a Cloudflare JavaScript challenge (title "Just a moment..."). Content still **not verified**; a human must check it in a browser. |
| I-RHOPE, I-RETROSIX | see [../README.md](../README.md) | — | — | Not re-fetched; PR #16 access notes still apply. |
| **Excluded:** S-HW, S-BIOS, S-SDM, S-FMT | Official manual scans marked CONFIDENTIAL / PROPERTY OF SEGA | — | Issue #17 (still open). | **Not used as a basis for any "implementable" verdict.** Recorded only as leads, in the "Existing material" column as `excl:`. |

Nothing was downloaded from or derived from a Sega BIOS binary, dump or disassembly. The clones live outside the repository, and no code or text from them is reproduced here.

## 1. Required behaviours (enumeration)

Levels: **LA** = minimal BIOS boot (own code runs on both CPUs, hardware in a known state). **LB** = boot a homebrew CD program (IP/SP). **LC** = commercial-game-compatible BIOS. An item is tagged with the lowest level that needs it.

* ROM image and header: ROM-01 – ROM-11
* Main-CPU exception vectors: ROM-20 – ROM-29
* Main-CPU startup: ROM-30 – ROM-38
* Sub-CPU startup and Sub system area: ROM-40 – ROM-51
* Main-CPU memory map and PRG-RAM banking: ROM-60 – ROM-72
* Sub-CPU memory map: ROM-80 – ROM-87
* Backup RAM and RAM cartridge: ROM-90 – ROM-94
* Regions and models: ROM-100 – ROM-103
* 68000 semantics the BIOS relies on: ROM-110 – ROM-124

Full list (ID [level] behaviour). It is the same set as the rows of §2:

1. ROM-01 [LA] Mode 2: the boot ROM occupies Main `$000000-$01FFFF` (128 KiB)
2. ROM-02 [LA] Emit exactly 131072 bytes, every byte defined
3. ROM-03 [LC] Same size and layout across JP/US/EU and all models
4. ROM-04 [LC] Mode 1 (cartridge boot): boot ROM at `$400000-$41FFFF`
5. ROM-05 [LA] BIOS must not rely on anything in `$040000-$1FFFFF` (mirrors)
6. ROM-06 [LA] ROM header starts with `"SEGA"` at `$100`. It is the source of the TMSS write, and Mode-1 software reads it at `$400100`
7. ROM-07 [LA] ROM-type field `"BR"` at `$180` (emulators then treat a side-loaded image as a boot ROM)
8. ROM-08 [LC] 16-byte model string at `$120` selects the GPGX fader model
9. ROM-09 [LA] Boot-ROM header checksum not checked
10. ROM-10 [LC] Mode-1 compatibility: Kosinski-compressed Sub-CPU BIOS at ROM `$16000`, with `"SEGA"` at offset `$6D` of the compressed data, because Mode-1 software finds and unpacks it itself
11. ROM-11 [LC] Main-side "boot ROM library" branch table at ROM `$000280` (soft/hard reset, control panel, controllers, VDP helpers…)
12. ROM-20 [LA] Reset vectors: SSP long at `$000000`, PC long at `$000004`
13. ROM-21 [LA] Initial PC even and inside the ROM window
14. ROM-22 [LA] Initial SSP even and inside Work RAM
15. ROM-23 [LA] After reset S=1, T=0, I=7, and no context is stacked
16. ROM-24 [LA] All vectors 2–63 point to valid handlers (bus/address error, illegal, zero divide, CHK, TRAPV, privilege, trace, line A/F, uninitialised interrupt 15, spurious 24, autovectors 25–31, TRAP 32–47, reserved)
17. ROM-25 [LA] Main interrupt sources: level 2 external port, level 4 H-INT, level 6 V-INT, autovectored
18. ROM-26 [LB] ROM vectors point into a Work-RAM table of 6-byte `JMP abs.l` entries at `$FFFD00`: exception/reset `$FFFD00`, V-INT `$FFFD06`, H-INT `$FFFD0C`, level 2 `$FFFD12`, TRAP #0–15 `$FFFD18-$FFFD72`, CHK `$FFFD78`, address error `$FFFD7E`, zero divide `$FFFD84`, TRAPV `$FFFD8A`, line A `$FFFD90`, line F `$FFFD96`, privilege `$FFFD9C`, trace `$FFFDA2`, cart-BRAM `$FFFDAE`
19. ROM-27 [LC] Address error and illegal instruction share one jump slot (`$FFFD7E`)
20. ROM-28 [LB] Reads of the H-INT vector low word (`$000072`) return gate-array register `$A12006`
21. ROM-29 [LC] H-INT vector high word at `$000070`, and the power-on value of `$A12006`
22. ROM-30 [LA] Main init: `SR=$2700`, SP loaded, interrupts masked until the jump table exists
23. ROM-31 [LA] TMSS: if `$A10001 & $0F` ≠ 0, write `"SEGA"` to `$A14000` before touching the VDP
24. ROM-32 [LA] Tell cold boot from soft reset (I/O control registers non-zero ⇒ soft reset)
25. ROM-33 [LA] Cold boot clears Main Work RAM (power-on contents undefined)
26. ROM-34 [LB] Detect the attached Mega-CD: `$A10001` bit 5 reads 0
27. ROM-35 [LB] Read region and TV standard from `$A10001` bits 7/6
28. ROM-36 [LA] Before IP entry: VDP in a known state, PSG silent, Z80 initialised, controllers initialised
29. ROM-37 [LC] Effect of the 68000 `RESET` instruction on Mega-CD hardware (gate array, Sub CPU)
30. ROM-38 [LC] Mega-CD side of a console soft reset (reset button): what is reset
31. ROM-40 [LA] Power-on: Sub CPU held in reset with its bus requested (`$A12001`: SBRQ=1, SRES=0)
32. ROM-41 [LA] SRES/SBRQ handshake: write, then poll the read-back until it latches. The Sub resets on an SRES 0→1 edge, and SRES=0 forces SBRQ to read 1
33. ROM-42 [LA] Sub reset vectors come from PRG-RAM `$000000/$000004`, so the BIOS writes a Sub vector table and program to PRG-RAM before releasing SRES
34. ROM-43 [LA] Clear PRG-RAM write protection before loading the Sub program; set it again afterwards
35. ROM-44 [LA] Sub hard-reset init: clear status/communication registers, reset peripherals (`$FF8001` bit 0), mask IRQs (`$FF8032`=0), set Word RAM mode, reset the stopwatch, init PCM
36. ROM-45 [LB] Sub system area: `$5E80` common work, `$5EA0` BOOTSTAT, BIOS entries `$5F0A-$5F22`, USERCALL0-3 `$5F28-$5F3A`, SP header `$6000`
37. ROM-46 [LB] Sub exception jump table `$5F40-$5FFF` of 6-byte `JMP` entries (address error `$5F40` … level 1 `$5F76` … level 7 `$5F9A`, TRAPs after)
38. ROM-47 [LB] Sub stack location and size
39. ROM-48 [LB] Sub IRQs enabled before user code (at least level 2 from Main and level 4 CDD)
40. ROM-49 [LC] SR and register state when the BIOS calls USERCALL0 (init) and USERCALL1 (main)
41. ROM-50 [LB] Main V-INT handler raises Sub level 2 (IFL2, `$A12000` byte bit 0) every frame; this drives `_WAITVSYNC` and USERCALL2
42. ROM-51 [LA] Main↔Sub boot handshake through the communication flags/registers (own protocol; registers cleared before IP entry)
43. ROM-60 [LA] PRG-RAM window `$020000-$03FFFF` usable only while SBRQ=1 or SRES=0
44. ROM-61 [LC] Hardware result of a Main access to the PRG-RAM window while the Sub owns it
45. ROM-62 [LA] PRG-RAM bank select: `$A12003` bits 7-6 choose four 128 KiB banks
46. ROM-63 [LA] `$A12002` write protection: protects (value × 512) bytes from `$0`
47. ROM-64 [LB] Power-on Word RAM: 2M mode, owned by Main (RET=1, DMNA=0)
48. ROM-65 [LC] Word RAM mode and owner at IP/SP entry
49. ROM-66 [LA] Main gate-array registers `$A12000-$A1202F` (GPGX mirrors them to `$A120FF`)
50. ROM-67 [LB] Main Work RAM `$FF0000-$FFFFFF`, with `$FFFD00-$FFFFFF` reserved for the system
51. ROM-68 [LB] Main SSP at IP entry: `$FFFD00` or `$FFFC00` (OQ-2)
52. ROM-69 [LB] IP runs at `$FF0000` in supervisor mode; extent of the IP area
53. ROM-70 [LC] Main register state at IP entry
54. ROM-71 [LC] Main BIOS work variables `$FFFDB4-~$FFFE58` (VDP register cache etc.)
55. ROM-72 [LC] Mode 2: cartridge slot / expansion area at `$400000-$7FFFFF`
56. ROM-80 [LA] Sub PRG-RAM `$000000-$07FFFF` (512 KiB)
57. ROM-81 [LB] Sub writes below the write-protect boundary are ignored
58. ROM-82 [LB] Sub Word RAM `$080000-$0BFFFF` (2M) / `$0C0000-$0DFFFF` (1M bank)
59. ROM-83 [LC] Sub access to Main-owned 2M Word RAM: stall or something else (OQ-4)
60. ROM-84 [LB] Backup RAM `$FE0000-$FE3FFF`: 8 KiB on odd addresses
61. ROM-85 [LA] PCM `$FF0000-$FF7FFF` (mirrored) and Sub registers `$FF8000-$FF81FF`
62. ROM-86 [LC] Sub address decoding mirrors every 1 MiB
63. ROM-87 [LA] Boot must not clear or format Backup RAM; PRG-RAM and Word RAM power-on contents are undefined
64. ROM-90 [LC] On-media format of internal Backup RAM (directory, signature, block size) that existing saves use
65. ROM-91 [LB] Detect "BRAM present / unformatted" at boot
66. ROM-92 [LC] RAM cartridge: ID at `$400001` (size code), data at `$600001+` (odd bytes), write enable `$7FFFFF` bit 0
67. ROM-93 [LC] RAM cartridge disabled in Mode 1
68. ROM-94 [LC] Main `$FFFDAE` cartridge-BRAM handler vector
69. ROM-100 [LB] One region-neutral image (region and TV standard read at runtime)
70. ROM-101 [LC] Disc region / security-block check
71. ROM-102 [LC] Model differences visible to the BIOS (fader/filter, front panel, LaserActive)
72. ROM-103 [LC] Region-dependent behaviour software expects from the BIOS
73. ROM-110 [LA] Exception sequence and the 6-byte group 1/2 frame (SR+PC); RTE
74. ROM-111 [LA] Group-0 (bus/address error) long frame; stacked PC unpredictable
75. ROM-112 [LA] Interrupt mask; autovector = `$18` + level; level 7 non-maskable
76. ROM-113 [LA] Uninitialised (15) and spurious (24) interrupt vectors
77. ROM-114 [LB] TRAP #0-15 → vectors 32-47
78. ROM-115 [LA] Illegal, line-A, line-F
79. ROM-116 [LA] Privilege violation, supervisor/user switching, USP initialisation
80. ROM-117 [LC] Trace
81. ROM-118 [LC] Priority of simultaneous exceptions
82. ROM-119 [LA] Double bus fault halts the CPU; only an external reset recovers
83. ROM-120 [LA] Odd-address word/long access → address error
84. ROM-121 [LB] Byte/MOVEP access to 8-bit odd-address devices (BRAM, PCM, RAM cartridge)
85. ROM-122 [LC] `TAS` read-modify-write on the Mega Drive / Mega-CD bus
86. ROM-123 [LC] Exception and instruction timing for timing-sensitive BIOS code
87. ROM-124 [LB] CPU clocks: Sub 12.5 MHz (50 MHz / 4); Main is the Mega Drive clock

## 2. Coverage table

Abbreviations: "Cond" = conditional; "emu" = emulator source (behaviour of that emulator, not hardware truth); "excl:" = lead in excluded CONFIDENTIAL material, not counted.

| ID | Required behavior | Level | Existing material (Y/N/partial) | Exact reference URL + location | Provenance & usage terms | Implementable from public material only? (Y/Cond/N + why) | Specific missing information | Coverable by own test? | Verifiable in emulator only? | Real hardware needed? | Blocker? (Y/N + why) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ROM-01 | Mode 2: the boot ROM occupies Main `$000000-$01FFFF` (128 KiB) | LA | Y. ESTIMATED from public sources (CONFIRMED only with excl: S-HW p.12/16) | GPGX-F `core/cd_hw/scd.h:73`, `core/cd_hw/scd.c:1605-1614`. PICO `pico/pico_int.h:556`, `pico/cd/memory.c:1232-1233`. CLOWN `source/bus-main-m68k.c:508-520`. MCDBOOT `src/main/core.asm:61` (pads to `$20000`). MEGADEV `docs/main_bios.md:30` | emu NC/AGPL cite-only; MCDBOOT 0BSD; MEGADEV MIT | Y: five public sources agree | ROM chip capacity per model (OQ-16) | Y (ROM validator) | Y | N for LA (Y before release) | N |
| ROM-02 | Emit exactly 131072 bytes, every byte defined | LA | Y (PROJECT-RULE) | PR #16 `docs/specifications/rom-layout.md` R-02, `invariants.json` | project rule | Y | — | Y | Y | N | N |
| ROM-03 | Same size and layout across JP/US/EU and all models | LC | partial (ESTIMATED) | GPGX-F `core/loadrom.c:405-420` (one 128 KiB buffer for all three regions) | emu cite-only | Cond: an emulator assumption only | Per-model capacity (Model 1/2, CDX, Wondermega, X'Eye, LaserActive) | N (needs physical evidence) | N | Y (public PCB photos / chip markings, no dumping) | N |
| ROM-04 | Mode 1 (cartridge boot): boot ROM at `$400000-$41FFFF` | LC | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.c:1598-1614`. PICO `pico/cd/memory.c:1226-1233`. MEGADEV `lib/main/memmap.def.h:30-63` (Mode-1 Word RAM `$600000`, PRG window `$420000`) | as above | Cond: emulators and SDK agree; no non-excluded hardware document | Hardware confirmation | Y (Mode-1 probe cartridge, OQ-1) | Y | Y | N |
| ROM-05 | BIOS must not rely on anything in `$040000-$1FFFFF` (mirrors) | LA | partial (UNCONFIRMED: GPGX mirrors every 256 KiB; PICO and CLOWN do not) | GPGX-F `core/cd_hw/scd.c:1613,1626-1645`. PICO `pico/cd/memory.c:1232-1233`. CLOWN `source/bus-main-m68k.c:427-536` | as above | Y as an avoidance rule | Real address decode (OQ-3) | Y | N | Y (to characterise only) | N |
| ROM-06 | ROM header starts with `"SEGA"` at `$100`. It is the source of the TMSS write, and Mode-1 software reads it at `$400100` | LA | partial (ESTIMATED) | MCDBOOT `src/main/main.asm:30-33` (copies the long at ROM `$100` to the TMSS register), `src/main/header.asm:95`. PICO `pico/cd/memory.c:1220-1223` (comment) | as above | Cond: the TMSS mechanism is generic Mega Drive knowledge outside the examined set; the detection use is an emulator comment | Whether TMSS inspects the expansion ROM (OQ-6) | Y | Y (no TMSS model for MCD in GPGX) | Y | N |
| ROM-07 | ROM-type field `"BR"` at `$180` (emulators then treat a side-loaded image as a boot ROM) | LA | Y (CONFIRMED, scope emu) | GPGX-F `core/loadrom.c:48,791-829` (identical to upstream). PICO `pico/media.c:373-381` (`"BOOT"` at `$124`/`$128`). MCDBOOT `src/main/header.asm:99` | as above | Y (developer convenience) | — | Y | Y | N | N |
| ROM-08 | 16-byte model string at `$120` selects the GPGX fader model | LC | Y (scope emu only) | GPGX-F `core/loadrom.c:422-442`, `core/cd_hw/scd.c:1504-1525` | emu | Cond: meaning is emulator-only | Whether any real software reads it | Y | Y | N | N |
| ROM-09 | Boot-ROM header checksum not checked | LA | partial | GPGX-F `core/loadrom.c:279-288`. PICO `pico/media.c:256-381` | emu | Y (scope emu); hardware UNCONFIRMED | Hardware/TMSS check | Y | Y | Y | N |
| ROM-10 | Mode-1 compatibility: Kosinski-compressed Sub-CPU BIOS at ROM `$16000`, with `"SEGA"` at offset `$6D` of the compressed data, because Mode-1 software finds and unpacks it itself | LC | partial (ESTIMATED, single source) | MCDBOOT `README.md` § "Mode 1 Compatibility"; `src/main/core.asm:48-55` | 0BSD; origin of the offsets **undocumented** | Cond: one source with unstated provenance; Kosinski format spec not examined | Detection algorithm used by Mode-1 software; per-region variance; whether a bit-exact compressor is required | Y (public Mode-1 homebrew in an emulator with our ROM) | Y | Y | **Y** for the LC Mode-1 subset: single source, unknown provenance |
| ROM-11 | Main-side "boot ROM library" branch table at ROM `$000280` (soft/hard reset, control panel, controllers, VDP helpers…) | LC | partial (UNCONFIRMED) | MEGADEV `docs/main_bios.md:12,30-44`. MCDBOOT `src/main/function_table.asm:17-102` (a second, 0BSD, implementation of the same table) | MEGADEV states the table is known **from reverse engineering**; MCDBOOT origin unstated | N until OQ-7 is decided. A second public source exists, but it may share the same origin | Clean-room entry list and semantics | Y (clean-room black-box tests with retail titles) | N | Y (or original-BIOS observation under a clean-room protocol) | **Y**: legal/process (OQ-7) |
| ROM-20 | Reset vectors: SSP long at `$000000`, PC long at `$000004` | LA | Y (CONFIRMED) | M68K §6.3.1 p.6-11–6-12; Table 6-2 p.6-7 | vendor manual, cite only | Y | — | Y | Y | N | N |
| ROM-21 | Initial PC even and inside the ROM window | LA | Y (CONFIRMED derived) | M68K §6.3.10 p.6-19; ROM-01 | as above | Y | — | Y (validator) | Y | N | N |
| ROM-22 | Initial SSP even and inside Work RAM | LA | Y (CONFIRMED derived) | M68K §6.2.5 p.6-10, §6.3.10 p.6-19 | as above | Y | — | Y | Y | N | N |
| ROM-23 | After reset S=1, T=0, I=7, and no context is stacked | LA | Y (CONFIRMED) | M68K §6.3.1 p.6-11 | as above | Y | — | Y | Y | N | N |
| ROM-24 | All vectors 2–63 point to valid handlers (bus/address error, illegal, zero divide, CHK, TRAPV, privilege, trace, line A/F, uninitialised interrupt 15, spurious 24, autovectors 25–31, TRAP 32–47, reserved) | LA | Y | M68K Table 6-2 p.6-7, §6.3.3–6.3.4 p.6-13. MCDBOOT `src/main/header.asm:21-89` (complete example) | as above | Y | — | Y (validator: every vector even and inside ROM/RAM) | Y | N | N |
| ROM-25 | Main interrupt sources: level 2 external port, level 4 H-INT, level 6 V-INT, autovectored | LA | partial (CPU part CONFIRMED; level→source ESTIMATED) | M68K p.5-10 (autovector = `$18` + level), §6.3.2 p.6-12. MEGADEV `lib/main/memmap.def.h:69-74`. MCDBOOT `src/main/header.asm:49-55` | as above | Cond: the level→source mapping is generic Mega Drive knowledge from SDKs | — | Y | Y | N | N |
| ROM-26 | ROM vectors point into a Work-RAM table of 6-byte `JMP abs.l` entries at `$FFFD00`: exception/reset `$FFFD00`, V-INT `$FFFD06`, H-INT `$FFFD0C`, level 2 `$FFFD12`, TRAP #0–15 `$FFFD18-$FFFD72`, CHK `$FFFD78`, address error `$FFFD7E`, zero divide `$FFFD84`, TRAPV `$FFFD8A`, line A `$FFFD90`, line F `$FFFD96`, privilege `$FFFD9C`, trace `$FFFDA2`, cart-BRAM `$FFFDAE` | LB | partial (ESTIMATED; two sources agree) | MEGADEV `lib/main/memmap.def.h:68-99` (gives the **operand** address, entry + 2). MCDBOOT `include/mcd_main.inc:83-112` (entry address), `src/main/call_table.asm:21-50` | MEGADEV MIT, partly RE; MCDBOOT 0BSD, provenance caveat | Cond: two public sources agree once the +2 offset is normalised; they may share an origin | Use of `$FFFDA8`; which entries are initialised before IP entry | Y (homebrew IP patches `$FFFD06`) | Y | N | N |
| ROM-27 | Address error and illegal instruction share one jump slot (`$FFFD7E`) | LC | partial (ESTIMATED) | MEGADEV `lib/main/memmap.def.h:92-93`. MCDBOOT `include/mcd_main.inc:104-105` | as above | Cond. **Updates OQ-12:** the MegaDev "duplicate" is corroborated by a second source, so it is probably intentional rather than a typo | Original-BIOS confirmation | Y (clean-room observation) | N | Y | N |
| ROM-28 | Reads of the H-INT vector low word (`$000072`) return gate-array register `$A12006` | LB | partial (ESTIMATED) | GPGX-F `core/mem68k.c:553-556,1279-1281`. PICO `pico/cd/memory.c:129-131,235-242`. CLOWN `source/bus-main-m68k.c:511-516,695,1188-1189`. MEGADEV `lib/main/gate_arr.def.h:261-266` | as above | Cond: four public sources agree; no non-excluded hardware document | Write width (byte vs word) | Y | Y | Y | N |
| ROM-29 | H-INT vector high word at `$000070`, and the power-on value of `$A12006` | LC | N (UNCONFIRMED; sources conflict: GPGX `$FFFF:$FFFF`; PICO `$FF` bytes when no cartridge; MEGADEV `$00FF`; CLOWN low word `$FD0C`) | GPGX-F `core/cd_hw/scd.c:1810-1812`. PICO `pico/cd/mcd.c:80-81`. MEGADEV `lib/main/gate_arr.def.h:261-262`. CLOWN `source/clownmdemu.c:135` | as above | Cond: sidestep by design (ROM holds `$FFFF` at `$70`; BIOS writes `$A12006`=`$FD0C` before IP entry) | Real power-on value | N | N | Y (Mode-1 probe, OQ-1) | N (mitigable) |
| ROM-30 | Main init: `SR=$2700`, SP loaded, interrupts masked until the jump table exists | LA | Y | M68K §6.3.1 p.6-11. MCDBOOT `src/main/main.asm:21-23` | as above | Y | — | Y | Y | N | N |
| ROM-31 | TMSS: if `$A10001 & $0F` ≠ 0, write `"SEGA"` to `$A14000` before touching the VDP | LA | partial | MCDBOOT `src/main/main.asm:30-33` | 0BSD | Cond: generic Mega Drive knowledge (MD documentation not examined); Mega-CD relevance UNCONFIRMED (OQ-6) | Whether expansion boot engages TMSS | Y | Y | Y | N |
| ROM-32 | Tell cold boot from soft reset (I/O control registers non-zero ⇒ soft reset) | LA | partial (ESTIMATED) | MCDBOOT `src/main/main.asm:25-28`. CLOWN `source/clownmdemu.c:79-81` ("standard Sega SDK bootcode") | as above | Cond | I/O control register values after the Mega-CD reset button | Y | Y | Y | N |
| ROM-33 | Cold boot clears Main Work RAM (power-on contents undefined) | LA | Y (design) | MCDBOOT `src/main/main.asm:36-46` (clears only `$FF8000-$FFFFFF`). CLOWN `source/clownmdemu.c:63-67` | as above | Y | How much of the IP area must survive | Y | Y | N | N |
| ROM-34 | Detect the attached Mega-CD: `$A10001` bit 5 reads 0 | LB | partial | CLOWN `source/bus-main-m68k.c:598-600` | AGPL cite-only | Cond: one emulator in the examined set | — | Y | Y | Y | N |
| ROM-35 | Read region and TV standard from `$A10001` bits 7/6 | LB | partial | CLOWN `source/bus-main-m68k.c:600` | as above | Cond | — | Y | Y | N | N |
| ROM-36 | Before IP entry: VDP in a known state, PSG silent, Z80 initialised, controllers initialised | LA | partial | MCDBOOT `src/main/main.asm:52-73` | 0BSD | Cond: generic Mega Drive VDP/Z80 knowledge, outside this area | (VDP/IO area) | Y | Y | N | N |
| ROM-37 | Effect of the 68000 `RESET` instruction on Mega-CD hardware (gate array, Sub CPU) | LC | N | M68K §5.5 p.5-29 (asserts RESET for 124 clocks; CPU itself not reset), §6.3.1 p.6-12 | vendor | N: Mega-CD `/RESET` wiring not in non-excluded sources | What `RESET` resets on Mega-CD | N | N | Y | N (the BIOS need not execute `RESET`) |
| ROM-38 | Mega-CD side of a console soft reset (reset button): what is reset | LC | partial (UNCONFIRMED) | GPGX-F `core/cd_hw/scd.c:1867-1874` (TODO comment; communication registers kept) | emu | Cond | Full list of reset registers | Y (Mode-1 probe + reset button) | N | Y | N |
| ROM-40 | Power-on: Sub CPU held in reset with its bus requested (`$A12001`: SBRQ=1, SRES=0) | LA | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.c:1814-1816,1859-1862`. PICO `pico/cd/mcd.c:76-79` (comment "tested"). CLOWN `source/clownmdemu.c:99-100` | emu | Cond: three emulators agree | Hardware read-back (OQ-13) | Y (Mode-1 probe) | Y | Y | N |
| ROM-41 | SRES/SBRQ handshake: write, then poll the read-back until it latches. The Sub resets on an SRES 0→1 edge, and SRES=0 forces SBRQ to read 1 | LA | partial (ESTIMATED) | GPGX-F `core/mem68k.c:715-756` (comments "verified on real hardware" at :748, :752). PICO `pico/cd/memory.c:186-208` (the "verified" SRES=0 => SBRQ=1 rule at :186-187 is commented out, so PICO does not apply it; cf. COM-05) (corrected during integration review). MCDBOOT `src/main/main.asm:75-97` | as above | Cond | Latch timing | Y | Y | Y | N |
| ROM-42 | Sub reset vectors come from PRG-RAM `$000000/$000004`, so the BIOS writes a Sub vector table and program to PRG-RAM before releasing SRES | LA | Y | M68K §6.3.1 p.6-11. GPGX-F `core/cd_hw/scd.c:1698-1699`. CLOWN `source/bus-sub-m68k.c:709-711`. MCDBOOT `src/main/main.asm:83-93`, `src/sub/header.asm:21-22` | as above | Y: CPU rule plus three consistent maps | — | Y | Y | N | N |
| ROM-43 | Clear PRG-RAM write protection before loading the Sub program; set it again afterwards | LA | partial (emulators disagree) | MCDBOOT `src/main/main.asm:83-89` (WP=0, then `$2A`). CLOWN `source/bus-main-m68k.c:972` (Main writes obey WP). GPGX-F `core/cd_hw/scd.c:160-182,1624-1645` (only Sub writes checked) | as above | Cond: clearing WP first is safe either way | Whether WP applies to Main-CPU writes | Y | Y | Y | N |
| ROM-44 | Sub hard-reset init: clear status/communication registers, reset peripherals (`$FF8001` bit 0), mask IRQs (`$FF8032`=0), set Word RAM mode, reset the stopwatch, init PCM | LA | partial | MCDBOOT `src/sub/main.asm:21-53` | 0BSD | Cond | Which steps are mandatory | Y | Y | N | N |
| ROM-45 | Sub system area: `$5E80` common work, `$5EA0` BOOTSTAT, BIOS entries `$5F0A-$5F22`, USERCALL0-3 `$5F28-$5F3A`, SP header `$6000` | LB | partial (ESTIMATED) | MEGADEV `lib/sub/memmap.def.h:64-95`, `lib/sub/bios.def.h:50-127`. MCDBOOT `include/mcd_sub.inc:213-226`. excl: S-BIOS p.4 | MegaDev says the values come from the official BIOS manual (excluded); MCDBOOT states no origin (corrected during integration review) | Cond: two public SDKs agree; MegaDev attributes them to the excluded manual (Issue #17) and MCDBOOT's origin is unstated (corrected during integration review) | — | Y | Y | N | N |
| ROM-46 | Sub exception jump table `$5F40-$5FFF` of 6-byte `JMP` entries (address error `$5F40` … level 1 `$5F76` … level 7 `$5F9A`, TRAPs after) | LB | partial (ESTIMATED) | MEGADEV `lib/sub/memmap.def.h:64-95`. MCDBOOT `include/mcd_sub.inc:227-242` | as ROM-45 | Cond | — | Y | Y | N | N |
| ROM-47 | Sub stack location and size | LB | partial (conflict) | MCDBOOT `src/sub/variables.inc:23-24` (`$5D80-$5E80`). excl: S-BIOS p.4 (heap/stack `$5C00`) | as above | Cond | Stack depth that SPs expect | Y | Y | N | N |
| ROM-48 | Sub IRQs enabled before user code (at least level 2 from Main and level 4 CDD) | LB | partial | MCDBOOT `src/sub/main.asm:56` | 0BSD | Cond | The original's full enable set | Y | Y | N | N |
| ROM-49 | SR and register state when the BIOS calls USERCALL0 (init) and USERCALL1 (main) | LC | partial (design only) | MCDBOOT `src/sub/main.asm:62-72` (`$2200` during init, `$2000` after; registers zeroed) | 0BSD | Cond: the original state is UNCONFIRMED | Original values | Y (an SP that reports SR via the communication registers) | N | Y | N |
| ROM-50 | Main V-INT handler raises Sub level 2 (IFL2, `$A12000` byte bit 0) every frame; this drives `_WAITVSYNC` and USERCALL2 | LB | partial | MCDBOOT `src/main/interrupt.asm:23,131-135`, `include/mcd_main.inc:36`. GPGX-F `core/mem68k.c:689` | as above | Cond | — | Y | Y | N | N |
| ROM-51 | Main↔Sub boot handshake through the communication flags/registers (own protocol; registers cleared before IP entry) | LA | Y (design) | MCDBOOT `src/main/main.asm:61`, `src/sub/main.asm:21-27` | — | Y: our own design | What the original leaves in the registers (LC) | Y | Y | N | N |
| ROM-60 | PRG-RAM window `$020000-$03FFFF` usable only while SBRQ=1 or SRES=0 | LA | partial (ESTIMATED) | GPGX-F `core/mem68k.c:758-800`. PICO `pico/cd/memory.c:203-206`. CLOWN `source/bus-main-m68k.c:525-531,968-970` | emu | Cond: three emulators agree | — | Y | Y | Y | N |
| ROM-61 | Hardware result of a Main access to the PRG-RAM window while the Sub owns it | LC | N (UNCONFIRMED) | CLOWN `source/bus-main-m68k.c:525-528` (logs, reads 0). GPGX-F `core/mem68k.c:786-792` (unused handlers) | emu | N | Hang, open bus or ignored? | Y | N | Y | N (the BIOS avoids it) |
| ROM-62 | PRG-RAM bank select: `$A12003` bits 7-6 choose four 128 KiB banks | LA | partial (ESTIMATED; official scan cropped, OQ-14) | GPGX-F `core/mem68k.c:826-828`. PICO `pico/cd/memory.c:212-219`. CLOWN `source/bus-main-m68k.c:685,1177` | emu | Cond: three emulators agree | Hardware bit check | Y | Y | Y | N |
| ROM-63 | `$A12002` write protection: protects (value × 512) bytes from `$0` | LA | partial | GPGX-F `core/cd_hw/scd.c:158-182`. CLOWN `source/bus-main-m68k.c:972`. PICO `pico/cd/memory.c:209-211` | emu | Cond | Scope for Main writes (ROM-43) | Y | Y | Y | N |
| ROM-64 | Power-on Word RAM: 2M mode, owned by Main (RET=1, DMNA=0) | LB | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.c:1815-1830`. PICO `pico/cd/mcd.c:79`. CLOWN `source/clownmdemu.c:104-107` (its comment cites excl: hardware manual p.24) | emu | Cond | — | Y | Y | Y | N |
| ROM-65 | Word RAM mode and owner at IP/SP entry | LC | partial (UNCONFIRMED; CLOWN hands it to Sub, MCDBOOT's Sub sets 1M) | CLOWN `source/clownmdemu.c:529-531`. MCDBOOT `src/sub/main.asm:32-38` | as above | Cond | Original state | Y | N | Y | N |
| ROM-66 | Main gate-array registers `$A12000-$A1202F` (GPGX mirrors them to `$A120FF`) | LA | partial | GPGX-F `core/mem68k.c:689-830`. CLOWN `source/bus-main-m68k.c:685-695,1150-1189`. MEGADEV `lib/main/gate_arr.def.h:52-511` | as above | Cond | Mirroring | Y | Y | Y | N |
| ROM-67 | Main Work RAM `$FF0000-$FFFFFF`, with `$FFFD00-$FFFFFF` reserved for the system | LB | partial (ESTIMATED) | MEGADEV `docs/megacd_dev.md:19-31`, `docs/main_bios.md:56-60,116`. MCDBOOT `src/main/variables.inc:42-58` | MEGADEV quotes official text (caveat) | Cond | — | Y | Y | N | N |
| ROM-68 | Main SSP at IP entry: `$FFFD00` or `$FFFC00` (OQ-2) | LB | partial (conflict) | MEGADEV `docs/main_bios.md:56-57` (`$FFFD00`), `docs/megacd_dev.md:21,29` (`$FFFC00`). MCDBOOT `src/main/variables.inc:47-48`, `src/main/main.asm:23` (`$FFFD00`) | as above | Cond: use `$FFFD00` (two of three statements) | Original value | Y | N | Y | N |
| ROM-69 | IP runs at `$FF0000` in supervisor mode; extent of the IP area | LB | partial | CLOWN `source/clownmdemu.c:498-524` (copies 32 KiB; comment "This is what Sega's BIOS does"). MCDBOOT `src/main/main.asm:36-46,102`. MEGADEV `docs/main_bios.md:56` | as above | Cond | Maximum IP size; exact copy behaviour | Y | Y | N | N |
| ROM-70 | Main register state at IP entry | LC | partial | MCDBOOT `src/main/main.asm:99-102` (D0-A6 and USP zeroed) | 0BSD | Cond: design only | Original state | Y | N | Y | N |
| ROM-71 | Main BIOS work variables `$FFFDB4-~$FFFE58` (VDP register cache etc.) | LC | partial (UNCONFIRMED) | MEGADEV `docs/megacd_dev.md:23-27`, `lib/main/bios.def.h:44-146`. MCDBOOT `src/main/variables.inc:49-58` (VDP cache at the same `$FFFDB4`) | RE caveat | N until OQ-7 | Clean-room layout | Y (black-box) | N | Y | **Y**: legal/process (OQ-7) |
| ROM-72 | Mode 2: cartridge slot / expansion area at `$400000-$7FFFFF` | LC | partial | GPGX-F `core/cd_hw/cd_cart.c:246-262`. PICO `pico/cd/memory.c:1242-1248`. CLOWN `source/bus-main-m68k.c:429-468` | emu | Cond | — | Y | Y | Y | N |
| ROM-80 | Sub PRG-RAM `$000000-$07FFFF` (512 KiB) | LA | partial (ESTIMATED; excl: S-HW p.14) | GPGX-F `core/cd_hw/scd.h:74`, `core/cd_hw/scd.c:1689-1699`. CLOWN `source/bus-sub-m68k.c:709` | emu | Cond | — | Y | Y | N | N |
| ROM-81 | Sub writes below the write-protect boundary are ignored | LB | partial | GPGX-F `core/cd_hw/scd.c:158-182` | emu | Cond: one emulator checked | Ignored or faulting? | Y | Y | Y | N |
| ROM-82 | Sub Word RAM `$080000-$0BFFFF` (2M) / `$0C0000-$0DFFFF` (1M bank) | LB | partial | GPGX-F `core/cd_hw/scd.c:1714-1742`. CLOWN `source/bus-sub-m68k.c:256` | emu | Cond | — | Y | Y | N | N |
| ROM-83 | Sub access to Main-owned 2M Word RAM: stall or something else (OQ-4) | LC | N (UNCONFIRMED) | GPGX-F `core/cd_hw/scd.c:1832-1839` (no /DTACK) | emu | N | Hardware behaviour | Y | N | Y | N (the BIOS avoids it) |
| ROM-84 | Backup RAM `$FE0000-$FE3FFF`: 8 KiB on odd addresses | LB | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.h:77`, `core/cd_hw/scd.c:1760-1768`. PICO `pico/cd/memory.c:945-971` | emu | Cond | Word-access behaviour (PICO flags an anomaly at :953, :969) | Y | Y | Y | N |
| ROM-85 | PCM `$FF0000-$FF7FFF` (mirrored) and Sub registers `$FF8000-$FF81FF` | LA | partial | GPGX-F `core/cd_hw/scd.c:530,1771-1779` | emu | Cond | — | Y | Y | N | N |
| ROM-86 | Sub address decoding mirrors every 1 MiB | LC | N (UNCONFIRMED) | GPGX-F `core/cd_hw/scd.c:1684-1699` | emu | Cond (avoid) | Hardware decode (OQ-17) | Y | N | Y | N |
| ROM-87 | Boot must not clear or format Backup RAM; PRG-RAM and Word RAM power-on contents are undefined | LA | partial (design) | GPGX-F `core/cd_hw/scd.c:1791-1795` (emulator clears its buffers; saves loaded separately) | emu | Y (design rule) | — | Y | Y | N | N |
| ROM-90 | On-media format of internal Backup RAM (directory, signature, block size) that existing saves use | LC | N | Not found in the sources examined. CLOWN `source/bus-sub-m68k.c:695,715` has only a block-size macro and an HLE comment ("None of this … is accurate"). MEGADEV `lib/sub/bram.def.h` has function codes only | — | N | Full on-media format | Y (clean-room: format and save with the original BIOS on one's own unit, read back the data) | N | Y | **Y** (LC save interoperability) |
| ROM-91 | Detect "BRAM present / unformatted" at boot | LB | N | Not found in the sources examined | — | Cond: an own format is enough for LB | Original detection rule (LC) | Y | Y | N | N |
| ROM-92 | RAM cartridge: ID at `$400001` (size code), data at `$600001+` (odd bytes), write enable `$7FFFFF` bit 0 | LC | partial | GPGX-F `core/cd_hw/cd_cart.c:42-173,196-244`. PICO `pico/cd/memory.c:672-727` | emu | Cond: both fit size = 8 KiB << ID (GPGX ID 6 = 512 KiB, `cd_cart.c:205`; PICO ID 3 = 64 KiB, `memory.c:680`) | Official size-code semantics; cartridge format | Y | Y | Y | N |
| ROM-93 | RAM cartridge disabled in Mode 1 | LC | partial (emu) | GPGX-F `core/cd_hw/cd_cart.c:184-188` | emu | Cond | — | Y | Y | Y | N |
| ROM-94 | Main `$FFFDAE` cartridge-BRAM handler vector | LC | partial | MEGADEV `lib/main/bramcart.def.h:11`. MCDBOOT `include/mcd_main.inc:112` | RE caveat | Cond | Semantics and function codes | Y | N | Y | N |
| ROM-100 | One region-neutral image (region and TV standard read at runtime) | LB | Y (design) | CLOWN `source/bus-main-m68k.c:600`. MCDBOOT `src/main/header.asm:107` (`"JUE"`) | — | Y | — | Y | Y | N | N |
| ROM-101 | Disc region / security-block check | LC | partial | PR #16 R-31 / OQ-8 (I-RHOPE only). CLOWN `source/clownmdemu.c:511` (region byte read, commented out) | single independent source | N (legal) | Policy | Y (own discs) | N | Y | **Y**: legal (OQ-8) |
| ROM-102 | Model differences visible to the BIOS (fader/filter, front panel, LaserActive) | LC | partial | GPGX-F `core/cd_hw/scd.h:53-57`, `core/cd_hw/scd.c:1504-1525`. O-SEGAJP HTTP 403 | emu | Cond | Official model list | N | N | Y | N |
| ROM-103 | Region-dependent behaviour software expects from the BIOS | LC | N | Not found in the sources examined | — | N | Everything | N | N | Y | N |
| ROM-110 | Exception sequence and the 6-byte group 1/2 frame (SR+PC); RTE | LA | Y (CONFIRMED) | M68K §6.2.5 p.6-10 | vendor | Y | — | Y | Y | N | N |
| ROM-111 | Group-0 (bus/address error) long frame; stacked PC unpredictable | LA | Y | M68K §6.2.5 p.6-10, §6.3.9–6.3.10 p.6-16–6-19 | vendor | Y | — | Y | Y | N | N |
| ROM-112 | Interrupt mask; autovector = `$18` + level; level 7 non-maskable | LA | Y | M68K p.5-10, §6.3.2 p.6-12 | vendor | Y | — | Y | Y | N | N |
| ROM-113 | Uninitialised (15) and spurious (24) interrupt vectors | LA | Y | M68K §6.3.3–6.3.4 p.6-13 | vendor | Y | — | Y | Y | N | N |
| ROM-114 | TRAP #0-15 → vectors 32-47 | LB | Y | M68K §6.3.5 p.6-13 | vendor | Y | — | Y | Y | N | N |
| ROM-115 | Illegal, line-A, line-F | LA | Y | M68K §6.3.6 p.6-14 | vendor | Y | — | Y | Y | N | N |
| ROM-116 | Privilege violation, supervisor/user switching, USP initialisation | LA | Y | M68K §6.1.3 p.6-2, §6.3.7 p.6-15 | vendor | Y | — | Y | Y | N | N |
| ROM-117 | Trace | LC | Y | M68K §6.3.8 p.6-15 | vendor | Y | — | Y | Y | N | N |
| ROM-118 | Priority of simultaneous exceptions | LC | Y | M68K §6.2.3 p.6-8 | vendor | Y | — | Y | Y | N | N |
| ROM-119 | Double bus fault halts the CPU; only an external reset recovers | LA | Y | M68K §5.4.4 p.5-28 | vendor | Y | — | Y | Y | N | N |
| ROM-120 | Odd-address word/long access → address error | LA | Y | M68K §6.3.10 p.6-19 | vendor | Y | — | Y | Y | N | N |
| ROM-121 | Byte/MOVEP access to 8-bit odd-address devices (BRAM, PCM, RAM cartridge) | LB | Y | M68K p.2-13 (MOVEP), p.6-19 (MOVEP fault note) | vendor | Y | — | Y | Y | N | N |
| ROM-122 | `TAS` read-modify-write on the Mega Drive / Mega-CD bus | LC | partial | M68K §4.1.3 p.4-5 (indivisible RMW cycle). System-specific write-back behaviour: not found in the sources examined | vendor | Cond: the BIOS can avoid `TAS` | Whether gate-array registers and Word RAM honour the RMW write | Y (hardware probe) | N | Y | N |
| ROM-123 | Exception and instruction timing for timing-sensitive BIOS code | LC | Y | M68K Section 8 (MC68000 execution times; exception table p.8-10 per the TOC) | vendor | Y | Bus wait states on Mega-CD (not in M68K) | Y | Y | Y | N |
| ROM-124 | CPU clocks: Sub 12.5 MHz (50 MHz / 4); Main is the Mega Drive clock | LB | partial | GPGX-F `core/cd_hw/scd.h:60` (`SCD_CLOCK` 50 MHz). PICO `pico/cd/mcd.c:82` (12,500,000) | emu | Cond | Exact hardware tolerances | Y | Y | Y | N |

## 3. Per-level summary

**Counting rule (applied mechanically to the table).** An item has a *verifiable spec from non-excluded sources* when two things hold. First, the "Implementable" column is **Y** or **Cond**. Second, the "Existing material" column is not **N** and does not record an unresolved conflict (UNCONFIRMED / conflict / emulators disagree). Values that rest only on emulator or SDK agreement count, but they still need hardware confirmation before release.

| Level | Items enumerated | Implementable Y / Cond / N | With a verifiable spec from non-excluded sources | Without one | Blockers |
| --- | --- | --- | --- | --- | --- |
| LA | 38 | 23 / 15 / 0 | 36 | ROM-05, ROM-43 (sources conflict, but both are fully specified as avoidance rules: never use mirrors; always clear WP before loading. Counting those two gives 38/38.) | none |
| LB | 21 | 3 / 18 / 0 | 18 | ROM-47 (Sub stack conflict), ROM-68 (Main SSP conflict, OQ-2), ROM-91 (BRAM detection; an own design is enough for LB) | none |
| LC | 28 | 3 / 17 / 8 | 16 | ROM-11, -29, -37, -38, -61, -65, -71, -83, -86, -90, -101, -103 | ROM-10, ROM-11, ROM-71, ROM-90, ROM-101 |
| **Total** | **87** | 29 / 50 / 8 | **70** | 17 | **5** |

Notes:

* **LA:** 15 of the 38 items are only *Cond*: they rest on emulator or SDK agreement and need the E-1/E-2 probes before release. Nothing blocks LA in this area.
* **LB:** depends on SDK tables (ROM-26, ROM-45, ROM-46) that MegaDev traces back to the excluded official manual (MCDBOOT states no origin; corrected during integration review). If the Issue #17 decision treats such derived facts as tainted, these items must be re-derived clean-room, using E-5-style observation or our own definition plus homebrew-SDK agreement.
* **Prior art.** MCDBOOT (0BSD) is a working minimal boot ROM for this exact purpose, which shows LA is achievable in an emulator. It does **not** prove LB on hardware, because its host emulator (CLOWN) loads the IP/SP itself (`source/clownmdemu.c:494-531`) instead of the BIOS driving the CD hardware. MCDBOOT can be studied for facts, but **must not be copied** without a separate provenance decision: its licence is fine, the origin of its interface knowledge is not.

## 4. Top blockers (LC)

1. **ROM-90:** on-media format of the internal Backup RAM. Not found in any examined source. Without it, users' existing saves are unreadable.
2. **ROM-11:** Main-side `$000280` branch table. Its sources are reverse-engineered (MEGADEV) or of unstated origin (MCDBOOT). Needs the OQ-7 clean-room decision.
3. **ROM-71:** Main BIOS work variables at `$FFFDB4+`. Same provenance problem as ROM-11 (OQ-7).
4. **ROM-101:** disc region / security check. Needs a legal decision (OQ-8).
5. **ROM-10:** Mode-1 Sub-BIOS location and format (`$16000`, Kosinski, `"SEGA"` at `$6D`). One source, provenance unstated.

## 5. Feasible independent experiments (design only)

All experiments use only our own code and our own media. No Sega code enters the repository or CI, and observations are recorded as clean-room behaviour notes. They only read and write documented registers and RAM within specification, never modify the console, and involve no commercial software distribution.

| Exp | Closes | Design |
| --- | --- | --- |
| E-1 Mode-1 probe cartridge (already proposed in OQ-1) | ROM-04, -09, -29, -38, -40, -41, -43, -60, -61, -62, -63, -64, -66 | Our own Mega Drive cartridge program, run from a flash cartridge with a stock Mega-CD attached. Its first instructions read `$A12000-$A1200F` (power-on values). It then toggles SRES/SBRQ and logs the latch timing, writes each bit of `$A12002/3` and checks the PRG-RAM window, tests whether WP blocks Main writes, and reads `$400070-$400073` while varying `$A12006`. Results go to the screen or to SRAM. |
| E-2 Sub-side probe (loaded by E-1) | ROM-81, -83, -84, -86, -122 | A small Sub program that E-1 places in PRG-RAM. It reads PRG-RAM at `+$100000`, writes below WP, touches Main-owned Word RAM with a timer-IRQ watchdog, does word accesses to BRAM, and runs `TAS` on a communication flag. Results come back through the communication registers. |
| E-3 Mode-1 compatibility run | ROM-10 | Run public open-source Mode-1 software (for example MSU-MD drivers) in emulators with our ROM, once with a Sub image at `$16000` and once without. Log which ROM bytes the software reads. This shows the dependency without any Sega ROM. |
| E-4 BRAM format observation (clean-room, own unit) | ROM-90, -91, -92 | On one's own console with its installed original BIOS, our own homebrew SP formats BRAM and saves files with known names and contents through BURAM calls. Our probe reads the 8 KiB back, and the structure is described in a behaviour note. No ROM bytes are read. Repeat for the RAM cartridge. |
| E-5 IP-entry state recorder | ROM-27, -49, -65, -68, -69, -70 | Our own homebrew disc, run under the original BIOS on one's own unit. Its IP and SP report SR, SP, registers, Word RAM mode and the `$FFFD00` table contents via the communication registers or the screen. It then triggers an illegal instruction and an address error and records which jump slot runs. Clean-room notes only. |
| E-6 PCB evidence survey | ROM-03, -102 | Collect public PCB photos for each model and record ROM chip markings and capacity. No dumping. |
| E-7 Emulator three-way diff | ROM-05, -28, -29, -43, -92 | Run our own probe ROM under GPGX-F, PICO and CLOWN, and tabulate every divergence as a harness test case. |

## 6. Not investigated

* **Excluded CONFIDENTIAL material** (Issue #17), not read in this audit. Leads only: S-HW §1-1–1-3 pp.12–17 (maps, Mode 1/2), §3 pp.22–30 (Sub registers, reset, interrupts), §4-1 pp.56–57 (Main registers, forced-reset sequence); S-BIOS §1-4 p.4 (Sub system map), §4 pp.30–32 (boot flow), §5 pp.33–34 (user calls); S-SDM and S-FMT (never reviewed). MEGADEV `docs/main_bios.md:56-60` and CLOWN `source/clownmdemu.c:105` appear to draw on these.
* Generic Mega Drive references (TMSS, the `$A10001` version register, VDP init, Z80 bus): Sega Retro, Plutiedev, Charles MacDonald's `genhw.txt`, the SpritesMind forum. ROM-31, -34, -35 and -36 rely on emulator/SDK statements instead.
* Kosinski compression format documentation (needed for ROM-10).
* Upstream `ekeeke/Genesis-Plus-GX` was not re-cloned; this file cites the fork `87dd8b8` only.
* MCDBOOT `src/main/vdp.asm`, `decompress.asm`, `object.asm`, `splash.asm`, `control_panel.asm` and `src/sub/module.asm` were not read in detail.
* Other emulators: MAME `segacd`, Kega Fusion (closed source), BlastEm, Exodus.
* LaserActive PAC-S/PAC-N, Wondermega and X'Eye specifics; Mega-CD + 32X interactions.
* O-SEGAJP content (HTTP 403 again on 2026-10-08) and I-RETROSIX (login wall).
* Patent filings and public regulatory (FCC) documents for the Mega-CD / Sega CD.
