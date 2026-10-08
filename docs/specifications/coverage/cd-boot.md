# Coverage audit: CDC / CDD, disc format and boot sequence (prefix CD-)

Audit-Agent D, branch `audit/d-cd-boot`, based on `origin/agent-a/issue-1-rom-layout` @ `c2abc36`. Research and documentation only. No BIOS code, no policy change.

**Question.** Does public or independent material let us implement the CD-drive, CD-data and disc-boot part of a Mega-CD-compatible BIOS without the original BIOS?

**Short answer.**

* **LA (minimal boot).** Yes, but only against an emulator model. The CDD and CDC register protocols are specified in emulator source (Genesis Plus GX, with PicoDrive derived from it, and BlastEm independently) and in MegaDev. No non-excluded source describes real-hardware timing.
* **LB (homebrew CD program).** Conditionally yes. The disc-layout and SP-header conventions come from MegaDev (MIT, partly reverse-engineered). The `_CDBIOS` function codes and calling conventions that homebrew uses exist only in MegaDev. MegaDev itself appears to derive them from the official BIOS manual or from reverse engineering, so issue #17 and OQ-7 decide whether they are usable.
* **LC (commercial compatibility).** No. The region and security handling, the exact `_CDBIOS`/`_CDBOOT` behaviour, the CPU state at IP entry, and the drive timing that games depend on have no non-excluded specification.

## 0. Conventions and source register

Labels: **CONFIRMED**, **ESTIMATED** and **UNCONFIRMED**, as defined in [../README.md](../README.md). Emulator behaviour is a model, not hardware truth. "Spec defined" in §3 means a concrete, testable expected behaviour can be written from **non-excluded** sources (scope may be emulator-only).

| Key | Source | Pinned version | Class | Provenance / usage terms |
| --- | --- | --- | --- | --- |
| GX | Genesis Plus GX fork <https://github.com/mao2009/Genesis-Plus-GX> | `87dd8b80802ff5217ab2f765202b6b14ecd23f94` (2026-08-21). **All GX line numbers in this file refer to this fork** (the harness pin from PR #15), not to the upstream `49c5847` used in `../*.md` (see OQ-20). | emulator | Non-commercial licence (file headers). Cite only, never copy. |
| PD | PicoDrive <https://github.com/notaz/picodrive> | `26ecb2b6358fefba24e3d68b9eb2efba7f10d5ee` | emulator | Non-commercial (`COPYING`). `pico/cd/cd_parse.c` states the MAME licence. **`pico/cd/cdd.c:1-12` and `pico/cd/cdc.c:1-12` credit Genesis Plus (Eke-Eke): PD's CDD/CDC model is derived from GX, so it is not independent evidence.** |
| CL | clownmdemu-core <https://github.com/mao2009/clownmdemu-core> | `15c6cba32bdaab3320056ff762e159951f85367a` | emulator | AGPL-3.0 (`LICENCE.txt`). Cite only. Independent of GX, but **high-level**: see CD-090. |
| BE | BlastEm `cdd_mcu.h`, <https://www.retrodev.com/repos/blastem/file/07ed42bd7b4c/cdd_mcu.h> | hg rev `07ed42bd7b4c` | emulator (independent of GX; LLE model of the CDD MCU) | Licence **not verified in this pass**, and the file shows no header. Read only through WebFetch (enum names). Cite only. |
| MD | MegaDev <https://github.com/drojaazu/megadev> | `7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef` | independent SDK | MIT. Partly reverse-engineered: function codes and layouts appear to come from the official manuals or from RE (OQ-7, #17). **Exception:** `lib/security.c` (274 lines) embeds per-region byte arrays that MegaDev labels as the Mega CD "security block". These appear to be Sega-authored code that the MIT grant cannot cover. **Excluded. Never use it in fixtures. Do not inspect it further.** |
| EC130 | ECMA-130 2nd ed. (June 1996), CD-ROM ("Yellow Book") <https://www.ecma-international.org/wp-content/uploads/ECMA-130_2nd_edition_june_1996.pdf> | 2nd ed. | public standard | Free download. Cite only. ISO/IEC 10149 equivalent. Clause and page numbers are not yet recorded (see §5). |
| EC119 | ECMA-119 (ISO 9660 file system) <https://ecma-international.org/publications-and-standards/standards/ecma-119/> | not pinned in this pass | public standard | Free download. Cite only. |
| LCDM | "LC8950 / LC8951 Design Manual" (scan), <https://www.mirrorservice.org/sites/www.bitsavers.org/pdf/sony/cdrom/CDU535-88_SLCD/LC8950_LC8951_Design_Manual.pdf> | undated scan (PDF metadata 2021-05-13) | vendor datasheet (third-party mirror) | **Provenance unverified.** An automated fetch extracted no confidentiality marking, but the text layer was not readable, so a human must check the pages. Sanyo copyright presumed. Cite only. |
| MR | MiSTer MegaCD core `docs/` <https://github.com/MiSTer-devel/MegaCD_MiSTer/tree/a3a3da81d04b22533def34f26eb9d748be9d2d0c/docs> | `a3a3da8` | mixed | Repo GPL-3.0. `docs/mcd logs/*.PNG` look like third-party logic-analyser captures of real hardware (CDC DMA, register writes). **Not opened**: lead only. The same folder hosts Sega manual PDFs and a Sega-marked LC8950/8951 copy. Those are **excluded** (see XS). |
| XS | **Excluded** (CONFIDENTIAL / PROPERTY OF SEGA, issue #17): S-HW, S-BIOS, S-SDM, S-FMT (`../README.md` register); `https://segaretro.org/images/5/55/Sanyo_LC8950_%26_LC8951.pdf` (search summary reports a Sega confidential marking); the Sega PDFs in MR `docs/` | - | official (excluded) | Existence recorded only. Not an independent basis. Their table-of-contents entries are listed as **leads** (from <https://www.megadrive.org/elbarto/megacd/Official%20Sega%20CD%20Manual/segacd_toc.html>, TOC only): S-HW §3-2 CDC pp.26–27, §3-6 CDD pp.31–33, §4-2 CDC (Main) pp.58–59; S-BIOS §3-M CD-DA pp.13–17, §3-R CD-ROM pp.18–19, §4 bootstrap pp.30–32, §6 CD-Boot pp.36–37; S-SDM CDC pp.12–13/34, CDD pp.16–17, Subcodes p.32; S-FMT physical/logical format pp.2–15, System ID pp.18–19, Disc ID pp.20–21. |
| SEGAJP | <https://www.sega.jp/history/hard/mega-cd/> | - | official corporate | **Retried 2026-10-08 with curl and a browser UA: HTTP 403** (unchanged from `../README.md`). Not used. |
## 1. Enumerated required behaviours

The level is the **minimum** level that needs the behaviour. LA = minimal BIOS boot. LB = boot a homebrew CD program. LC = commercial-game-compatible BIOS.

**A. Disc image and test fixtures**
- CD-001 Cooked ISO (2048 B/sector) fixture recognised by the harness emulators: **LB**
- CD-002 Raw BIN (2352 B/sector, Mode 1) plus CUE fixture: **LB**
- CD-003 Mixed-mode CUE (data track 1, audio tracks 2+, 2 s pregaps): **LC**
- CD-004 Correct sync, header and EDC/ECC in raw sectors (needed for real CD-R): **LB**
- CD-005 Data track at least 150 sectors long: **LB**
- CD-006 Subcode side file (`.sub`, 96 B/sector) for subcode and CD+G tests: **LC**
- CD-007 Physical CD-R of a fixture that the stock drive reads: **LB**
- CD-008 Audio-only disc (no data track) handled without hang: **LA**
- CD-009 Negative fixtures (bad ID, short boot area, oversize IP/SP, zero SP): **LB**
- CD-010 ISO 9660 file system in the data track (application-level, PVD at LBA 16): **LB**
- CD-011 LBA↔MSF mapping (LBA 0 = 00:02:00, BCD MSF) in CDD and CDC: **LA**

**B. Disc system area (sector 0) and headers**
- CD-020 Recognise the 16-byte system ID at offset 0 and know which IDs are bootable: **LB**
- CD-021 Volume/system name and version fields `$10-$2F`: **LC**
- CD-022 IP offset/size fields (`$30/$34`) drive the IP load: **LB**
- CD-023 SP offset/size fields (`$40/$44`) drive the SP load to `$6000`: **LB**
- CD-024 IP/SP entry and work-RAM fields (`$38/$3C/$48/$4C`): **LC**
- CD-025 Disc header `$100-$1FF` (hardware ID, titles, serial, region string at `$1F0`): is any of it checked? **LC**
- CD-026 Extent of the boot area that the BIOS reads (sectors 0..n): **LB**
- CD-027 IP size limit and the "IP crosses into sector 1" quirk: **LC**
- CD-028 SP header format (module header plus usercall0-3 offset table): **LB**
- CD-029 Disc-type classification (no disc / music / CD-ROM / mixed / system / data / boot / game): **LC**

**C. CDD command/status protocol**
- CD-030 Enable CDD communication (HOCK, `$FF8036` bit 2). INT4 per CDD frame (75 Hz model): **LA**
- CD-031 Status frame: 10 nibbles `$FF8038-$FF8041` (RS0 status, RS1 report type, RS2-8 data, RS9 checksum): **LA**
- CD-032 Command frame: 10 nibbles `$FF8042-$FF804B`, sent by writing `$FF804A`: **LA**
- CD-033 Checksum algorithm, plus the drive's reaction to a bad command checksum: **LA** (algorithm)
- CD-034 Status code set (stop, play, seek, scan, pause, open, errors, TOC-read, tracking, no-disc, lead-out, lead-in, tray moving): **LA**
- CD-035 Command code set (status, stop, report, play/read, seek, pause, resume, FF, REW, track jump, track cue, close, open): **LA**
- CD-036 Report sub-codes (abs time, rel time, track no., disc length, first/last track, track start plus data flag, error info): **LA**
- CD-037 Command→status latency, seek duration, frames until data flows: **LB**
- CD-038 RS1 = `$F` ("not valid yet") during seek: the BIOS must wait: **LB**
- CD-039 Drive state after power-on and the minimal bring-up sequence: **LA**
- CD-040 Physical HOCK/CDCK nibble link: does BIOS software have to pace accesses? **LA**
- CD-041 `$FF8036` read-only status bits (e.g. "audio not playing"): **LC**
- CD-042 Track-jump command (`$A`) parameters and semantics: **LC**
- CD-043 Undefined or rarely used command codes (`$5`, `$B`, `$E`, `$F`) and their responses: **LC**

**D. Drive, tray and LED states**
- CD-050 Tray open/close (motorised tray, Model 1 type) and the open/moving statuses: **LC**
- CD-051 Top-loader lid (Model 2 type) open detection: **LC**
- CD-052 Disc insertion → automatic TOC read: **LA**
- CD-053 No-disc detection: **LA**
- CD-054 Disc change while running → re-read TOC and invalidate state: **LC**
- CD-055 Pause→standby spin-down timer: **LC**
- CD-056 End-of-disc / lead-out status handling: **LC**
- CD-057 Front-panel LEDs (`$FF8000` LEDR/LEDG) and the LED modes the BIOS offers: **LC**

**E. CDC (LC8951-compatible) registers and transfers**
- CD-060 Chip identity, register-file access through `$FF8004` (address) and `$FF8006` (data), auto-increment: **LB**
- CD-061 CDC reset and initialisation sequence: **LB**
- CD-062 Decoder enable and mode (Mode 1 / Mode 2 / CD-DA pass-through): **LB**
- CD-063 Buffer write (WRRQ), WA/PT pointers, 16 KiB ring buffer: **LB**
- CD-064 HEAD0-3 header registers used to confirm the delivered sector: **LB**
- CD-065 STAT0-3 error and validity flags: **LB**
- CD-066 Decoder interrupt (DECI → Sub level 5) and its acknowledgement: **LB**
- CD-067 Data transfer: DBC, DAC, DTRG, DTACK, DTEI, DTBSY/DTEN: **LB**
- CD-068 Sub-CPU host read through `$FF8008` with DSR/EDT flags: **LB**
- CD-069 Main-CPU host read through `$A12004/$A12008`: **LC**
- CD-070 DMA to PRG-RAM (address unit, halt while Main holds PRG-RAM): **LB**
- CD-071 DMA to Word RAM (2M and 1M banks, halt while Main owns it): **LC**
- CD-072 DMA to PCM wave RAM: **LC**
- CD-073 A write to `$FF8004` resets the DMA address and re-latches the destination: **LB**
- CD-074 DMA and host transfer throughput and timing: **LC**
- CD-075 LC89513K variant (wider register address) on CDX / Wondermega M2 type units: **LC**
- CD-076 Mode 2 (CD-ROM XA) sub-header handling: **LC**
- CD-077 Ring-buffer overrun behaviour when software is slow: **LC**

**F. BIOS CD service interface (`_CDBIOS`, `_CDBOOT`)**
- CD-080 Data-read services (ROMREAD/ROMREADN/ROMREADE/ROMSEEK, CDCSTART/STOP/STAT/READ/TRN/ACK): **LB**
- CD-081 CDBSTAT and the BIOS status block at `$5E80`: **LB**
- CD-082 CDBCHK, CDBTOCREAD, CDBTOCWRITE: **LC**
- CD-083 CD-DA services (MSCPLAY, PLAY1, PLAYR, PLAYT, SEEK, SEEKT, SEEK1, STOP, PAUSEON/OFF, SCANFF/FR/OFF): **LC**
- CD-084 DRVINIT (close tray, read TOC) and DRVOPEN: **LB**
- CD-085 FDRSET and FDRCHG (fader services): **LC**
- CD-086 Subcode services (SCDINIT/START/STOP/STAT/READ/PQ/PQL): **LC**
- CD-087 LEDSET: **LC**
- CD-088 CDCSETMODE, CDCSTARTP, codes `$00/$01`, WONDERREQ/WONDERCHK: **LC**
- CD-089 `_CDBOOT` services (CBTINIT … CBTSPSTAT): **LC**
- CD-090 Busy/return convention (carry flag), with drive work done asynchronously from interrupts: **LB**
- CD-091 Function-code conflicts in the only source (OQ-12): **LC**

**G. CD-DA, fader, subcode, CD+G**
- CD-100 CD-DA path: drive audio through the fader to the mixer, under BIOS control: **LC**
- CD-101 Fader register `$FF8034` format, including model variants: **LC**
- CD-102 Fader ramp-rate semantics: **LC**
- CD-103 Mute and pre-emphasis flags reported by the drive: **LC**
- CD-104 Subcode buffer `$FF8100-$FF817F`, pointer `$FF8068`, Sub INT6: **LC**
- CD-105 Q-channel use (position and track info): **LC**
- CD-106 CD+G (R-W) decode for a built-in player: **LC** (optional feature)
- CD-107 Seek-to-play latency accurate enough for games that sync audio: **LC**

**H. Boot sequence (disc detection → IP execution)**
- CD-110 Sub-side BIOS init: vectors, INT2/4/5 handlers, CDD on, CDC init: **LA**
- CD-111 Wait for a ready drive or disc, with a timeout and a no-disc path: **LA**
- CD-112 Read the TOC and decide that track 1 is data: **LA**
- CD-113 Seek to and read the boot-area sectors, verifying each header: **LB**
- CD-114 Validate the system ID and reject non-bootable discs: **LB**
- CD-115 Deliver the IP to Main Work RAM `$FF0000` (the mechanism is our choice): **LB**
- CD-116 Place the SP at PRG-RAM `$6000`, call usercall0 then usercall1, route INT2 to usercall2: **LB**
- CD-117 CPU and hardware state at IP and SP entry (SR, SSP, VDP, Word RAM owner, interrupt masks): **LB** (minimal) / LC (exact)
- CD-118 Main↔Sub handshake during boot (BIOS-internal, via comm registers): **LA**
- CD-119 Audio CD inserted → player or message: **LC**
- CD-120 Mode 1 (cartridge boot) with CD services available to the cartridge: **LC**
- CD-121 Boot-time budget and timeouts that software or users expect: **LC**
- CD-122 Reset during boot and re-entry: **LC**

**I. Security and region**
- CD-130 Region check (disc region vs console region): **LC**
- CD-131 Commercial IPs begin with a region "security block" that runs on the Main CPU and calls into the boot ROM: **LC**
- CD-132 Boot of our own discs without any Sega security code (project policy): **LB**
- CD-133 Use of the header region string (`$1F0`) vs the IP byte at disc offset `$20B`: **LC**
- CD-134 No reproduction of the Sega logo/trademark screen. Policy for an independent splash: **LC**

**J. Error handling**
- CD-140 Read errors (CRC/ECC flags): retry policy and failure reporting to the caller: **LB**
- CD-141 Drive error statuses (checksum, command, function error) and the "latest error" report: **LC**
- CD-142 Drive silent (no INT4) → timeout and an error screen: **LA**
- CD-143 Tray opened or disc removed mid-read: **LC**
- CD-144 Non-bootable or foreign data disc → graceful message: **LA**
- CD-145 Detect a skipped or out-of-order sector by header compare: **LC**

Total: **105** items (LA 19, LB 36, LC 50). Counted by minimum level. CD-117 is counted as LB.
## 2. Coverage table

Abbreviations for the testability columns: "SynDisc" = our own synthetic disc image or CD-R. "Probe" = the Mode-1 probe cartridge from `../open-questions.md` OQ-1/OQ-4 (our own code, run from a flash cart on real hardware), which loads its own Sub program into PRG-RAM (B-03) and so drives CDD/CDC directly **without executing Sega BIOS code**.

| ID | Required behavior | Level | Existing material (Y/N/partial) | Exact reference URL + location | Provenance & usage terms | Implementable from public material only? (Y/Cond/N + why) | Specific missing information | Coverable by own test? | Verifiable in emulator only? | Real hardware needed? | Blocker? (Y/N + why) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CD-001 | Cooked ISO fixture recognised by emulators | LB | Y | GX `core/cd_hw/cdd.c:584-643` (ISO accepted only if `SEGADISCSYSTEM` at byte 0; otherwise needs sync or CUE); PD `pico/media.c:220-229`, `pico/cd/cdd.c:337-349`; MD `megadev.make:236-241` (ISO = boot area via `mkisofs -G` + ISO 9660) | GX/PD cite only; MD MIT | **Y** (emulator scope): own generator. CONFIRMED (scope: emulator) | Whether IDs other than `SEGADISCSYSTEM` load at all in GX/PD (they do not autodetect them; CUE path untested) | Y (SynDisc) | Y | N | N |
| CD-002 | Raw BIN 2352 + CUE fixture | LB | Y | GX `cdd.c:604-615` (sync autodetect), `cdd.c:796-812` (CUE MODE1/2048, MODE1/2352, MODE2/2352); PD `pico/cd/cd_parse.c:330-336`; EC130 (sector layout) | GX/PD cite only; EC130 public | **Y**. CUE syntax has no free official spec (de-facto CDRWIN format), so define the fixture only from what both emulators parse | Formal CUE grammar (not found in sources examined: GX, PD, MD, EC130) | Y | Y | N | N |
| CD-003 | Mixed-mode CUE, audio pregaps | LC | Y | MD `docs/disc.md:25-45` (track 1 data, 2 s pregap "per the official documentation"); GX `cdd.c:864-910` (PREGAP/INDEX handling); PD `pico/cd/cd_parse.c:366-410` | MD MIT, but the 2 s rule is second-hand from XS; GX/PD cite only | **Cond**: the layout is clear. The "2 s pregap required" rule rests on an excluded doc and is ESTIMATED | Whether the BIOS or drive needs the pregap or it is only a seek-margin recommendation | Y (SynDisc with generated tones) | Y | Partial (seek-overrun audibility) | N |
| CD-004 | Correct sync/header/EDC/ECC for raw sectors | LB | Y | EC130 (sector structure, Mode 1 EDC/ECC); GX `cdd.c:1376-1395` (emulator skips sync+header and does not verify ECC) | EC130 public | **Y** (CONFIRMED: public standard) | None for the generator. Emulators will not catch EDC/ECC bugs | Y (generator unit test vs EC130) | N (emulators do not check) | Y (CD-R read by the stock drive) | N |
| CD-005 | Data track ≥ 150 sectors | LB | partial | GX `cdd.c:630-634` (pads to 150; comment calls it a "BIOS requirement") | GX cite only | **Cond**: an emulator comment only. ESTIMATED. As a fixture rule, just pad | Origin of the requirement (probably drive lead-in / pregap behaviour) | Y | Y (scope: emulator) | Y to confirm | N |
| CD-006 | `.sub` subcode side file | LC | Y | GX `cdd.c:1284-1285` (opens `<name>.sub`), `cdd.c:1738-1775` (96 B/sector, P-W interleaved, raises INT6); EC130 (subchannels) | GX cite only; EC130 public | **Y** for P/Q (EC130). R-W CD+G content format: see CD-106 | CD+G packet format (Red Book / IEC 60908 is paid; not found free) | Y | Y | N | N |
| CD-007 | Physical CD-R the stock drive reads | LB | N | none found | - | **Cond**: burn from the CD-004 image | Whether Model 1/2 drives read CD-R reliably; ATIP or dye limits. Not found in sources examined (GX, PD, CL, MD, EC130) | Y (SynDisc) | N | Y | N |
| CD-008 | Audio-only disc does not hang the BIOS | LA | partial | MD `lib/sub/cdboot.def.h:73-81` (disc types incl. "music"); GX `cdd.c:2100-2190` (TOC reports track type via RS6 bit 3 / RS8 bit 2) | MD MIT (RE caveat); GX cite only | **Y**: classify from the TOC data flag | None for "do not hang" | Y (SynDisc audio-only CUE) | Y | Partial | N |
| CD-009 | Negative fixtures | LB | N (our own design) | - | - | **Y**: our own spec | Expected behaviour of the original BIOS for each case (not needed for our own BIOS) | Y | Y | N | N |
| CD-010 | ISO 9660 in the data track | LB | Y | EC119 (PVD at LBA 16); MD `lib/sub/cdrom.s:217-243` (application code reads the PVD at sector `$10` itself, which implies the BIOS provides no file system) | EC119 public; MD MIT | **Y** | Whether any BIOS service parses ISO 9660 (MD suggests none; S-FMT "File System" pp.8–14 excluded) | Y | Y | N | N |
| CD-011 | LBA↔MSF (LBA 0 = 00:02:00, BCD) | LA | Y | EC130 (2 s offset, MSF in header and Q); GX `cdd.c:1813-1825` (header MSF = LBA+150, BCD), `cdd.c:1945-1948` (CDD command MSF → LBA−150) | EC130 public; GX cite only | **Y** (CONFIRMED: EC130 plus an emulator) | None | Y | Y | N | N |
| CD-020 | System ID recognition and bootability | LB | partial | MD `lib/cd_boot.s:16-27` (quotes I-RHOPE: four IDs; security check only for `SEGABOOTDISC`/`SEGADISCSYSTEM`; the other two "appear" non-bootable); `../rom-layout.md` B-09; XS S-FMT App. 2 pp.18–19 (lead) | MD MIT, but the text is a quote of I-RHOPE (no licence, TLS issue) | **Cond**: `SEGADISCSYSTEM` is safe (emulators require it). The semantics of the other IDs are ESTIMATED only | Exact accepted IDs, padding/case rules, meaning of `SEGADISC`/`SEGADATADISC` | Y (SynDisc per ID) | Partial (emulators ignore the ID beyond detection) | Y for parity with real discs | N for LB (choose `SEGADISCSYSTEM`); see OQ-9 |
| CD-021 | Volume/system fields `$10-$2F` | LC | partial | MD `lib/cd_boot.s:29-40` | MD MIT (RE caveat) | **Cond**: layout known, BIOS use unknown | Whether the BIOS reads them at all | Y | N | Y | N |
| CD-022 | IP offset/size → IP load | LB | partial | MD `lib/cd_boot.s:42-56` (IP offset `$800`, size `$800`, plus a quoted "SOJ" note that the original BIOS assumes the IP starts in sector 0), `cfg/ip.ld:5-13` (IP ≤ `$E00`), `docs/boot.md:13-15` | MD MIT; the quotes are second-hand | **Cond**: our BIOS can define "load the IP from `$200` for N bytes per the fields". Exact original semantics are ESTIMATED | Exact interpretation of the offset/size fields in the original BIOS; whether the IP must start at `$200` | Y | Y (for our BIOS) | Y for parity | N for LB / Y for LC parity (see CD-027) |
| CD-023 | SP offset/size → SP at `$6000` | LB | Y | MD `lib/cd_boot.s:57-60`, `docs/boot.md:3`; `../rom-layout.md` B-07/B-08 | MD MIT | **Cond** (ESTIMATED; B-07 placement CONFIRMED only via an excluded doc) | Max SP size; whether the BIOS write-protects after loading | Y | Y | Y for parity | N |
| CD-024 | Entry/work-RAM fields `$38/$3C/$48/$4C` | LC | partial | MD `lib/cd_boot.s:55-60` (always written 0) | MD MIT | **N**: semantics unknown | Meaning of non-zero values | Y (SynDisc variants) | N | Y | N |
| CD-025 | Disc header `$100-$1FF` checks | LC | partial | MD `lib/cd_boot.s:67-85` (hardware ID, copyright, names, serial, region `JUE` at `$1F0`); GX `cdd.c:1172-1200` (GX itself keys hard-coded TOCs on the serial at `$180`) | MD MIT; GX cite only | **Cond**: layout known; BIOS checks unknown | Which fields the BIOS validates (e.g. hardware ID string) | Y | N | Y | N |
| CD-026 | Boot-area extent read by the BIOS | LB | partial | MD `lib/cd_boot.s:98-104` (SP at `$1000`, boot area padded to `$8000` = 16 sectors) | MD MIT | **Cond**: our BIOS reads what the fields say. The original extent is ESTIMATED | Number of sectors the original reads; whether the SP can exceed the boot area | Y | Y | Y for parity | N |
| CD-027 | IP size limit / sector-1 quirk | LC | partial | MD `lib/cd_boot.s:42-50`, `docs/boot.md:13-15` | MD MIT (quotes) | **N** for exact parity | Exact rule; whether commercial discs depend on it | Y | N | Y | N |
| CD-028 | SP header format and usercall table | LB | Y | MD `lib/sub/sp_header.s:8-25`, `docs/boot.md:19-26`; `../bios-api.md` A-01/A-02 | MD MIT (RE caveat) | **Cond**: the usable spec is in MD; official §5-3 is excluded | Meaning of the flag/type/next-module fields; module chaining | Y | Y | Y for parity | N for LB (if MD is accepted, #17) |
| CD-029 | Disc-type classification | LC | partial | MD `lib/sub/cdboot.def.h:73-93` | MD MIT (RE caveat) | **Cond**: the codes are known; the classification rules are not | Rules mapping TOC + ID → type 0–7 | Y | N | Y | N |
| CD-030 | HOCK enable, INT4 per CDD frame | LA | Y | GX `core/cd_hw/scd.c:1541-1546` (only bit 2 writable), `scd.c:1943-1965` (75 Hz; INT4 only while bit 2 is set); MD `lib/sub/gate_arr.def.h:433`; `../memory-map.md` level 4 | GX cite only; MD MIT | **Cond**: the emulator model is consistent. Hardware rate is ESTIMATED. A NeoGeo-CD wiki note (<https://wiki.neogeodev.org/index.php/CD_drive_control>, different machine) mentions about 64 Hz rather than 75 for its CDD: an **unresolved conflict** | Real INT4 period and jitter; whether it is drive-timed | Y (Probe) | Y (scope: emulator) | Y | N (LA in emulator) / Y for real-HW LA |
| CD-031 | Status frame layout | LA | Y | GX `cdd.c:2026-2078`, `cdd.c:2330-2335`; PD `pico/cd/cdd.c:855-1228` (derived); BE `cdd_mcu.h` (`status_format`, `drive_status` enums, `current_status_nibble`); MD `lib/sub/gate_arr.def.h:440-503` | GX/PD/BE cite only | **Cond**: two independent emulator lineages (GX, BE) agree on the nibble frame. ESTIMATED | Unused-nibble values on hardware; per-report RS8 flags | Y (Probe log) | Y | Y | N (emulator) |
| CD-032 | Command frame and send trigger | LA | Y | GX `scd.c:1548-1556` (write to `$FF804A` → `cdd_process`); BE `cdd_mcu.h` (`current_cmd_nibble`, `cmd_recv_pending`) | as above | **Cond** (ESTIMATED) | Whether hardware needs all nibbles written in order; word vs byte access | Y (Probe) | Y | Y | N |
| CD-033 | Checksum algorithm and bad-checksum reaction | LA | partial | GX `cdd.c:2330-2335` (status: low nibble of the inverted nibble sum); BE `cdd_mcu.h` (`checksum` fields); GX `cdd.h:63` defines "no valid checksum" status 6 but never uses it | GX/BE cite only | **Cond** for the algorithm. **N** for the drive reaction (GX does not verify command checksums) | Real drive response to a bad command checksum; whether the BIOS must verify the status checksum | Y (Probe sends a bad checksum; harmless) | N | Y | N (LA) / Y for LC robustness |
| CD-034 | Status code set | LA | Y | GX `core/cd_hw/cdd.h:56-71`; BE `cdd_mcu.h` (`drive_status`: same order 0–E) | GX/BE cite only | **Cond**: two lineages agree. ESTIMATED | When each error status (6/7/8, A, D, E) actually occurs | Y (Probe) | Partial | Y | N |
| CD-035 | Command code set | LA | Y | GX `cdd.c:2024-2325` (0,1,2,3,4,6,7,8,9,A,C,D; others "unsupported"); BE `cdd_mcu.h` (`host_cmd`: NOP, STOP, REPORT_REQUEST, READ, SEEK, INVALID, PAUSE, PLAY, FFWD, RWD, TRACK_SKIP, TRACK_CUE, DOOR_CLOSE, DOOR_OPEN) | GX/BE cite only | **Cond**: the codes agree. Naming differs (GX "Play/Resume" = BE "READ/PLAY") | Semantics of `$5`/`$B`; exact difference between `$3` and `$7` | Y (Probe) | Y | Y | N |
| CD-036 | Report sub-codes 0–6 (incl. TOC) | LA | Y | GX `cdd.c:2100-2190` (abs/rel time, track no., total length, first/last, track start with RS6 bit 3 = data track, error info); BE `cdd_mcu.h` (`SF_*`: ABSOLUTE, RELATIVE, TRACK, TOCO, TOCT, TOCN, E); EC130 (Q-channel TOC content) | GX/BE cite only; EC130 public | **Cond** (ESTIMATED; the TOC concept is CONFIRMED by EC130) | Exact nibble placement on hardware for each report; lead-in vs lead-out flags | Y (Probe + SynDisc) | Y | Y | N |
| CD-037 | Latency and seek timing | LB | partial | GX `cdd.c:1950-1976` (minimum 2 frames "or the BIOS hangs", +10/step option; linear seek of up to ~120 frames, explicitly "rough approximation"); GX `cdd.c:2028-2031` (games needing ≥ 2–3 "playing" reports) | GX cite only | **N** for hardware (game-tuned emulator constants) | Real command-to-status latency, seek-time curve, spin-up time | Y (Probe timing log) | N | Y | N for LB (a tolerant BIOS can poll) / Y for LC (see CD-107) |
| CD-038 | RS1 = `$F` invalid during seek | LB | Y | GX `cdd.c:2193-2222`, `cdd.c:2041-2052` | GX cite only | **Cond** (emulator; second-hand game evidence in comments) | Hardware confirmation | Y (Probe) | Y | Y | N |
| CD-039 | Power-on drive state and bring-up | LA | partial | GX `cdd.c:216-234` (reset: fader full, latency 0), `cdd.c:2080-2098` and `2276-2295` (stop/close → TOC-read or no-disc); MD `lib/sub/bios.def.h:213-228` (DRVOPEN/DRVINIT exist) | GX cite only; MD MIT | **Cond**: an emulator model only | Real status sequence after power-on (tray state, spin-up, automatic TOC read?) | Y (Probe cold boot) | N | Y | N (emulator) / Y real-HW LA |
| CD-040 | HOCK/CDCK nibble link pacing | LA | N | BE `cdd_mcu.h` (`cdd_hock_enabled/disabled`, cycle fields); gendev forum thread on HOCK/CDCK (<https://gendev.spritesmind.net/forum/viewtopic.php?p=21203>): not read in detail | BE cite only; forum (no licence) | **N**: not specified in non-excluded sources | Whether the gate array buffers the whole frame (pure register model) or software must time accesses | Y (Probe) | N | Y | N (all emulators use the register model) |
| CD-041 | `$FF8036` status bits | LC | partial | GX `cdd.c:1833-1930` (sets `$FF8036` high byte to 0/1 for audio playing) | GX cite only | **Cond** | Bit meanings and read behaviour on hardware | Y (Probe) | Partial | Y | N |
| CD-042 | Track jump `$A` | LC | partial | GX `cdd.c:2261-2274` (comment: parameter meaning unknown, refers to a Sony DSP datasheet and US patent 5,222,054) | GX cite only | **N** | Parameter semantics | Y (Probe) | N | Y | N |
| CD-043 | Codes `$5`/`$B`/`$E`/`$F` | LC | partial | BE `cdd_mcu.h` (`CMD_INVALID`=5, `CMD_TRACK_CUE`=B); GX `cdd.c:2318-2325` | BE/GX cite only | **N** | Behaviour | Y (Probe) | N | Y | N |
| CD-050 | Motorised tray open/close | LC | Y | GX `cdd.c:2276-2316` (`$C` close → TOC/no-disc; `$D` open → status 5); MD `lib/sub/bios.def.h:213`, `lib/sub/cdboot.def.h:33-57` | GX cite only; MD MIT | **Cond** | Tray-moving status duration; behaviour on top-loaders | Y (Probe, Model 1) | Partial | Y | N |
| CD-051 | Top-loader lid detection | LC | N | not found in sources examined (GX, PD, CL, BE, MD) | - | **N** | How a lid-open is reported (status code? timing?) | Y (Probe, Model 2) | N | Y | N |
| CD-052 | Insertion → TOC read | LA | partial | GX `cdd.c:2276-2295` (close → status 9 "TOC" when loaded) | GX cite only | **Cond** | Whether the drive reads the TOC on its own or needs a command | Y (Probe) | Y (scope: emulator) | Y | N |
| CD-053 | No-disc detection | LA | Y | GX `cdd.h:68` (status B), `cdd.c:2083`; BE `cdd_mcu.h` (`DS_NO_DISC`) | GX/BE cite only | **Cond** (two lineages agree) | Time until no-disc is reported | Y (emulator with no disc; Probe) | Y | Y | N |
| CD-054 | Disc change while running | LC | N | not found in sources examined | - | **N** | Status sequence and required re-init | Y (Probe) | Partial | Y | N |
| CD-055 | Pause→standby timer | LC | partial | MD `lib/sub/bios.def.h:424-434` (CDBPAUSE sets the spin-down delay) | MD MIT (RE caveat) | **Cond**: the API exists; units unknown | Units and default; whether the drive or the BIOS implements it | Y | N | Y | N |
| CD-056 | Lead-out / end status | LC | partial | GX `cdd.c:1800-1804` (status C at end of disc); BE `DS_DISC_LEADOUT` | GX/BE cite only | **Cond** | Real behaviour at lead-out (auto-stop? loop?) | Y (SynDisc + Probe) | Y | Y | N |
| CD-057 | LEDs and LED modes | LC | partial | MD `lib/sub/gate_arr.def.h:29-44` (LEDR/LEDG at `$FF8000`), `lib/sub/bios.def.h:630-659` (LEDSET modes 0–7) | MD MIT | **Cond** | Blink patterns per mode | Y (Probe, visual) | N | Y | N |
| CD-060 | CDC identity and register access | LB | Y | GX `core/cd_hw/cdc.c:3` ("LC8951x compatible"), `cdc.c:585-750` (writes), `cdc.c:760-870` (reads), `scd.c:1412-1434`; MD `lib/sub/gate_arr.def.h:163-205`; LCDM (whole document) | GX cite only; MD MIT; LCDM provenance unverified | **Cond**: the vendor design manual (if cleared) plus emulators give a full register-level spec | Clearance of LCDM; gate-array specifics (address auto-increment, which bits of `$FF8004`) are emulator-only | Y (Probe) | Y | Y | N |
| CD-061 | CDC reset and init | LB | Y | GX `cdc.c:743-750` (RESET reg `$F`), `cdc.c:75-90`; LCDM | as above | **Cond** | Required init order and values for this board (clock, buffer size config) | Y (Probe) | Y | Y | N |
| CD-062 | Decoder enable / mode | LB | Y | GX `cdc.c:56-64` (DECEN, AUTORQ, WRRQ, MODRQ, FORMRQ, SHDREN), `cdc.c:686-733`; MD `lib/sub/bios.def.h:663-704` (BIOS mode 0/1/2) | GX cite only; MD MIT | **Cond** | Error-correction modes and their effect on STAT flags | Y | Y | Y | N |
| CD-063 | Buffer write, WA/PT, 16 KiB ring | LB | Y | GX `cdc.h:61` (16 KiB plus overrun slack), `cdc.c:520-580` | GX cite only; LCDM | **Cond** | Buffer size on each model (16 KiB is ESTIMATED) | Y (Probe) | Y | Y | N |
| CD-064 | HEAD0-3 header check | LB | Y | GX `cdc.c:792-815`, `cdd.c:1813-1825`; EC130 | GX cite only; EC130 public | **Y** (header content is CONFIRMED by EC130; register access is Cond) | None for Mode 1 | Y | Y | N | N |
| CD-065 | STAT0-3 flags | LB | partial | GX `cdc.c:840-870` (STAT1 always 0; STAT3 VALST; comment that its handling is "not 100% correct but BIOS do not seem to care") | GX cite only; LCDM | **Cond** (LCDM) / emulator incomplete | Real error flags under bad reads; emulators never produce errors | Partial (needs damaged media) | N | Y | N (LB) |
| CD-066 | DECI → INT5 and acknowledge | LB | Y | GX `cdc.c:487-517`, `cdc.c:764-775`, `cdc.c:862-869`; `../memory-map.md` level 5 | GX cite only | **Cond** | Exact clear condition on hardware | Y (Probe) | Y | Y | N |
| CD-067 | DBC/DAC/DTRG/DTACK transfer | LB | Y | GX `cdc.c:631-676`, `cdc.c:255-325`; LCDM | GX cite only | **Cond** | DBC off-by-one and DBCH upper-bit behaviour (GX comment `cdc.c:283`) | Y (Probe) | Y | Y | N |
| CD-068 | Sub host read via `$FF8008` | LB | Y | GX `cdc.c:261-325` (DD=3; DSR set per word; EDT at end), `scd.c:1436-1441` (a write also reads, "verified on real hardware" via Krikzz's tool, second-hand); MD `lib/sub/gate_arr.def.h:643-653`, `lib/sub/cdrom.s:339-390` | GX cite only; MD MIT | **Cond** | First-hand hardware confirmation | Y (Probe) | Y | Y | N |
| CD-069 | Main host read via `$A12008` | LC | partial | GX `cdc.c:261` (DD=2); `../memory-map.md` `$A12004/$A12008`; MD `docs/cdrom.md:59` ("Main CPU read … not well understood") | GX cite only; MD MIT | **Cond** (emulator only) | Handshake between Main and Sub for this path | Y (Probe) | Y | Y | N |
| CD-070 | DMA → PRG-RAM | LB | Y | GX `cdc.c:332-345` (halts while Main holds PRG-RAM), `scd.c:121-135` (address = `$FF800A` × 8) | GX cite only | **Cond** | Hardware confirmation of the unit and halt behaviour; MR `docs/mcd logs/dma_prgram*.PNG` (not opened) may cover it | Y (Probe) | Y | Y | N |
| CD-071 | DMA → Word RAM (2M/1M) | LC | Y | GX `cdc.c:348-372`, `gfx.c:44-130` (× 8 units; bank select) | GX cite only | **Cond** | As CD-070; MR `dma_wordram*.PNG` (not opened) | Y (Probe) | Y | Y | N |
| CD-072 | DMA → PCM RAM | LC | Y | GX `cdc.c:326-330`, `pcm.c:398-407` (× 4 units) | GX cite only | **Cond** | As above; MR `dma_pcm*.PNG` | Y (Probe) | Y | Y | N |
| CD-073 | `$FF8004` write resets DMA addr/dest | LB | Y | GX `scd.c:1412-1428` (comments: "verified on real hardware, cf. Krikzz's mcd-verificator") | GX cite only; second-hand HW claim | **Cond** | First-hand confirmation | Y (Probe) | Y | Y | N |
| CD-074 | Transfer throughput/timing | LC | partial | GX `cdc.c:69-73` (≥ 16 SCD clocks/byte, citing MR "mcd logs"; stalls not modelled) | GX cite only; MR lead | **N** (hardware timing unconfirmed) | Real DMA rate under contention | Y (Probe) | N | Y | N |
| CD-075 | LC89513K variant | LC | partial | GX `cdc.c:79-90` (5-bit register address on CDX / WM2 types); LC89513K datasheet lead: <https://bitsavers.mirrorservice.org/components/sanyo/_dataSheets/LC89513K.pdf> (not read) | GX cite only; datasheet not read | **Cond** | Which retail models use which chip; software-visible differences | Y (Probe per model) | N | Y | N |
| CD-076 | Mode 2 / XA sub-header | LC | partial | GX `cdc.c:545-570`; EC130 (Mode 2) | GX cite only; EC130 public | **Cond** | Which titles use Mode 2; whether the BIOS must support it | Y (SynDisc Mode 2) | Y | N | N |
| CD-077 | Ring overrun behaviour | LC | partial | GX `cdc.c:573-577` | GX cite only | **N** (hardware) | Overwrite vs stall semantics | Y (Probe) | N | Y | N |
| CD-080 | Data-read services | LB | partial | MD `lib/sub/bios.def.h:314-365`, `:458-539` (codes and notes); `lib/sub/cdrom.s:289-390` (call sequence: CDCSTOP → ROMREADN → poll CDCSTAT → CDCREAD → CDCTRN or DMA → CDCACK); CL `source/bus-sub-m68k.c:64-330` (HLE; the author notes its calls are not accurate, `:66`) | MD MIT but **codes appear to derive from XS S-BIOS or RE** (#17, OQ-7); CL AGPL cite only | **Cond**: implementable to MegaDev's usage only. Input/output registers, error codes and edge cases (0 sectors, negative counts: open TODOs at CL `bus-sub-m68k.c:128,140`) are not specified | Official ABI is excluded; no clean-room spec | Y (own SP calling our BIOS) | Y | N for our BIOS | **Y** (LB): homebrew built with MegaDev depends on these codes, which have no cleared source. Needs a #17/OQ-7 decision |
| CD-081 | CDBSTAT / `$5E80` status block | LB | partial | MD `lib/sub/bios.def.h:62-66`; CL `source/bus-sub-m68k.c:151-171` (placeholder layout "enough to boot one game"; real address unknown) | as CD-080 | **N** | Field layout and update timing | Y | N | Y (clean-room observation) | **Y** (LC; LB only if homebrew polls it) |
| CD-082 | CDBCHK/TOCREAD/TOCWRITE | LC | partial | MD `lib/sub/bios.def.h:376-420`; CL `bus-sub-m68k.c:146-176` | as CD-080 | **Cond** (outputs only partly described) | Exact outputs | Y | N | Y | N |
| CD-083 | CD-DA (MSC*) services | LC | partial | MD `lib/sub/bios.def.h:149-334` (incl. OQ-12 duplicates `$11`/`$12`); CL `bus-sub-m68k.c:73-101` | as CD-080 | **Cond**: semantics only as MD comments | Repeat/loop flags, end-of-track behaviour, return codes | Y (SynDisc mixed mode) | N | Y | **Y** (LC: no cleared spec) |
| CD-084 | DRVINIT / DRVOPEN | LB | partial | MD `lib/sub/bios.def.h:213-228` | as CD-080 | **Cond** | Parameter table format for DRVINIT | Y | N | Y | N (LB can boot without a game calling it) |
| CD-085 | FDRSET / FDRCHG | LC | partial | MD `lib/sub/bios.h:518-552` (volume `$0000-$0400`, rate values) | as CD-080 | **Cond** | Rate units, master vs system volume | Y | N | Y | N |
| CD-086 | SCD* subcode services | LC | partial | MD `lib/sub/bios.def.h:543-626` | as CD-080 | **Cond** | Buffer formats | Y | N | Y | N |
| CD-087 | LEDSET | LC | partial | MD `lib/sub/bios.def.h:630-659` | as CD-080 | **Cond** | Patterns | Y | N | Y | N |
| CD-088 | CDCSETMODE, CDCSTARTP, `$00/$01`, WONDER* | LC | partial | MD `lib/sub/bios.def.h:131-141`, `:471-474`, `:686-720` ("needs research") | as CD-080 | **N** | Everything except CDCSETMODE | N without observation | N | Y | N |
| CD-089 | `_CDBOOT` services | LC | partial | MD `lib/sub/cdboot.def.h:15-125` (calls 6–9 "no official documentation") | as CD-080 | **N** | Semantics of CBTIPDISC…CBTSPSTAT; which titles call them | Y | N | Y | **Y** (LC: titles that re-boot from disc) |
| CD-090 | Carry-flag busy convention; async drive work | LB | partial | MD `lib/sub/cdboot.def.h:38-68` (CC/CS), `docs/cdrom.md:3` (work pumped from INT2); CL `bus-sub-m68k.c:148,219-221`; **CL caveat**: CL intercepts execution at `$5F22` (`bus-sub-m68k.c:882-888`) and implements no CDD registers `$FF8034-$FF804B` (no handlers in `:941-1053`), and CL's CDC is high level (`source/cdc.c:44-75`) | MD MIT; CL AGPL | **Cond** | Which calls are synchronous | Y | Y (GX/PD only; **CL cannot test our CD driver** and would hijack our `$5F22` entry) | N | N |
| CD-091 | Function-code conflicts | LC | Y (conflict) | `../open-questions.md` OQ-12; MD `lib/sub/bios.def.h:235-262` | MD MIT | **N** | Authoritative code list (only in excluded S-BIOS §2-2) | N | N | Y (observation) | **Y** (LC; part of the CD-080 blocker) |
| CD-100 | CD-DA path under BIOS control | LC | partial | GX `cdd.c:1476-1700` (CD-DA mixing through the fader) | GX cite only | **Cond** | Analogue path; mute timing | Y (SynDisc tones + Probe) | Y | Y | N |
| CD-101 | Fader `$FF8034` format and model variants | LC | partial | GX `scd.c:1501-1538` (default LC7883-type: 12-bit value in bits 4–15; Wondermega/M2 variants differ); MD `lib/sub/gate_arr.def.h:426` | GX cite only | **Cond** (emulator; LC7883 datasheet not located) | Real attenuation curve per model; unused bits | Y (Probe + audio capture) | N | Y | N |
| CD-102 | Fader ramp semantics | LC | partial | GX `cdd.c:1559`, `:1622`, `:1677` (one step per sample, "cf. LC7883 datasheet"); MD `lib/sub/bios.h:540-552` | GX/MD | **Cond** | Is ramping done by hardware or by the BIOS? | Y (Probe + capture) | N | Y | N |
| CD-103 | Mute/pre-emphasis flags | LC | partial | GX `cdd.c:2049` (RS8 bit 0 mute, bit 1 pre-emphasis, bit 2 track type) | GX cite only; EC130 (Q control field) | **Cond** | Whether de-emphasis is automatic | Y | N | Y | N |
| CD-104 | Subcode buffer, `$FF8068`, INT6 | LC | Y | GX `cdd.c:1738-1775`; MD `lib/sub/gate_arr.def.h:620-638`; `../memory-map.md` level 6 | GX cite only; MD MIT | **Cond** | Buffer image region `$FF8180` semantics; timing vs sector | Y (SynDisc `.sub`) | Y | Y | N |
| CD-105 | Q-channel use | LC | Y | EC130 (subchannel Q) | public | **Y** (format CONFIRMED) | None | Y | Y | N | N |
| CD-106 | CD+G decode for the player | LC | N | Red Book / IEC 60908 (paid, not examined) | - | **N** from free sources | CD+G packet/instruction format | Y (SynDisc after a spec) | Y | N | N (optional feature) |
| CD-107 | Seek-to-play latency accuracy | LC | partial | GX `cdd.c:1961-1976` (tuned against a game's real-hardware recording; comment), `cdd.c:1952-1957` | GX cite only | **N** | Real seek and spin timings | Y (Probe) | N | Y | **Y** (LC: games desync without it; no source) |
| CD-110 | Sub BIOS init (vectors, INT handlers, CDD, CDC) | LA | partial | `../rom-layout.md` B-05/B-07; `../memory-map.md` §4; MD `lib/sub/memmap.def.h:64-95` | as cited there | **Cond** (our own design; the needed hardware facts are in CD-030/060) | None beyond CD-030/060 | Y | Y | Y for real-HW LA | N |
| CD-111 | Wait for drive/disc with timeout | LA | partial | GX `cdd.c:1950-1957` (minimum latency) | GX cite only | **Cond** | Real worst-case spin-up/TOC time for choosing timeouts | Y | Y | Y | N |
| CD-112 | TOC read, track 1 is data | LA | Y | CD-036 sources; EC130 (Q control: data track flag) | as CD-036 | **Cond** | As CD-036 | Y | Y | Y | N |
| CD-113 | Read boot sectors with header verify | LB | Y | CD-032/064/068 sources; MD `lib/sub/cdrom.s:289-390` | as cited | **Cond** | Pre-seek margin (MD notes the BIOS pre-seeks 2–4 sectors: `lib/sub/bios.def.h:458-467`) | Y | Y | Y | N |
| CD-114 | Validate system ID | LB | partial | CD-020 | as CD-020 | **Cond** | As CD-020 | Y | Y | Y | N |
| CD-115 | Deliver the IP to `$FF0000` | LB | Y | MD `docs/boot.md:3`, `cfg/ip.ld:5-13`; `../rom-layout.md` B-08 | MD MIT | **Y** for our own mechanism (e.g. via Word RAM, B-03/W-02) | None for LB | Y | Y | N | N |
| CD-116 | SP at `$6000`, usercall0/1/2 | LB | Y | MD `docs/boot.md:19-26`, `lib/sub/sp_header.s`; `../bios-api.md` A-01/A-02 | MD MIT | **Cond** | Call order and re-entry (e.g. does usercall1 loop?), INT2 timing | Y | Y | Y for parity | N (LB) |
| CD-117 | CPU and hardware state at IP/SP entry | LB/LC | N | not found in sources examined (MD `docs/megacd_dev.md` stack notes are self-contradictory: OQ-2) | - | **N** | SR, SSP, VDP regs, Word RAM owner, interrupt enables, Z80 state at entry | Y (emulator only; not observable on HW without running Sega code) | Partial | Y | **Y** (LC) |
| CD-118 | Main↔Sub boot handshake | LA | partial | `../rom-layout.md` B-02; `../memory-map.md` comm registers | as cited | **Y** (internal to our BIOS) | None | Y | Y | N | N |
| CD-119 | Audio CD → player or message | LC | partial | MD `lib/sub/cdboot.def.h:73-81` | MD MIT | **Y** (any UI of our own) | None (the UI is ours) | Y | Y | N | N |
| CD-120 | Mode 1 with CD services | LC | partial | `../rom-layout.md` B-02 (S-BIOS §4-1, excluded) | XS | **N** | How a cartridge obtains the CD BIOS in Mode 1 | Y (Probe) | Partial | Y | N (other area overlap) |
| CD-121 | Boot-time budget | LC | N | not found in sources examined | - | **N** | Any software or attract-mode timing dependency | Y | N | Y | N |
| CD-122 | Reset during boot | LC | N | not found in sources examined | - | **Cond** (our own design) | Soft-reset semantics expected by games | Y | Y | Y | N |
| CD-130 | Region check | LC | partial | `../rom-layout.md` R-30/R-31; `../open-questions.md` OQ-8 | I-RHOPE (no licence, TLS issue) | **N** (policy and legal) | Legal decision; region-code semantics | Y (SynDisc per region byte) | Y | N | **Y** (legal/policy, OQ-8) |
| CD-131 | Commercial security block calls into the boot ROM | LC | partial (excluded content) | MD `docs/boot.md:13` (IP must contain the security code); MD `lib/security.c` (**excluded; not analysed**: on first-line inspection it appears to contain Main-CPU code that calls a fixed low boot-ROM address; address deliberately not recorded); I-RHOPE ("On the Genesis Side", see R-31) | Sega-authored code inside an MIT repo; I-RHOPE | **N** | What the boot ROM must provide at the called address(es), and what the block expects back (logo display, verification), with no access to the Sega code | Only by clean-room observation | N | Y | **Y** (LC: every commercial disc; legal + no independent spec) |
| CD-132 | Boot own discs without Sega code | LB | Y (policy) | `../bios-api.md` §4; `../provenance.md` rules 1–3 | project policy | **Y** | Fixture IP layout without a security block (MD always prepends it: `megadev.make:213-219`, so **MegaDev's default build cannot be used for fixtures**) | Y | Y | N | N |
| CD-133 | `$1F0` string vs byte `$20B` | LC | partial | MD `lib/cd_boot.s:84-85`; GX `core/loadrom.c` R-30; PD `pico/media.c:239-245` | MD MIT; GX/PD cite only | **Cond** | Which one the BIOS uses (`$20B` lies inside the IP security block) | Y | Y | Y | N |
| CD-134 | No Sega logo; independent splash | LC | Y (policy) | `../bios-api.md` §4 | project policy | **Y** | Legal review of trademark-lockout interplay (OQ-8) | Y | Y | N | N |
| CD-140 | Read-error retry/reporting | LB | partial | MD `docs/cdrom.md:65-73` (application-level result codes); GX `cdc.c:840-870` (no error emulation) | MD MIT | **Cond** (our own policy) | Real error flag behaviour; BIOS error-return codes for compatibility | Partial (needs damaged CD-R) | N | Y | N |
| CD-141 | Drive error statuses and the "latest error" report | LC | partial | GX `cdd.c:2172-2181` (always "no error"); BE `DS_SUM_ERROR`/`DS_CMD_ERROR`/`DS_FUNC_ERROR` | GX/BE cite only | **N** | Error-code payloads | Y (Probe with bad commands) | N | Y | N |
| CD-142 | Drive silent → timeout | LA | N | not found in sources examined | - | **Y** (our own watchdog design) | None | Y (emulator with HOCK never acked; hard to force) | Partial | N | N |
| CD-143 | Tray open or disc removed mid-read | LC | N | not found in sources examined | - | **N** | Status sequence | Y (Probe) | N | Y | N |
| CD-144 | Foreign data disc → message | LA | partial | CD-020 | as CD-020 | **Y** (our own rule) | None | Y (SynDisc without an ID) | Y | N | N |
| CD-145 | Skipped/out-of-order sector detection | LC | partial | GX `cdd.c:1813-1825`; EC130 header | GX cite only; public | **Y** (compare HEAD MSF to the expected value) | None | Y | Partial (emulators never skip) | Y | N |
## 3. Per-level summary

"Spec defined" counts rows whose Implementable column is **Y** or **Cond**, i.e. a concrete expected behaviour can be written from non-excluded sources (GX/PD/CL/BE/MD/EC130/EC119/LCDM). Many Cond rows are **emulator-scoped**, not hardware-verified. Excluded XS material contributed nothing.

| Level | Items enumerated | Spec defined from non-excluded sources | Of which Y (public standard or our own design) | N (no spec) | Blockers |
| --- | --- | --- | --- | --- | --- |
| LA | 19 | 18 | 5 (CD-008, 011, 118, 142, 144) | 1 (CD-040) | none **in emulator**. On real hardware, CD-030–040 lack hardware-confirmed behaviour and timing (Cond → needs the Probe, §4 item 2) |
| LB | 36 | 33 | 8 (CD-001, 002, 004, 009, 010, 064, 115, 132) | 3 (CD-037, 081, 117) | **CD-080** (`_CDBIOS` ABI only via MegaDev; provenance #17/OQ-7), **CD-081** (only if homebrew polls `$5E80`). CD-117 for LB is our own choice; its exact form is an LC blocker |
| LC | 50 | 31 | 5 (CD-006, 105, 119, 134, 145) | 19 | **CD-083**, **CD-089**, **CD-091**, **CD-107**, **CD-130**, **CD-131** (+ CD-117 exact state) |
| **Total** | **105** | **82** | 18 | 23 | 9 rows flagged Y (CD-080, 081, 083, 089, 091, 107, 117, 130, 131) |

Top 5 blockers:
1. **CD-131**: commercial IPs start with a Sega security block that calls into the boot ROM. There is no independent spec of what the ROM must provide, and the only source in reach (MegaDev `lib/security.c`) is Sega code (excluded). Blocks LC for every commercial disc. Needs legal input plus a clean-room observation protocol.
2. **CD-080/081/091**: the `_CDBIOS` function codes, register ABI and `$5E80` status block exist only in MegaDev, which appears to derive from the excluded S-BIOS or from RE. Blocks LB compatibility with MegaDev-built homebrew until #17/OQ-7 is decided. Also blocks LC.
3. **CD-130** (+ CD-133): region-check policy is a legal decision (OQ-8). The region byte lives inside the security block.
4. **CD-107/037** (+ CD-074): CDD seek/latency and transfer timing. Only game-tuned emulator constants exist. Commercial titles that sync audio or expect delays fail without them. Needs Probe measurements.
5. **CD-117** (+ CD-083/089): CPU and hardware state at IP/SP entry, and the CD-DA/`_CDBOOT` service semantics, have no source in the material examined.

Additional harness finding (not a blocker, but it affects test design): clownmdemu intercepts `$5F22` and does not model the CDD registers (CD-090). Only GX and PD can exercise a register-level CD driver, and PD's CD model derives from GX. Emulator agreement between GX and PD is therefore **not** two independent confirmations.

## 4. Feasible legal independent experiments (design only)

All experiments use our own code and our own synthetic discs. They need no Sega code or dumps in the repository or CI, distribute no commercial software, and have no hardware-damage risk (no over-voltage, no forced mechanics: tray commands go only through the drive's own command set).

1. **Synthetic disc suite (closes CD-001–011, 020, 029, 132, 144; emulator side of most rows).** Write our own generator for ISO (2048), BIN (2352 with EC130 EDC/ECC) and CUE images. It produces: an ID variants matrix (4 IDs, padding, case), header field variants (IP/SP offset/size, oversize, zero), region byte and `$1F0` variants, short data track (< 150 sectors), mixed mode with generated sine/sweep tones and 0/2 s pregaps, an audio-only disc, Mode 2 track, `.sub` files with synthetic Q and simple R-W patterns. The IP contains **no security block**: build fixtures without MegaDev's `security.c`. Run the suite in GX (fork `87dd8b8`) and PD. Record per-case behaviour as emulator-scoped facts.
2. **Mode-1 CDD logger probe (CD-030–043, 050–056, 141, 143).** The Probe cartridge loads our own Sub program, enables HOCK, and logs every status frame with a timer timestamp to Word RAM. The Main side displays or dumps it over the controller port. Scripted sequences: cold boot, close/open, no disc, our CD-R inserted, each command code including the undefined ones, deliberately bad command checksum, track jump parameters, lid open on top-loaders. It gives the first non-excluded hardware data for the CDD protocol and timing.
3. **CDC/DMA probe (CD-060–077, 140, 145).** Same Probe: register read-back after reset; DMA to PRG/Word/PCM with known address-register values, to establish address units; `$FF8004` write side effects; DSR/EDT sequencing; DMA rate by timer; overrun by withholding acknowledgement. Use a scratched or deliberately mastered-with-errors CD-R of our own to see STAT flags. Cross-check against LCDM once its provenance is cleared, and against MR captures (open and evaluate their provenance first).
4. **Fader and CD-DA capture (CD-100–103, 107).** Play our generated tone track. Step `$FF8034` through its values while recording line-out with an ADC, to derive the attenuation curve and ramp behaviour per model. Measure seek-to-audio latency between known MSF positions. Purely passive audio capture.
5. **CD-R compatibility matrix (CD-007).** Burn the same fixture on several media and speeds and record read success per drive model. Non-destructive.
6. **Clean-room observation of reference BIOS services (CD-080–089, 117, 131). Needs a maintainer and legal decision first (OQ-7, #17).** Team A runs a Probe that calls the retail BIOS `_CDBIOS`/`_CDBOOT` entries with our synthetic disc, recording only inputs and outputs (registers, flags, `$5E80` contents, timings) into behaviour notes. Team B implements from the notes alone. Nobody reads disassembly. For CD-117 and CD-131, a logic-analyser capture of the 68000 bus while a legitimately owned retail disc boots would record CPU state and the addresses that the security block touches, **not code bytes**. Its legality must be reviewed before anyone attempts it.
7. **Review LCDM and MR provenance (desk task).** A human checks the LC8950/8951 design-manual scan for confidentiality markings or a publisher notice. A human opens MR `docs/mcd logs` to see whether they are original third-party measurements (usable as "measured, third party") or derived from Sega material.

## 5. Not investigated

* MR `docs/mcd logs/*.PNG` content, and the authorship of those captures.
* BlastEm full source (`cdd_mcu.c`, fader), its licence, and its pinned upstream. Only `cdd_mcu.h` enum names were read via WebFetch.
* Krikzz "mcd-verificator" source, test list and licence (forum: <https://gendev.spritesmind.net/forum/viewtopic.php?p=36660>). The repository location was not confirmed.
* LC89513K and LC7883 datasheets (only located, not read). LCDM was not read page by page.
* EC130 / EC119 clause and page numbers (the documents were located but not read clause by clause; add precise locations on review).
* The source and licence of the replacement boot ROM bundled in CL (`source/mega-cd-boot-rom.c`, a pre-built word array included at `source/bus-main-m68k.c:19-20`, `:519`). Its embedded header suggests an independently written ROM, but its source is not in the examined repository. This is potential prior art worth reviewing.
* I-RHOPE was not re-fetched (TLS mismatch as recorded in `../README.md`).
* The gendev HOCK/CDCK thread (<https://gendev.spritesmind.net/forum/viewtopic.php?p=21203>) and the NeoGeo CD wiki page beyond the search summary.
* Per-model differences: LaserActive Mega-LD pack, Sega CD 32X boot, Wondermega / X'Eye / CDX drives, multi-session discs.
* The content of S-FMT, S-SDM, S-HW and S-BIOS (excluded by #17; only their TOC titles are listed as leads).
* SEGAJP (HTTP 403 again on 2026-10-08) and I-RETROSIX (login required).
* Mode 1 cartridge-side use of CD services (overlaps the cartridge and boot areas of other agents).