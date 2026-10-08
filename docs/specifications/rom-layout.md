# BIOS ROM layout and boot requirements

Source IDs and evidence labels are defined in [README.md](README.md). Emulator citations use `path:line` at the pinned commit. Official citations give document, section and printed page number; the scan file name is `Cdh-NN.gif` or `Bios-NN.gif` with NN equal to the printed page. "OQ-n" refers to [open-questions.md](open-questions.md).

## 1. ROM window and image size

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| R-01 | In Mode 2 (boot from CD, no cartridge), the internal boot ROM occupies Main-CPU addresses `$000000-$01FFFF`. That is 1 Mbit = 128 KiB. | **CONFIRMED** | S-HW §1 "Mapping", 1-1 Mapping Mode, p.12 (diagram labels the area "1M ROM"), and §1-3 Main-CPU Mapping, p.16 ("$000000-$01FFFF: for CD-ROM boot"). E-GPGX `core/cd_hw/scd.h:73` (`bootrom[0x20000]`), `core/cd_hw/scd.c:1604-1605`. E-PICO `pico/pico_int.h:556` (`bios[0x20000]`), `pico/cd/memory.c:1232-1233`. I-MEGADEV `docs/main_bios.md:30`. |
| R-02 | The "128 KiB" hypothesis in `docs/architecture.md` is correct for the ROM **address window and device**. Project policy: emit an image of exactly 131072 bytes, so that no part of the window is left undefined. | **CONFIRMED** (window). The policy is derived from it. | R-01 |
| R-03 | Emulators do not require exactly 128 KiB. GPGX reads up to `sizeof(scd.bootrom)` and accepts any size > 0. PicoDrive truncates larger files to 128 KiB and accepts smaller ones. | **CONFIRMED** (scope: emulator) | E-GPGX `core/loadrom.c:405-420`. E-PICO `pico/cd/mcd.c:34-37`. |
| R-04 | All regional BIOS variants (JP/US/EU) have the same 128 KiB size. | **ESTIMATED** | E-GPGX uses one fixed 128 KB buffer for all three region files (`core/loadrom.c:405-417`, comment "fixed 128KB size"). We found no official per-region size statement. We have no dumps and will not obtain any. |
| R-05 | In Mode 1 (boot from cartridge), the boot ROM appears at `$400000-$41FFFF` and the cartridge at `$000000`. | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1589-1596` (`base` = `0x40`). E-PICO `pico/cd/memory.c:1226`. S-BIOS §4-1 (p.30) describes the Mode 1 boot flow but not the address. S-HW Mode 1 mapping pages were not reviewed. |
| R-06 | Main-CPU `$040000-$1FFFFF` is "reserved by the system". GPGX mirrors the ROM and the PRG-RAM window every 256 KiB up to `$1FFFFF`. PicoDrive maps only `$000000-$01FFFF`. The BIOS must not rely on mirrors. | **UNCONFIRMED** (mirroring) | S-HW §1-3 p.16. E-GPGX `core/cd_hw/scd.c:1596-1642`. E-PICO `pico/cd/memory.c:1232-1233`. See OQ-3. |

## 2. Reset vectors and the exception table (ROM offsets `$000-$0FF`)

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| R-10 | On reset, the 68000 fetches the initial SSP from `$000000` (long) and the initial PC from `$000004` (long). Together with R-01, the Mode 2 main-CPU reset vectors are ROM offsets `0x000-0x007`. | **CONFIRMED** | S-M68K §6.3.1 "Reset" and Table 6-2 "Exception Vector Assignment" (p.6-7). R-01. |
| R-11 | The initial PC must be even. Instruction words are fetched from even addresses, and a word fetch from an odd address raises an address error. | **CONFIRMED** | S-M68K §6.2 (word fetches from odd addresses → address error). |
| R-12 | The initial PC must point into the ROM window: `0x000008 <= PC <= 0x01FFFE`, with the upper byte ignored as the 68000 has a 24-bit bus. At power-on no other memory is guaranteed to contain code. PicoDrive also rejects a ROM loaded as a cartridge if PC >= file size. | **CONFIRMED** (derived) | R-01, R-10. E-PICO `pico/media.c:364-371`. |
| R-13 | The initial SSP should be even and point into Main Work RAM (`$FF0000-$FFFFFF`). A value of `0`, which wraps to the top of RAM, is also common. | **ESTIMATED** (value). Evenness: **CONFIRMED** (derived: stack operations are word/long accesses → S-M68K §6.2). | I-MEGADEV `docs/megacd_dev.md:19-31` (stack conventions) |
| R-14 | The Level 1–7 autovectors are at `$64-$7C`. Level 4 (`$70`) is the VDP H-INT, level 6 (`$78`) the V-INT, level 2 (`$68`) the external port. | **CONFIRMED** (addresses: S-M68K Table 6-2). Level → source: **ESTIMATED**. | S-M68K Table 6-2. I-MEGADEV `lib/main/memmap.def.h:69-74`. |
| R-15 | The Main-CPU vector table in ROM points into a RAM jump table at `$FFFD00+` (6-byte `JMP abs.l` entries), so that software can re-point handlers. Games patch these entries, e.g. V-INT at `$FFFD08`, H-INT at `$FFFD0E`, level 2 at `$FFFD14`. | **ESTIMATED** | I-MEGADEV `docs/megacd_dev.md:7-17`, `lib/main/memmap.def.h:19,68-99`. An official statement was not located among the pages reviewed. |
| R-16 | The H-INT vector **low word** read from `$000072-$000073` is supplied by gate-array register `$A12006`, not by ROM. | **ESTIMATED** | S-HW §4-1 p.56 lists `$A12006` (H-INT) among the Main-CPU registers. E-GPGX `core/mem68k.c:552-556,1267-1270`. E-PICO `pico/cd/memory.c:129-131,235-242`. I-MEGADEV `lib/main/gate_arr.def.h:261-266`. The official page describing `$A12006` bits was not reviewed. |
| R-17 | The H-INT vector **high word** at `$000070-$000071` is handled inconsistently. GPGX forces `$FFFF` at hard reset regardless of ROM content. PicoDrive forces `$FF` bytes only when no cartridge is present, otherwise it uses the ROM bytes. MegaDev says the boot ROM leaves `$00FF`. With a 24-bit bus, `$00FF` and `$FFFF` select the same region. | **UNCONFIRMED** | E-GPGX `core/cd_hw/scd.c:1801-1803`. E-PICO `pico/cd/mcd.c:80-81`. I-MEGADEV `lib/main/gate_arr.def.h:261-262`. See OQ-1. |

## 3. Header area (`$100-$1FF`) and identification bytes

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| R-20 | Some software detects a Mega-CD by reading `"SEGA"` at `$400100`, i.e. ROM offset `$100` while a cartridge is in Mode 1. PicoDrive fakes these bytes for MSU-MD for this reason. | **ESTIMATED** | E-PICO `pico/cd/memory.c:1220-1223` (comment). No official statement found. See OQ-5. |
| R-21 | On TMSS-equipped Mega Drives, it is unknown whether the TMSS boot ROM checks the expansion boot ROM header in Mode 2. GPGX emulates TMSS only for `SYSTEM_MD`, not for Mega-CD. | **UNCONFIRMED** (hardware). **CONFIRMED** (scope: emulator:gpgx). | E-GPGX `core/genesis.c:307-308`. See OQ-6. |
| R-22 | GPGX picks an emulated CD hardware model from the 16 bytes at ROM offset `$120`: `"WONDER-MEGA BOOT"` → Wondermega, `"WONDERMEGA2 BOOT"` → Wondermega M2 / X'Eye, `"CDX BOOT ROM    "` → CDX/Multi-Mega, anything else → default. This changes the emulated CD fader behaviour. | **CONFIRMED** (scope: emulator:gpgx) | E-GPGX `core/loadrom.c:422-442`, `core/cd_hw/scd.c:1492-1527` |
| R-23 | If the BIOS is loaded **as a cartridge**, GPGX treats it as a boot ROM when the header ROM-type field at `$180` contains `"BR"`. PicoDrive does so when the size is ≤ 128 KiB and `"BOOT"` is at `$124` or `$128`. | **CONFIRMED** (scope: emulator) | E-GPGX `core/loadrom.c:48,791-829`. E-PICO `pico/media.c:373-381`. |
| R-24 | Neither emulator checks a header checksum for the boot ROM. GPGX computes one only for display. | **CONFIRMED** (scope: emulator). Hardware: **UNCONFIRMED**. | E-GPGX `core/loadrom.c:279-288`. E-PICO `pico/media.c:256-381` (no checksum use). |
| R-25 | Several commercial games call into a fixed-position Main-CPU jump table at ROM offset `$000280`. Its position is said to be stable across ROM revisions and models. | **ESTIMATED** | I-MEGADEV `docs/main_bios.md:30-44`. This comes from reverse engineering. Not in official manuals (MegaDev notes the official manuals call the area only "for CD-ROM boot"). See OQ-7. |

## 4. Regions and models

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| R-30 | Both emulators choose **which BIOS file** to load from the disc's region byte at disc offset `0x20B` (2048-byte sector data): `0x64` → Europe, `0xA1` → Japan, anything else → USA. The BIOS image itself carries no region marker that the emulator checks. | **CONFIRMED** (scope: emulator) | E-GPGX `core/loadrom.c:1056-1072`. E-PICO `pico/media.c:239-245`. |
| R-31 | The original BIOS compares disc boot data (`$200`–`$783`) against a region-specific copy held in the BIOS before booting. | **ESTIMATED** | I-RHOPE "On the Genesis Side". This is a single independent source, reached over an unverified TLS connection. See OQ-8 (legal/compatibility). |
| R-32 | Model variants exist (Model 1/2, CDX/Multi-Mega, Wondermega, Wondermega M2/X'Eye) with different audio filter hardware. | **ESTIMATED** | E-GPGX `core/cd_hw/scd.h:53-57`, `core/cd_hw/scd.c:1492-1527`. Official model documentation was not reviewed. O-SEGAJP was inaccessible. |

## 5. Boot sequence (Main/Sub CPU startup)

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| B-01 | At power-on, the Sub CPU is held in reset with its bus requested (`$A12001`: SRES=0, SBRQ=1). | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1805-1807,1850-1853`. E-PICO `pico/cd/mcd.c:76-79` (comment "cold reset state (tested)"). S-HW §4-1 p.56 defines SRES/SBRQ but no power-on value was read. |
| B-02 | Mode 2 boot order: the Main CPU starts from the boot ROM, initialises Mega Drive hardware, transfers the CD system program and the CD-BOOT (IP/SP loader) program to the Sub side, then releases Sub-CPU reset. It then waits for the IP, executes it, waits for the application and executes it. Mode 1 follows a similar flow started from the cartridge. | **CONFIRMED** | S-BIOS §4-1/4-2 p.30. I-MEGADEV `docs/boot.md:3`. I-RHOPE "On the Genesis Side". |
| B-03 | The Main CPU can access PRG-RAM through the `$020000-$03FFFF` window only while the Sub CPU is bus-requested or held in reset. | **CONFIRMED** | S-HW §1-3 p.16 and §4-1 p.57 (BK0/1 description). E-GPGX `core/mem68k.c:1085-1116`. E-PICO `pico/cd/memory.c:203-206`. |
| B-04 | The PRG-RAM bank shown in the window is selected by `$A12003` bits 6–7 (BK0/1). | **ESTIMATED** (bit positions) | S-HW p.57 names BK0/1, but the scan's high-byte bit columns are cropped. E-GPGX `core/mem68k.c:1160-1162`. E-PICO `pico/cd/memory.c:215-219`. |
| B-05 | The Sub CPU takes its reset SSP/PC from PRG-RAM `$000000/$000004`. Therefore the boot ROM must contain a Sub-CPU program image, including its vector table, and copy it into PRG-RAM before releasing SRES. | **CONFIRMED** (derived) | S-HW §1-2 p.14 (Sub `$000000-$07FFFF` is program RAM, "transfer a program from the MAIN-CPU"). S-M68K §6.3.1. S-BIOS §1-4 p.4 (vectors at `$000000`). E-GPGX `core/cd_hw/scd.c:1689-1697`. |
| B-06 | PRG-RAM `$00000-$1FDFF` can be write-protected in `$200` units via `$A12002` WP0–7. | **CONFIRMED** | S-HW §1-2 p.14, §4-1 p.57. I-MEGADEV `lib/main/gate_arr.def.h:123-124`. E-GPGX `core/cd_hw/scd.c:1694-1696`. |
| B-07 | Sub-CPU system area layout used by the BIOS and expected by software: vectors `$0000`, CD-BIOS ID `$0100`, CD system program `$0200-$53FF`, work `$5400`, heap/stack `$5C00`, common work `$5E80`, jump table `$5EE0-$5FFF`, user header `$6000`, user program `$6020-$7FFFF`. | **CONFIRMED** | S-BIOS §1-4 "CD System Memory Map" p.4. I-MEGADEV `lib/sub/memmap.def.h:64-95`, `lib/sub/bios.def.h:50-127`, `docs/boot.md:3`, `docs/megacd_dev.md:123`. |
| B-08 | Disc boot (Mode 2): the IP is loaded to Main Work RAM `$FF0000` and executed there; the SP is loaded to PRG-RAM `$6000`. | **ESTIMATED** | I-MEGADEV `docs/boot.md:3`. I-RHOPE. Official S-BIOS §4-3 (pp.31–32) and S-FMT §3-3 (p.7) were not reviewed. |
| B-09 | The disc system area starts with an ID string. PicoDrive recognises `"SEGADISCSYSTEM"` at offset 0 (ISO) or 0x10 (raw BIN). I-RHOPE lists further IDs (`SEGABOOTDISC`, `SEGADISC`, `SEGADATADISC`). | **ESTIMATED** | E-PICO `pico/media.c:220-229`. I-RHOPE "General". S-FMT §3-2 (p.6) not reviewed. See OQ-9. |
| B-10 | The SP begins with a header that names entry points, and the BIOS calls user routines (`usercall0`–`3`: init, main, level-2 handler, user). | **ESTIMATED** | S-BIOS §5-3 p.34 (not reviewed in detail). I-MEGADEV `docs/boot.md` "Special notes about the SP". I-RHOPE "On the Sega CD Side". |

## 6. Emulator vs hardware differences found so far

| Topic | Emulator behaviour | Hardware | Status |
| --- | --- | --- | --- |
| ROM mirroring above `$040000` | GPGX mirrors; PicoDrive does not | Official: "reserved" | UNCONFIRMED (OQ-3) |
| H-INT vector high word | GPGX `$FFFF`, PicoDrive ROM bytes or `$FF` | Unknown | UNCONFIRMED (OQ-1) |
| TMSS with Mega-CD | GPGX does not emulate | Unknown | UNCONFIRMED (OQ-6) |
| Sub access to Word RAM owned by Main (2M) | GPGX stalls the Sub CPU (no /DTACK) | Unknown | UNCONFIRMED (OQ-4) |
| BIOS region selection | Chosen from the disc byte `0x20B` | Fixed by the purchased unit | CONFIRMED (emulator) |
| Model detection | GPGX string at `$120` | Different PCB/filters | CONFIRMED (emulator) |
| RAM at power-on | GPGX clears PRG/Word RAM to 0 (`core/cd_hw/scd.c:1782-1786`) | Not guaranteed | ESTIMATED: the BIOS must initialise all RAM it relies on |
