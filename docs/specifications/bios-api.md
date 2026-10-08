# BIOS-facing interfaces (by public documentation and observed behaviour)

This document describes **interfaces** that software expects from the BIOS. The descriptions come from public or independent documentation, not from any Sega ROM. Implementations must be written independently (see [provenance](../provenance.md)). Labels follow [README.md](README.md).

## 1. Sub-CPU entry points (PRG-RAM jump table)

The official BIOS manual says that applications call the BIOS through a jump table in the common area and by "setting parameters in registers and calling BIOS entries such as `_cdbios` and `_buram`" (S-BIOS §5-1/5-2 p.33). The jump table lies in `$5EE0-$5FFF` (S-BIOS §1-4 p.4). Entry names: **CONFIRMED**. Exact addresses below: **ESTIMATED**. They come from I-MEGADEV only; the official `cabios.i` include file is not available to us.

| Symbol | Address | Purpose | Evidence |
| --- | --- | --- | --- |
| `_SETJMPTBL` | `$5F0A` | Set the user jump table | I-MEGADEV `lib/sub/bios.def.h:92` |
| `_WAITVSYNC` | `$5F10` | Wait for the next level-2 interrupt (Main V-INT) | I-MEGADEV `lib/sub/bios.def.h:97` |
| `_BURAM` | `$5F16` | Backup RAM services | I-MEGADEV `lib/sub/bram.def.h:15` |
| `_CDBOOT` | `$5F1C` | CD boot services | I-MEGADEV `lib/sub/cdboot.def.h:15` |
| `_CDBIOS` | `$5F22` | CD drive / CD-DA / CD-ROM / subcode / fader / LED services | I-MEGADEV `lib/sub/bios.def.h:127` |
| `_USERCALL0`-`3` | `$5F28`, `$5F2E`, `$5F34`, `$5F3A` | User routines the BIOS calls (init, main, level-2, user) | I-MEGADEV `lib/sub/bios.def.h:102-120`, `docs/boot.md` |
| exception jump table | `$5F40-$5FFF` | 6-byte `JMP` entries per exception | I-MEGADEV `lib/sub/memmap.def.h:64-95` |
| `CDSTAT`, `BOOTSTAT`, `INT2FLAG`, `USERMODE` | `$5E80`, `$5EA0`, `$5EA4`, `$5EA6` | BIOS status variables in common work | I-MEGADEV `lib/sub/bios.def.h:50-66` |

**Calling convention (ESTIMATED):** the function code goes in `D0.w`, arguments in `A0`/`A1`/`D1` as each call requires, and the caller uses `JSR` to the entry; results come back in `D0`/`D1`/`A0` and condition codes. Evidence: S-BIOS §5-2 p.33 (registers plus entry call, no register detail on that page), and I-MEGADEV `lib/sub/bram.h:60-145` (inline wrappers) and `lib/sub/cdrom.macro.s:34`.

**Function codes:** I-MEGADEV `lib/sub/bios.def.h` (e.g. `MSC_STOP=$0002`, `DRV_INIT=$0010`, `ROM_READ=$0017`, `CDBCHK=$0080`) and `lib/sub/bram.def.h` (`BRMINIT=$0000` … `BRMVERIFY=$0008`). Status: **ESTIMATED**. The official list is S-BIOS §2-2 "BIOS Call List" pp.7–8 (not reviewed in this PR). MegaDev defines codes `$0011` and `$0012` twice (OQ-12). The full code list will be tracked in a follow-up issue rather than copied here.

## 2. User program interface (SP header and user calls)

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| A-01 | The SP is loaded to `$6000`. Its header (`$6000-$601F`) names the module and points to a table of word offsets for the entry points. | **ESTIMATED** | S-BIOS §1-4 p.4 (user header `$6000`, user program `$6020`: **CONFIRMED** placement). I-RHOPE "On the Sega CD Side". I-MEGADEV `lib/sub/sp_header.s` |
| A-02 | The BIOS calls entry 0 (init) and entry 1 (main) from the boot flow and entry 2 from the level-2 handler. Entry 3 is user-defined. | **ESTIMATED** | I-RHOPE. I-MEGADEV `docs/boot.md` "Special notes about the SP". S-BIOS §5-3 p.34 (not reviewed in detail) |
| A-03 | The IP runs on the Main CPU from `$FF0000`. On commercial discs it begins with a region-specific security block. | **ESTIMATED** | I-RHOPE. I-MEGADEV `docs/boot.md`. OQ-8 |

## 3. Main-CPU interfaces

| ID | Claim | Status | Evidence |
| --- | --- | --- | --- |
| A-10 | The Main-side exception/interrupt jump table at `$FFFD00` (6-byte `JMP` entries, e.g. V-INT pointer at `$FFFD08`) is a compatibility surface that software patches. | **ESTIMATED** | I-MEGADEV `lib/main/memmap.def.h:19,68-99`, `docs/megacd_dev.md:7-31` |
| A-11 | Some commercial titles call a fixed jump table at ROM `$000280` (an undocumented Main-side "boot ROM library"). Supporting those titles requires the same table position and calling semantics. | **ESTIMATED** | I-MEGADEV `docs/main_bios.md:30-44`. OQ-7 (clean-room method) |
| A-12 | Main-side BIOS work variables in `$FFFDB4-~$FFFE58` (VDP register cache, communication-register caches, etc.) are used by that library. Their layout varies by revision. | **ESTIMATED** | I-MEGADEV `docs/megacd_dev.md:23`, `lib/main/bios.def.h:44-146` |

## 4. What we deliberately do not provide

* No reproduction of Sega's security block, logo, CD player or any other ROM content.
* No table or entry ordering derived from disassembling a Sega ROM. Any entry needed for compatibility must come from public documentation, independent documents, or black-box observation under a clean-room protocol (OQ-7).
