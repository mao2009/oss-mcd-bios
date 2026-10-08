# Memory map, registers and interrupts

Conventions follow [README.md](README.md) and [rom-layout.md](rom-layout.md). Register addresses are given exactly; bit layouts appear only where a cited source states them. No register tables are reproduced from the official manuals.

## 1. Main CPU (Mode 2, 2M Word RAM mode)

| Range | Contents | Status | Evidence |
| --- | --- | --- | --- |
| `$000000-$01FFFF` | Boot ROM (128 KiB) | **CONFIRMED** | See R-01 |
| `$020000-$03FFFF` | 128 KiB window into Sub PRG-RAM (bank-selected). Accessible only while the Sub CPU is bus-requested or held in reset. | **CONFIRMED** | S-HW §1-3 p.16, p.57. E-GPGX `core/cd_hw/scd.c:1615-1640`, `core/mem68k.c:1085-1116` |
| `$040000-$1FFFFF` | Reserved by the system (mirroring is emulator-dependent) | **UNCONFIRMED** (contents) | S-HW §1-3 p.16. OQ-3 |
| `$200000-$23FFFF` | Word RAM. 2M mode: 256 KiB. 1M mode: one 128 KiB bank at `$200000-$21FFFF`, plus its cell-image view at `$220000-$23FFFF`. | **CONFIRMED** | S-HW §1-3 p.16. E-GPGX `core/cd_hw/scd.c:1644-1669`. I-MEGADEV `lib/main/memmap.def.h:30-54` |
| `$400000-$7FFFFF` | Cartridge or expansion area (Mode 2: cartridge slot; RAM cartridge/BRAM cart in PicoDrive) | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1593-1594`. E-PICO `pico/cd/memory.c:1242-1248` |
| `$A12000-$A1202F` | Gate-array registers, Main side. GPGX mirrors them up to `$A120FF`. | **CONFIRMED** (base and range). Mirroring: **CONFIRMED** (scope: emulator:gpgx) | S-HW §1-1 p.12 (diagram "MAIN-CPU REGISTER" at `$A12000`), §4 p.56–60. E-GPGX `core/mem68k.c:529-530`. I-MEGADEV `lib/main/gate_arr.def.h:52-511` |
| `$FF0000-$FFFFFF` | Main Work RAM (64 KiB). `$FFFD00-$FFFFFF` is used by the system (exception jump table, BIOS variables). | Work RAM: **CONFIRMED** (S-HW p.12). System-use area: **ESTIMATED** | I-MEGADEV `docs/megacd_dev.md:19-31,65-89`, `lib/main/bios.def.h:44-146` |

### Main-side gate-array registers (addresses only)

| Address | Name | Status | Evidence |
| --- | --- | --- | --- |
| `$A12000` | IEN2 (read) / IFL2 (bit 8: raise Sub level 2) | **CONFIRMED** | S-HW §4-1 p.56. E-GPGX `core/mem68k.c:1137-1151`. E-PICO `pico/cd/memory.c:171-182` |
| `$A12001` | SBRQ (bit 1), SRES (bit 0) | **CONFIRMED** | S-HW §4-1 p.56. E-GPGX `core/mem68k.c:1039-1080` |
| `$A12002-3` | Write protect WP0-7, BK0/1, MODE, DMNA, RET | names: **CONFIRMED**; high-byte bit positions: **ESTIMATED** (scan cropped) | S-HW §4-1 p.57. E-GPGX `core/mem68k.c:1156-1265` |
| `$A12004` | CDC mode (Main view) | **ESTIMATED** | E-GPGX `core/mem68k.c:568-572`. S-HW §4-2 p.58 not reviewed |
| `$A12006` | H-INT vector low word | **ESTIMATED** | See R-16 |
| `$A12008` | CDC host data | **ESTIMATED** | E-GPGX `core/mem68k.c:541-550,1273-1278` |
| `$A1200C` | Stopwatch | **ESTIMATED** | E-GPGX `core/mem68k.c:558-566` |
| `$A1200E` | Communication flags (Main writes the high byte) | **ESTIMATED** | E-GPGX `core/mem68k.c:1280-1287` |
| `$A12010-$A1201F` | Main→Sub command words (read-only from the Sub side) | **ESTIMATED** | E-GPGX `core/mem68k.c:1291-1297`, `core/cd_hw/scd.c:1567-1572`. I-MEGADEV `lib/main/gate_arr.def.h:346-423` |
| `$A12020-$A1202F` | Sub→Main status words | **ESTIMATED** | E-GPGX `core/mem68k.c:575-586`. I-MEGADEV `lib/main/gate_arr.def.h:434-511` |

The official manual describes a "forced reset" command pattern that initialises the gate array (S-HW §4-1 p.56). Whether and when the BIOS must issue it is **UNCONFIRMED**. We do not reproduce the pattern here (OQ-10).

## 2. Sub CPU

| Range | Contents | Status | Evidence |
| --- | --- | --- | --- |
| `$000000-$07FFFF` | PRG-RAM, 512 KiB. Sub reset vectors and the BIOS system area are at the bottom (see B-07). | **CONFIRMED** | S-HW §1-2 p.14. S-BIOS §1-4 p.4. E-GPGX `core/cd_hw/scd.c:1680-1698` |
| `$080000-$0BFFFF` | Word RAM, 2M mode (256 KiB). In 1M mode this range holds the "dot image" (decoded 4bpp view). | **CONFIRMED** | S-HW §1-2 p.14. E-GPGX `core/cd_hw/scd.c:1700-1725` |
| `$0C0000-$0DFFFF` | Word RAM, 1M mode bank; not assigned in 2M mode | **CONFIRMED** | S-HW §1-2 p.14. I-MEGADEV `lib/sub/memmap.def.h:56-62` |
| `$FE0000-$FE3FFF` | Backup RAM, 8 KiB on odd addresses only | **CONFIRMED** | S-HW §1-1 p.12 (diagram). E-GPGX `core/cd_hw/scd.h:77`, `core/cd_hw/scd.c:1751-1760` |
| `$FF0000-$FF7FFF` | PCM sound source (8-bit device on odd addresses) | **CONFIRMED** | S-HW p.12. I-RHOPE "PCM Chip" |
| `$FF8000-$FF81FF` | Sub-side gate-array registers | **CONFIRMED** | S-HW p.12, §3 pp.22–55. E-GPGX `core/cd_hw/scd.c:1762-1771` |
| Address mirroring every 1 MiB (only A1–A19 decoded) | Emulator implementation | **CONFIRMED** (scope: emulator:gpgx). Hardware: **UNCONFIRMED** | E-GPGX `core/cd_hw/scd.c:1675-1678` |

### Sub-side registers used during boot (addresses only)

| Address | Purpose | Status | Evidence |
| --- | --- | --- | --- |
| `$FF8000-1` | LED / reset status | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:826-843,1185-1197` |
| `$FF8002-3` | Memory mode (Sub view) | **CONFIRMED** (existence) | S-HW §1-2 p.14 references `$FF8002`. E-GPGX `core/cd_hw/scd.c:1199` |
| `$FF8004-7` | CDC mode / register address / data | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1044-1073,1398-1421` |
| `$FF800E-F` | Communication flags (Sub writes the low byte) | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1440-1447` |
| `$FF8030` | General-purpose timer: level 3 every (n+1) × 30.72 µs; writing 0 stops it | **CONFIRMED** | S-HW §3-4 p.30. E-GPGX `core/cd_hw/scd.h:59-67` (1536 clocks at 50 MHz = 30.72 µs), `core/cd_hw/scd.c:1449-1471` |
| `$FF8032` | Interrupt mask IEN1–IEN6 | **CONFIRMED** | S-HW §3-5 p.30. E-GPGX `core/cd_hw/scd.c:1473-1490` |
| `$FF8036-7` | CDD control (HOCK etc.) | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1532-1537,1944-1956` |
| `$FF8038-$FF8041` | CDD status (10 nibbles) | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1545` |
| `$FF8042-$FF804B` | CDD command; a write to `$FF804A` sends it | **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:1539-1548` |
| `$FF8058-$FF8066` | Graphics (stamp rotation) operation; a write to `$FF8066` starts it | **ESTIMATED** | S-HW §1-2 p.14 (range). E-GPGX `core/cd_hw/scd.c:1550-1557` |

## 3. Word RAM ownership

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| W-01 | At power-on, Word RAM is in 2M mode and assigned to the Main CPU. | **CONFIRMED** | S-HW §1-3 p.16 (on power-on the Word RAM is attached to the Main side in this mode). E-GPGX `core/cd_hw/scd.c:1809-1821`. E-PICO `pico/cd/mcd.c:79` |
| W-02 | 2M mode: the Main CPU writes DMNA=1 to give Word RAM to the Sub CPU; the Sub returns it via RET. 1M mode: the two 128 KiB banks are swapped by request. Writing 0 to DMNA in 1M mode requests the swap. | **CONFIRMED** | S-HW §4-1 p.57 (DMNA/RET semantics). E-GPGX `core/mem68k.c:1164-1265`. E-PICO `pico/cd/memory.c:221-233` |
| W-03 | A Sub-CPU access to 2M Word RAM while the Main CPU owns it stalls (no /DTACK) until ownership changes. | **CONFIRMED** (scope: emulator:gpgx). Hardware: **UNCONFIRMED** | E-GPGX `core/cd_hw/scd.c:1716-1723,1823-1830`. OQ-4 |

## 4. Interrupts

### Sub CPU (autovectored)

| Level | Source | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Graphics (stamp) operation complete, 2M mode | **CONFIRMED** | S-HW §3-5 p.30. E-GPGX `core/cd_hw/gfx.c:727-731` |
| 2 | Software interrupt from the Main CPU (IFL2). Official advice: issue it from the Main V-INT for synchronisation. | **CONFIRMED** | S-HW §3-5 p.30, §4-1 p.56. E-GPGX `core/mem68k.c:1137-1151` |
| 3 | Timer (`$FF8030`) | **CONFIRMED** | S-HW §3-4/3-5 p.30. E-GPGX `core/cd_hw/scd.c:1959-1981` |
| 4 | CDD status reception complete (75 Hz while CDD communication is enabled) | **CONFIRMED** (source). Rate: **ESTIMATED** | S-HW §3-5 p.30. E-GPGX `core/cd_hw/scd.c:1934-1957` |
| 5 | CDC (decode/transfer) | **CONFIRMED** | S-HW §3-5 p.30. E-GPGX `core/cd_hw/cdc.c:301-305` |
| 6 | Subcode buffering complete | **CONFIRMED** | S-HW §3-5 p.30. E-GPGX `core/cd_hw/cdd.c:1784-1788` |
| Acknowledge | Autovector; acknowledging level 2 clears IFL2 | **CONFIRMED** (scope: emulator:gpgx). Hardware: **ESTIMATED** | E-GPGX `core/cd_hw/scd.c:2363-2382` |

The Sub-side exception handlers are routed through a RAM jump table at `$5F40-$5FFF` (6-byte entries). This is **ESTIMATED**, from I-MEGADEV `lib/sub/memmap.def.h:64-95` and `docs/megacd_dev.md:13`, and is consistent with the S-BIOS §1-4 jump-table range `$5EE0-$5FFF`.

### Main CPU

V-INT (level 6) and H-INT (level 4) come from the VDP, and level 2 from the external port. See R-14 to R-17. Status: **ESTIMATED** for the Mega-CD-specific routing.

## 5. CDC / CDD summary

* CDC: a Sanyo LC8951-compatible decoder is emulated by both emulators (E-GPGX `core/cd_hw/cdc.c`, E-PICO `pico/cd/cdc.c`). Chip identity: **ESTIMATED** (S-HW §3-2 pp.26–27 not reviewed).
* CDD: a nibble-serial command/status protocol through `$FF8038-$FF804B`, at 75 Hz. E-GPGX `core/cd_hw/cdd.c` implements the command codes (e.g. `case 0x00` Get Drive Status at `cdd.c:2035`). Status: **ESTIMATED** (S-HW §3-6 pp.31–33 not reviewed). Because the original BIOS drives the CDD directly, our BIOS must implement this protocol (OQ-11).
