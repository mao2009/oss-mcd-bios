# Coverage audit: BIOS API, jump tables, calling conventions (prefix `API-`)

Audit-Agent C, branch `audit/c-bios-api`, based on `origin/agent-a/issue-1-rom-layout` (`c2abc36`). Research and documentation only. Nothing here is an implementation basis until a maintainer resolves OQ-7 and OQ-19 ([open-questions.md](../open-questions.md)).

**Question:** can public, independent material specify the BIOS API well enough to build a compatible BIOS without the original BIOS? The central legal issue is where each piece of API knowledge comes from. The audit therefore records, for every item, *how* the knowledge was obtained.

## 0. Sources examined in this audit

These add to the register in [README.md](../README.md). All clones are shallow (`--depth 1`) and kept in a session scratchpad outside the repository. **No code or text was copied into this repository.** Facts are paraphrased and addresses or numbers are quoted as facts.

| ID | Source | Commit / version | Licence | Class |
| --- | --- | --- | --- | --- |
| I-MEGADEV (MD) | <https://github.com/drojaazu/megadev> | `7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef` (2026-05-10) | MIT | independent SDK, partly reverse-engineered |
| E-CLOWN (CL) | <https://github.com/mao2009/clownmdemu-core> (fork of `Clownacy/clownmdemu-core`) | `15c6cba32bdaab3320056ff762e159951f85367a` (2026-06-07) | AGPL-3.0 (`LICENCE.txt`). **Cite only.** | emulator with **HLE BIOS calls** (runs software without a Sega ROM) |
| I-MCDBOOT (MB) | <https://github.com/kirisamemofo/clownmdemu-mcd-boot> (author commits: devon-artmeier) | `6025457901814d3ec56e349866b691eb588c8e07` (2026-01-27) | 0BSD, "Copyright (c) 2025 Devon Artmeier and Clownacy" | **independent replacement boot ROM** (assembly source). Its binary is embedded in E-CLOWN `source/mega-cd-boot-rom.c`. |
| I-MODE1 (M1) | <https://github.com/kirisamemofo/mega-cd> (GitHub redirect from `devon-artmeier/mcd-mode-1-library`) | `74aa087ab25d2011853edd906fbda34161e48306` (2026-09-13) | 0BSD, "Copyright (c) 2024-2026 Devon Artmeier" | independent Mode-1 loader library |
| E-GPGX-F | <https://github.com/mao2009/Genesis-Plus-GX> | `87dd8b80802ff5217ab2f765202b6b14ecd23f94` (2026-08-21) | non-commercial. **Cite only.** | emulator (LLE, needs a real BIOS) |
| E-PICO | <https://github.com/notaz/picodrive> | `26ecb2b6358fefba24e3d68b9eb2efba7f10d5ee` (2025-04-03) | non-commercial. **Cite only.** | emulator (LLE, needs a real BIOS) |
| S-BIOS-TOC | Table of contents of the *Mega-CD BIOS Manual* scan, <https://www.megadrive.org/elbarto/megacd/Official%20Sega%20CD%20Manual/segacd_toc.html> | Ver 2.00 Feb. 24 '92 | **CONFIDENTIAL / PROPERTY OF SEGA. Excluded basis (Issue #17).** TOC read only, to list leads. | official (excluded) |
| O-SEGAJP | <https://www.sega.jp/history/hard/mega-cd/> | n/a | n/a | **Retried 2026-10-08 (WebFetch): HTTP 403 again.** Content not verified. |

Citations of `I-*`/`E-*` resolve as `<repo>/blob/<commit>/<path>#L<line>`. For example, `MD lib/sub/bios.def.h:228` = <https://github.com/drojaazu/megadev/blob/7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef/lib/sub/bios.def.h#L228>. A path:line with no prefix in a cell refers to the source named first in that cell.

### 0.1 How the existing BIOS-API knowledge was obtained (provenance classes)

| Code | Meaning | Where it appears |
| --- | --- | --- |
| **P-OFF** | Comes from the CONFIDENTIAL Sega manuals or Tech Bulletins. **Excluded as a basis.** | MegaDev says the Sub-side calls are "well-documented within the official Sega documentation" (`docs/main_bios.md:12`). MegaDev cites Tech Bulletins #1 and #3 (`lib/sub/bram.def.h:112`, `docs/main_bios.md:50-77`, `lib/main/bios.def.h:1393`). CL cites "Sega's developer documentation" (`source/bus-sub-m68k.c:559`). |
| **P-RE** | Comes from disassembling a Sega ROM. Conflicts with provenance rule 1 unless a clean-room protocol is approved (OQ-7). | MegaDev Main-side library: "only understood from reverse engineering" (`docs/main_bios.md:12,104,218-220`; `docs/megacd_dev.md:51`). MegaDev Sub side also cites "the disassemblies checked so far" (`lib/sub/bios.def.h:386-388`) and "per the documentation and disassemblies" (`new_project/src/sp.s:40`). |
| **P-UNK** | Origin not declared. Matches the original closely enough that RE is likely (ESTIMATED). | MB. Its Main `$280` table has 72 named entries, including original quirks such as an "unknown and bugged copy" entry (`src/main/function_table.asm:55`) and "Sega's BIOS loads a font and logo…" (`src/main/splash.asm:19-21`). |
| **P-BB** | Black-box behaviour: an implementation tested against existing software **without** a Sega ROM, or measured. | CL HLE traps. Values are tuned until named games run: "enough to get Popful Mail to boot" (`source/bus-sub-m68k.c:155`), "Sonic Megamix 4.0b relies on this" (`:229`). The author marks them "None of this … is accurate" (`:66`, `:715`) and refers to forum notes by Devon whose origin is unknown (`:67-68`). |
| **P-USE** | What callers do, read from public homebrew source. | MegaDev lib and examples (`lib/sub/cdrom.s`, `examples/*/src/sp.s`), M1. |

**Bottom line on sourcing.** For **every** Sub-side function code and register convention, the public chain of knowledge leads back to P-OFF (the leaked BIOS manual) and/or P-RE. No source in this audit derived the Sub-side API from black-box observation alone. The Main `$280` library is P-RE (MegaDev) or P-UNK (MB). CL is the only P-BB evidence, and it covers a subset with admitted inaccuracy.

The interface facts can be re-derived legally:
- addresses, function numbers and register roles, by observing **callers** (E1);
- semantics, by black-box probing of a console's own BIOS in place (E2–E6).

That re-derivation is the recommended path to a clean provenance chain. **New prior art:** MB is a 0BSD, independently written replacement boot ROM that runs commercial software in CL. However, its Sub-side `_CDBIOS`/`_BURAM`/`_CDBOOT` slots are bare `rts` stubs (`src/sub/call_table.asm:35-59`), and CL does the actual work in C traps (AGPL). So no complete, permissively licensed, independently written Sub BIOS was found in the sources examined.

## 1. Enumerated required behaviours

Levels: **LA** = minimal BIOS boot; **LB** = boot a homebrew CD program (MegaDev-class); **LC** = commercial-game-compatible BIOS. An item tagged LB is also required for LC. "LB/LC" means the basic form is needed for LB and the full form for LC.

### A. Sub-CPU jump table, entry points, dispatch
- **API-01** (LB) Fixed Sub-side system jump table in PRG-RAM `$5F00-$5FFF`, made of 6-byte `JMP abs.l` slots.
- **API-02** (LB) `_SETJMPTBL` (`$5F0A`) parses the module header (name check, flag byte, offset to the word-offset list, linked modules) and installs JMP slots. Used internally for the SP; callers may use it for overlays.
- **API-03** (LB) `_WAITVSYNC` (`$5F10`) waits for the next level-2 interrupt.
- **API-04** (LB) `_BURAM` (`$5F16`) is the Backup-RAM dispatcher (code in `D0.w`).
- **API-05** (LC) `_CDBOOT` (`$5F1C`) is the CD-boot service dispatcher.
- **API-06** (LB) `_CDBIOS` (`$5F22`) is the CD-BIOS dispatcher (code in `D0.w`).
- **API-07** (LB) `_USERCALL0`-`3` (`$5F28/$5F2E/$5F34/$5F3A`) are filled from the SP header's word-offset table.
- **API-08** (LB) Sub exception/interrupt slots `$5F40-$5FFF` (address error ... level 1-7 ... TRAP #15): fixed order, safe defaults.
- **API-09** (LB) The Sub hardware vector table (PRG-RAM `$000000-$0000FF`) points into the slots.
- **API-10** (LB) Calling convention: `JSR` to the entry; code in `D0.w`; inputs in `D1/A0/A1`; outputs in `D0/D1/A0/A1` and carry; a fixed clobber set per call.
- **API-11** (LB) Reentrancy and context rules: which calls are legal from `USERCALL2` or other interrupt context.
- **API-12** (LB) The level-2 handler runs BIOS periodic work, sets `INT2FLAG`, then calls `USERCALL2`.
- **API-13** (LB) The BIOS owns level-4 (CDD) and level-5 (CDC) interrupt processing.
- **API-14** (LB) Sub boot sequence: install tables and the SP module, call `USERCALL0` with IRQs masked, then loop on `USERCALL1`. Handle the return code.
- **API-15** (LB) Sub stack location and CPU mode at user-call entry (`USERMODE`).
- **API-16** (LB) Common work variables: `CDSTAT` `$5E80`, `BOOTSTAT` `$5EA0`, `INT2FLAG` `$5EA4`, `USERMODE` `$5EA6`.
- **API-17** (LB) PRG-RAM `$000000-$005FFF` is reserved to the BIOS. The user area starts at `$6000`.
- **API-18** (LB) Unknown or unimplemented function codes return safely.

### B. `_CDBIOS` functions
- **API-20** (LB) `DRV_INIT` `$10`: read the TOC. The argument is a 2-byte list (first track, last track). Bit 7 of the first byte = auto-play.
- **API-21** (LC) `DRV_OPEN` `$0A`: open the tray.
- **API-22** (LB) `CDBCHK` `$80`: carry = busy.
- **API-23** (LB/LC) `CDBSTAT` `$81`: returns a pointer to the status structure. LB needs only the upper nibble of `CDSTAT` (0 = idle). LC needs every field.
- **API-24** (LC) `CDBTOCWRITE` `$82`.
- **API-25** (LC) `CDBTOCREAD` `$83`: track in `D1.w` -> BCD time and track in `D0.l`, type in `D1.b`.
- **API-26** (LC) `CDBPAUSE` `$84`: pause-to-standby delay in 1/75-second ticks.
- **API-27** (LC) `MSC_STOP` `$02`.
- **API-28** (LC) `MSC_PAUSEON`/`MSC_PAUSEOFF` `$03/$04`.
- **API-29** (LC) `MSC_SCANFF`/`MSC_SCANFR`/`MSC_SCANOFF` `$05-$07`.
- **API-30** (LC) `MSC_PLAY`/`PLAY1`/`PLAYR` `$11-$13` (play all / once / repeat). This is the usual CD-DA music path.
- **API-31** (LC) `MSC_PLAYT` `$14`, `MSC_SEEK` `$15`, `MSC_SEEKT` `$16`, `MSC_SEEK1` `$19`.
- **API-32** (LB/LC) `ROM_READN` `$20` (start, count) for LB. `ROM_READ` `$17`, `ROM_SEEK` `$18`, `ROM_READE` `$21` (start, end) for LC.
- **API-33** (LC) `ROM_PAUSEON`/`OFF` `$08/$09`.
- **API-34** (LC) Undocumented or contested codes: `$00`, `$01`, `$0B-$0F`, `$1A-$1F`, and the `$11/$12` double naming (OQ-12).
- **API-35** (LC) `FDR_SET` `$85` (bit 15 = master volume) and `FDR_CHG` `$86` (target volume and ramp).
- **API-36** (LB) `CDC_START` `$87` and `CDC_STOP` `$89`. `CDC_STARTP` `$88` is LC.
- **API-37** (LB) `CDC_STAT` `$8A`, `CDCREAD` `$8B` (header time and mode in `D0`), `CDC_TRN` `$8C` (`0x920`-byte sector + 4-byte header; advances `A0/A1`), `CDC_ACK` `$8D`.
- **API-38** (LC) `CDCSETMODE` `$96`.
- **API-39** (LC) Subcode calls `$8E-$94` (`SCDINIT` work area `0x750` bytes, flags, P/Q and R-W reads).
- **API-40** (LB/LC) `LEDSET` `$95`: modes 0-7 plus "return to system".
- **API-41** (LC) `WONDERREQ`/`WONDERCHK` `$97/$98`.
- **API-42** (LB) Asynchronous command model: progress is driven by INT2 ticks. `CDSTAT` nibble codes mean ready, busy or error.
- **API-43** (LB) Error and return codes for each call (carry, numeric codes), including the no-disc and not-ready paths.
- **API-44** (LC) CDC pre-seek: data starts 2-4 sectors early, and the caller filters by header.
- **API-45** (LC) Timing: command latency, INT2 ticks to completion, 75 sectors/s, default standby delay.
- **API-46** (LB) Mode-1/Mode-2 sector header and size contract seen by the user.

### C. `_BURAM` and the media format
- **API-50** (LB/LC) `BRMINIT` `$00`: `0x640` work buffer and 12-byte string buffer. Returns size in `D0`, status in `D1`, and carry.
- **API-51** (LC) `BRMSTAT` `$01`.
- **API-52** (LC) `BRMSERCH` `$02`.
- **API-53** (LB/LC) `BRMREAD` `$03`.
- **API-54** (LB/LC) `BRMWRITE` `$04`: 14-byte file-info structure. A block is `0x40` bytes normally and `0x20` bytes in protect mode. `D1` is 0.
- **API-55** (LC) `BRMDEL` `$05`.
- **API-56** (LC) `BRMFORMAT` `$06`.
- **API-57** (LC) `BRMDIR` `$07`: pattern with `*`, skip/size argument in `D1`, 16-byte entries.
- **API-58** (LC) `BRMVERIFY` `$08`.
- **API-59** (LC) Codes `$09`, `$0A`.
- **API-60** (LC) On-media format of the internal 8 KiB BRAM and the RAM cartridge: trailer, directory, allocation, protect encoding.
- **API-61** (LC) File-name rules: 11 characters, character set, terminator.
- **API-62** (LC) RAM-cartridge BRAM detection and size.
- **API-63** (LC) BRAM display strings and the "other format" status.

### D. `_CDBOOT`
- **API-65** (LC) `CBTINIT`...`CBTCHKSTAT` `$00-$05` (`CBTINT` every 16.6 ms; `CBTCHKDISC` work area `0x800`; disc-type codes `$FF`, `$00-$07`).
- **API-66** (LC) `CBTIPDISC`/`CBTIPSTAT`/`CBTSPDISC`/`CBTSPSTAT` `$06-$09`.

### E. Boot hand-off and IP/SP loading
- **API-70** (LB) Read the boot sector header IP/SP offset and length fields. Load the IP to Main `$FF0000` and the SP to PRG-RAM `$6000`.
- **API-71** (LB) Security block / region check before the IP runs (policy, OQ-8).
- **API-72** (LB) Word RAM mode and owner at hand-off.
- **API-73** (LB) Main CPU state at IP entry (SP, SR, registers; OQ-2).
- **API-74** (LB) IFL2 (Sub INT2) must be raised every Main V-INT to drive the Sub BIOS. Who does it by default?
- **API-75** (LB) Communication registers are cleared at boot.
- **API-76** (LC) Mode-1 discoverability:
  - Main ROM header has `"SEGA"` at `$100` and `"BR"` at `$180`.
  - A Kosinski-compressed Sub BIOS sits at `$15800`, `$16000` or `$1AD00`.
  - `"SEGA"` (or `"WONDER"`) appears at image offset `+$6D`.
- **API-77** (LC) A Mode-1-decompressed Sub BIOS self-starts and accepts a cart-supplied SP at `$6000`.

### F. Main-CPU side
- **API-80** (LB) ROM exception vectors point at the Work-RAM slot table at `$FFFD00`, with a fixed slot order (V-INT slot `$FFFD08`).
- **API-81** (LB) Slots `$FFFD00-$FFFDB3` hold safe defaults. Software patches the long at slot+2.
- **API-82** (LC) Fixed Main jump table at ROM `$000280`: 73 four-byte entries (`$280-$3A3`), stable order across models.
- **API-83** (LC) `$280` system group: reset paths, control panel.
- **API-84** (LC) V-INT handler, V-INT wait, flags, user V-INT hook.
- **API-85** (LC) Controller input and detection.
- **API-86** (LC) VDP utilities, default registers, fixed VRAM layout, DMA (including the Word-RAM source), DMA queue.
- **API-87** (LC) Palette cache, CRAM update flag, fades.
- **API-88** (LC) Nemesis/Enigma decompression.
- **API-89** (LC) Sprite-object ("entity") system.
- **API-90** (LC) Built-in 1bpp font, font loading and print.
- **API-91** (LC) PRNG.
- **API-92** (LC) Main-side comm sync, CD-info and Sub-BIOS proxy calls, plus the predefined comm-flag protocol the Sub side must honour.
- **API-93** (LC) BCD and time-code arithmetic.
- **API-94** (LC) Main work-area layout: `$FFF700-$FFFBFF` and `$FFFDB4-~$FFFE58`.
- **API-95** (LC) Residual VRAM/VDP/palette state that software relies on at IP entry (font and logo tiles).
- **API-96** (LC) Return-to-BIOS / control-panel path.

### G. Variants
- **API-98** (LC) Model and region variants of the API (Wondermega, LaserActive, CDX, Model 1/2, JP/US/EU).
- **API-99** (LC) Region-dependent behaviour visible through the API (for example default VDP registers).
## 2. Coverage table

Source abbreviations are defined in §0. "Excl." means the only coverage is excluded (P-OFF) material. Column 7 answers whether the item can be implemented from public, non-excluded material: **Y** = defined and clean enough to use. **Cond** = public material defines it, but its origin is P-OFF/P-RE (or a policy decision is pending), so it must be re-derived or approved first. **N** = no adequate non-excluded definition.

| ID | Required behavior | Level | Existing material (Y/N/partial) | Exact reference URL + location | Provenance & usage terms | Implementable from public material only? (Y/Cond/N + why) | Specific missing information | Coverable by own test? | Verifiable in emulator only? | Real hardware needed? | Blocker? (Y/N + why) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API-01 | Sub jump table `$5F00-$5FFF`, 6-byte JMP slots | LB | Y | MD `lib/sub/bios.def.h:92-127`, `lib/sub/memmap.def.h:64-95`. MB `src/sub/call_table.asm:35-59`. CL `source/bus-sub-m68k.c:712,882` (traps at PC `$5F16`/`$5F22`) | MD P-OFF/P-RE (MIT). MB P-UNK (0BSD). CL P-BB (AGPL, cite only) | Cond: 3 public sources agree; origin P-OFF/P-RE; re-derive via E1 | Use of `$5F00-$5F09` | Y | Y (E1) | N (E2 to confirm) | N |
| API-02 | `_SETJMPTBL` module parsing/installation | LB | Y | MD `lib/sub/bios.def.h:68-92`, `lib/sub/sp_header.s:9-25`. MB `src/sub/module.asm:16-78` | MD text is disassembly-style ("it looks like ...") = P-RE. MB P-UNK | Cond: header shape also recoverable from homebrew SP headers (P-USE) | Accepted name strings (MD lists 4); meaning of version/type fields | Y | Y | N | N |
| API-03 | `_WAITVSYNC` waits for INT2 | LB | Y | MD `lib/sub/bios.def.h:94-97`; used `lib/sub/cdrom.s:42`. MB `src/sub/variables.inc:26` | P-OFF + P-USE | Cond: simple, black-box testable | Behaviour without INT2; preserved registers | Y | Y | N | N |
| API-04 | `_BURAM` dispatcher | LB | Y | MD `lib/sub/bram.def.h:11-15`. CL `source/bus-sub-m68k.c:712-881` | P-OFF (MD), P-BB (CL) | Cond | - | Y | Y | N | N |
| API-05 | `_CDBOOT` dispatcher | LC | partial | MD `lib/sub/cdboot.def.h:11-15` | P-OFF | Cond: address only | Whether commercial titles call it: not found in the sources examined | Y | partial (no HLE in CL) | Y (E2) | N |
| API-06 | `_CDBIOS` dispatcher, `D0.w` code | LB | Y | MD `lib/sub/bios.def.h:123-127`, `lib/sub/sub.macro.s:32-34` (`BIOSCALL` macro). CL `source/bus-sub-m68k.c:64-71,882-888` | P-OFF/P-RE (MD), P-BB (CL) | Cond | Effect of a non-zero high word in `D0` | Y | Y | N | N |
| API-07 | USERCALL0-3 from the SP header | LB | Y | MD `lib/sub/bios.def.h:99-121`, `docs/boot.md:17-26`, `lib/sub/sp_header.s:20-25`. MB `src/sub/main.asm:58-69` | MD cites "Sections 4 and 5 of the BIOS Manual" = P-OFF. MB P-UNK | Cond | Terminator rule of the offset list; modules with fewer than 4 entries | Y | Y | N | N |
| API-08 | Sub exception slots `$5F40-$5FFF`, order and defaults | LB | Y | MD `lib/sub/memmap.def.h:64-95`. MB `src/sub/call_table.asm:35-59` | P-OFF/P-RE (MD), P-UNK (MB) | Cond: order agreed by 2 sources; defaults are a design choice | Original default handler behaviour | Y | Y | Y (E6) | N |
| API-09 | Sub hardware vectors point into the slots | LB | partial | MD `docs/megacd_dev.md:9-17` | P-RE | Y: follows by design from API-08 | - | Y | Y | N | N |
| API-10 | Register convention, clobbers, carry | LB | Y | MD `@clobber`/`@param` tags, `lib/sub/bios.def.h:143-720`, `lib/sub/bram.def.h:17-187`. CL carry handling `source/bus-sub-m68k.c:146-149,216-223,745-870` | P-OFF/P-RE. MD notes a mismatch between the "documentation" and the disassembly (`bios.def.h:386-388`) | Cond: confirm by E2 register-diff | Exact clobber set for each call; meaning of N/Z/V | Y | partial | Y (E2) | N |
| API-11 | Calls legal from interrupt or USERCALL2 context | LB | N | Not found in the sources examined (MD, CL, MB, M1, E-GPGX-F, E-PICO) | Excl. (S-BIOS §5-3/5-4, TOC pp.33-35) | N | Reentrancy rules | partial | partial | Y | N for LB (homebrew calls from USERCALL1). Robustness risk for LC |
| API-12 | Level-2 handler: BIOS work, `INT2FLAG`, USERCALL2 | LB | partial | MD `lib/sub/bios.def.h:52-55`. MB `src/sub/interrupt.asm` (own design) | P-OFF/P-UNK | Cond | Ordering; `INT2FLAG` value convention | Y | Y | Y (E2) | N |
| API-13 | BIOS handles level 4/5 (CDD/CDC) | LB | partial | MB `src/sub/main.asm:56`. E-GPGX-F `core/cd_hw/cdd.c:1956` ("BIOS hangs otherwise") | P-UNK; emulator comment (cite only) | Cond: the CDD protocol is a memory-map/CDD item (OQ-11) | How CDD status reaches `CDSTAT` | partial | partial | Y | N |
| API-14 | Sub boot sequence, USERCALL0/1 loop | LB | partial | MD `docs/boot.md:17-26`. MB `src/sub/main.asm:21-72` | P-OFF (manual §4-5), P-UNK | Cond | USERCALL1 return-code semantics; BIOS work between iterations | Y | Y | Y (E2) | N |
| API-15 | Stack and CPU mode at user entry | LB | partial | MD `lib/sub/bios.def.h:57-60`. MB `src/sub/variables.inc:23-24` (stack `$5D80-$5E80`) | P-OFF/P-UNK | Cond | Encoding of `USERMODE`; original stack top | Y | partial | Y (E2) | N |
| API-16 | `CDSTAT`/`BOOTSTAT`/`INT2FLAG`/`USERMODE` addresses | LB | Y | MD `lib/sub/bios.def.h:47-66`; used `examples/hello_world/src/sp.s:17-20`. CL uses a different status address and says "Find the address that a real BIOS uses" (`source/bus-sub-m68k.c:153-171`) | P-OFF + P-USE; CL P-BB | Cond | Full `BOOTSTAT` encoding | Y | Y | N | N |
| API-17 | `$0000-$5FFF` reserved, user from `$6000` | LB | Y | MD `docs/boot.md:3`, `docs/megacd_dev.md:123`. MB `src/sub/main.asm:42-50`. CL `source/clownmdemu.c:498,527` | P-OFF/P-UNK/P-BB, consistent | Y: implied by every SP | - | Y | Y | N | N |
| API-18 | Unknown codes return safely | LB | partial | CL `source/bus-sub-m68k.c:326-328,875-880` | P-BB | Y: design choice | What the original does | Y | Y | N | N |
| API-20 | `DRV_INIT` | LB | Y | MD `lib/sub/bios.def.h:215-228`; used `new_project/src/sp.s:40-47`, `examples/hello_world/src/sp.s:17` | P-OFF/P-RE + P-USE | Cond | Completion signalling; auto-play behaviour | Y | partial (CL has no `$10` HLE) | Y (E5) | N |
| API-21 | `DRV_OPEN` | LC | partial | MD `lib/sub/bios.def.h:207-213` | P-OFF | Cond | Status and timing while the tray is open | Y | N | Y | N |
| API-22 | `CDBCHK` | LB | Y | MD `lib/sub/bios.def.h:367-376`. CL `source/bus-sub-m68k.c:146-149` | P-OFF/P-BB | Cond | - | Y | Y | N | N |
| API-23 | `CDBSTAT` status structure | LB/LC | partial | MD `lib/sub/bios.def.h:378-390` (pointer only). CL placeholder `source/bus-sub-m68k.c:151-172`. Nibble polling `new_project/src/sp.s:46-47` | P-OFF. CL fields are guesses (P-BB, "placeholder which is enough to get Popful Mail to boot") | Cond for LB (only "upper nibble 0 = idle" is needed). **N for LC**: no field-level non-excluded spec | Every field, status codes, update timing | Y | partial | Y (E2/E5) | **Y (LC)**: games read the fields; CL needed a game-specific placeholder |
| API-24 | `CDBTOCWRITE` | LC | partial | MD `lib/sub/bios.def.h:392-406` (refers to "the BIOS manual") | P-OFF | Cond | Entry count, terminator | Y | N | Y | N |
| API-25 | `CDBTOCREAD` | LC | Y | MD `lib/sub/bios.def.h:408-420`. CL incomplete `source/bus-sub-m68k.c:174-179` | P-OFF/P-BB | Cond | Error path for an invalid track | Y | partial | Y | N |
| API-26 | `CDBPAUSE` | LC | Y | MD `lib/sub/bios.def.h:422-434` | P-OFF | Cond | Default delay; actual drive effect | partial | N | Y. **Never test `$FFFF`**: MD warns it can damage the drive | N |
| API-27 | `MSC_STOP` | LC | Y | MD `lib/sub/bios.def.h:143-149`. CL `source/bus-sub-m68k.c:73-80` (implemented as pause, TODO) | P-OFF/P-BB | Cond | Observable difference between stop and pause | Y | partial | Y | N |
| API-28 | `MSC_PAUSEON/OFF` | LC | Y | MD `lib/sub/bios.def.h:159-165`. CL `source/bus-sub-m68k.c:77-85` | P-OFF/P-BB | Cond | - | Y | Y | N | N |
| API-29 | `MSC_SCANFF/FR/OFF` | LC | partial | MD `lib/sub/bios.def.h:167-189` | P-OFF | Cond | Scan speed and how scanning ends | Y | N | Y | N |
| API-30 | `MSC_PLAY/PLAY1/PLAYR` | LC | Y | MD `lib/sub/bios.def.h:244-272`. CL `source/bus-sub-m68k.c:87-101` (all/once/repeat). Contradiction: MD also names `$11/$12` UNKNOWN (`:230-242`, OQ-12) | P-OFF/P-BB | Cond: CL behaviour plus the E1 census resolves OQ-12 without P-OFF | "Play all" across track ends; status during play | Y | Y | Y (audio timing) | N |
| API-31 | `MSC_PLAYT/SEEK/SEEKT/SEEK1` | LC | partial | MD `lib/sub/bios.def.h:274-334` | P-OFF | Cond | Seek accuracy; status after seek | Y | N | Y | N |
| API-32 | `ROM_READ/SEEK/READN/READE` | LB/LC | Y | MD `lib/sub/bios.def.h:306-365`; used `lib/sub/cdrom.s:300-316,408-424`. CL `source/bus-sub-m68k.c:103-144` (open TODOs at `:128`, `:140`) | P-OFF/P-RE + P-USE + P-BB | Cond | Count 0; reversed range; interaction with `CDC_START` | Y | Y | Y (timing) | N |
| API-33 | `ROM_PAUSEON/OFF` | LC | partial | MD `lib/sub/bios.def.h:191-205` | P-OFF | Cond | - | Y | N | Y | N |
| API-34 | Undocumented/contested codes | LC | partial | MD `lib/sub/bios.def.h:129-142,230-242`. CL default branch `source/bus-sub-m68k.c:326-328` | P-RE (listed as "present in jump table") | N: semantics unknown in all sources examined | Purpose of `$00`, `$01`, `$0B-$0F`, `$1A-$1F` | Y (E1 shows whether anyone calls them) | partial | Y | N unless E1 finds callers |
| API-35 | `FDR_SET/FDR_CHG` | LC | Y | MD `lib/sub/bios.def.h:436-454`. CL `source/bus-sub-m68k.c:181-204` | P-OFF/P-BB | Cond | Volume scale; ramp units | Y | Y | Y (analogue level) | N |
| API-36 | `CDC_START/STARTP/STOP` | LB | Y | MD `lib/sub/bios.def.h:456-484`. CL `source/bus-sub-m68k.c:206-214` | P-OFF/P-BB. `STARTP` has "No official documentation" | Cond (`STARTP`: N) | Semantics of `STARTP` | Y | Y | N | N |
| API-37 | `CDC_STAT/CDCREAD/CDC_TRN/CDC_ACK` | LB | Y | MD `lib/sub/bios.def.h:486-539`; used `lib/sub/cdrom.s:315-366`. CL `source/bus-sub-m68k.c:216-324` | P-OFF/P-RE + P-USE + P-BB | Cond: well cross-checked by HLE running homebrew and games | Exact `D0` packing; behaviour with no sector | Y | Y | N | N |
| API-38 | `CDCSETMODE` | LC | partial | MD `lib/sub/bios.def.h:661-704` (clobbers "UNKNOWN") | P-OFF | Cond | Clobbers; effect on later reads | Y | N | Y | N |
| API-39 | Subcode `$8E-$94` | LC | partial | MD `lib/sub/bios.def.h:541-626` | P-OFF | Cond | `0x750` work-area layout; error counters | Y | N | Y (disc with subcode) | N |
| API-40 | `LEDSET` | LB/LC | Y | MD `lib/sub/bios.def.h:628-659`; used `new_project/src/sp.s:108-109` | P-OFF + P-USE | Cond | Code for "return control to BIOS" (MD shows `?`) | partial | N (no LED in emulators) | Y | N |
| API-41 | `WONDERREQ/WONDERCHK` | LC | N | MD `lib/sub/bios.def.h:706-720` (names only) | P-RE | N | Everything | N | N | Y (Wondermega) | N (niche) |
| API-42 | Asynchronous command model | LB | partial | MD `lib/sub/cdboot.def.h:24-31` (16.6 ms tick); polling `new_project/src/sp.s:44-47` | P-OFF + P-USE | Cond for LB; N for LC detail | State-transition table; queued vs immediate commands | Y | partial | Y (E5) | N for LB (it feeds the API-23 LC blocker) |
| API-43 | Error/return codes | LB | partial | Carry semantics from MD tags. CL `source/bus-sub-m68k.c:745-870` | P-OFF/P-BB | Cond | Numeric codes; no-disc paths | Y | partial | Y | N |
| API-44 | CDC pre-seek 2-4 sectors | LC | Y | MD `lib/sub/bios.def.h:462-465` | P-OFF/P-RE | Cond | Range per model | Y | N | Y | N |
| API-45 | Timing characteristics | LC | partial | E-GPGX-F `core/cd_hw/cdd.c:630` (data track at least 2 s, "BIOS requirement"), `:1956`. CL `TODO.md:101-102` (sector timing unimplemented) | Emulator comments (non-commercial, cite only) | N: no measured public spec | Latencies, ticks per command, seek times | partial | N | **Y** | **Y (LC)**: timing-sensitive titles cannot be validated without measurement (E5) |
| API-46 | Sector header/mode handling | LB | partial | MD `lib/sub/bios.def.h:497-513`. CL `source/bus-sub-m68k.c:225-293` | P-OFF/P-BB | Cond | Mode-2 form handling | Y | Y | N | N |
| API-50 | `BRMINIT` | LB/LC | Y | MD `lib/sub/bram.def.h:17-35`, wrapper `lib/sub/bram.h:60-104`. CL `source/bus-sub-m68k.c:720-728` | P-OFF/P-BB | Cond | Display strings; "other format" detection | Y | Y | Y (E3) | N |
| API-51 | `BRMSTAT` | LC | Y | MD `lib/sub/bram.def.h:37-47`. CL `source/bus-sub-m68k.c:730-737` (fixed fake values) | P-OFF/P-BB | Cond | - | Y | partial | Y (E3) | N |
| API-52 | `BRMSERCH` | LC | Y | MD `lib/sub/bram.def.h:49-66`. CL `source/bus-sub-m68k.c:739-760` | P-OFF/P-BB | Cond | Meaning of returned `A0` | Y | partial | Y (E3) | N |
| API-53 | `BRMREAD` | LB/LC | Y | MD `lib/sub/bram.def.h:68-86`. CL `source/bus-sub-m68k.c:762-790` | P-OFF/P-BB | Cond | Protect-mode decoding | Y | partial | Y (E3) | N |
| API-54 | `BRMWRITE` | LB/LC | Y | MD `lib/sub/bram.def.h:88-114` (`D1=0` per Tech Bulletin #1). CL `source/bus-sub-m68k.c:792-816` | P-OFF/P-BB | Cond | Overwrite vs. new file; out-of-space handling | Y | partial | Y (E3) | N |
| API-55 | `BRMDEL` | LC | Y | MD `lib/sub/bram.def.h:116-125`. CL `source/bus-sub-m68k.c:818-824` | P-OFF/P-BB | Cond | Compaction | Y | partial | Y | N |
| API-56 | `BRMFORMAT` | LC | Y | MD `lib/sub/bram.def.h:127-137`. CL no-op `source/bus-sub-m68k.c:826-830` | P-OFF | Cond (depends on API-60) | Format image | Y | N | Y (E3) | via API-60 |
| API-57 | `BRMDIR` | LC | Y | MD `lib/sub/bram.def.h:139-165`. CL unimplemented `source/bus-sub-m68k.c:832-836` | P-OFF | Cond | Paging edge cases | Y | N | Y (E3) | N |
| API-58 | `BRMVERIFY` | LC | Y | MD `lib/sub/bram.def.h:167-187` (lists `A0` twice, typo). CL `source/bus-sub-m68k.c:838-873` | P-OFF/P-BB | Cond | Error-number values | Y | partial | Y | N |
| API-59 | BRAM codes `$09/$0A` | LC | N | MD `lib/sub/bram.def.h:189-190` (names only) | P-RE | N | Everything | Y (E1) | N | Y | N unless E1 finds callers |
| API-60 | On-media BRAM format and protect encoding | LC | partial | E-GPGX-F `libretro/libretro.c:131-137,1137-1148` and E-PICO `pico/cd/misc.c:11-24`, `pico/cd/mcd.c:62-68`: a 64-byte formatted-trailer template with size fields and an ASCII medium signature. No directory or protect spec found | Emulator data tables (non-commercial, cite only); origin unstated, presumably copied from a formatted real BRAM. Excl. S-BIOS §7 pp.38-45 | **N**: no non-excluded spec of directory entries, allocation or protect encoding | Directory entry format, allocation order, protect encoding, any checksum | Y (E3) | N | **Y** | **Y (LC)**: saves must interoperate with real consoles, RAM carts and `.brm` files |
| API-61 | File-name rules | LC | partial | MD `lib/sub/bram.def.h:64`. CL `source/bus-sub-m68k.c:555-565` (cites "Sega's developer documentation": 0-9, A-Z, `_`) | P-OFF | Cond | Lower case; padding | Y | Y | Y | N |
| API-62 | RAM-cartridge BRAM | LC | partial | MD `lib/main/bramcart.def.h`. E-GPGX-F `libretro/libretro.c:1185-1195` | P-OFF/emulator | Cond | Detection and size encoding | Y | partial | Y (needs a cart) | N |
| API-63 | BRAM display strings, "other format" | LC | N | CL `source/bus-sub-m68k.c:726-727` ("I have no idea") | - | N | Content and purpose | Y | N | Y | N |
| API-65 | `_CDBOOT` `$00-$05` | LC | Y | MD `lib/sub/cdboot.def.h:17-93` | P-OFF | Cond | Who uses it | Y | N | Y | N |
| API-66 | `_CDBOOT` `$06-$09` | LC | N | MD `lib/sub/cdboot.def.h:95-125` ("No official documentation") | P-RE | N | Everything | Y (E1) | N | Y | N |
| API-70 | Boot header: IP to `$FF0000`, SP to `$6000` | LB | Y | CL `source/clownmdemu.c:494-531` (IP/SP offset and length from header words `$18/$1A/$20/$22`; default IP `$200`/`$600`). MD `docs/boot.md:3,13`. MB `src/sub/main.asm:58-60` | P-BB: CL boots commercial discs without a Sega ROM | **Y**: working black-box loader. Field layout is shared with disc format (Area B) | IP size limit; whether IP length > `$600` is honoured (CL does; unverified) | Y | Y | N (E2 optional) | N |
| API-71 | Security/region check | LB | partial | [open-questions.md](../open-questions.md) OQ-8 | policy | Cond on a legal decision | - | Y | Y | N | **Y (LB policy)**: OQ-8 unresolved |
| API-72 | Word RAM mode/owner at hand-off | LB | partial | CL `source/clownmdemu.c:529-531` (2M, given to Sub). MB `src/sub/main.asm:32-38` (Sub BIOS init sets 1M and returns it to Main) | P-BB / P-UNK. **Apparent disagreement** (may be different phases) | Cond | State observed by IP and SP | Y | Y | Y (E2) | N |
| API-73 | Main CPU state at IP entry | LB | partial | MD `docs/megacd_dev.md:21,29,89` (self-contradictory, OQ-2); `docs/main_bios.md:56-58` (Tech Bulletin #3: stack `$FFFD00`) | P-OFF/P-RE | Cond | SP, SR, registers | Y | partial | Y | N |
| API-74 | IFL2 raised each Main V-INT | LB | Y | MD `docs/main_bios.md:388-394,688-698,740-742`. MB `src/main/function_table.asm:85` | P-RE/P-UNK; P-USE in homebrew | Cond | Whether the default V-INT raises IFL2 before the IP patches it | Y | Y | N | N |
| API-75 | Comm registers cleared at boot | LB | Y | MB `src/sub/main.asm:22-27`. M1 `src/mode_1/mcd_mode_1.asm:39` | P-UNK, 0BSD | Y | - | Y | Y | N | N |
| API-76 | Mode-1 signatures, compressed Sub BIOS | LC | Y | M1 `src/mode_1/mcd_mode_1.asm:115-178`. MB `README.md:17-23`. MD `lib/main/bios.def.h:1387-1402`. E-PICO `pico/cd/memory.c:1220-1223` (MSU-MD checks `"SEGA"` at `$400100`) | P-USE (callers state the contract). The offsets were learned from real ROMs (P-RE/P-OFF, Tech Bulletin #3) | Cond: public interoperability facts. **Trademark question** about embedding `"SEGA"` (OQ-5 family) | Callers need a particular Kosinski encoder for detection (MB README); is the `"WONDER"` variant required? | Y | Y | Y (MSU-MD class on hardware) | N (design constraint) |
| API-77 | Mode-1 Sub BIOS self-start with cart SP | LC | Y | M1 `src/mode_1/mcd_mode_1.asm:32-105` | P-USE (0BSD) | Y: caller contract is public | - | Y | Y | Y | N |
| API-80 | Main vectors to `$FFFD00` slots, order | LB | Y | MD `lib/main/memmap.def.h:65-99`, `docs/megacd_dev.md:7-17`. MB `src/main/call_table.asm:21-50`. CL `source/mega-cd-boot-rom.c:1-15` (MB build) | P-RE (MD), P-UNK (MB). MD duplicate slot (OQ-12) | Cond: shape agreed by 2 sources; E6 resolves OQ-12 | Slot for illegal instruction vs address error | Y | Y | Y (E6) | N |
| API-81 | Slot defaults; patch slot+2 | LB | Y | MD `docs/megacd_dev.md:17,31`, `docs/main_bios.md:61-63` (Tech Bulletin #3, "label value plus 2") | P-OFF/P-RE | Cond | - | Y | Y | N | N |
| API-82 | `$280` table: existence, order, entry size | LC | Y | MD `lib/main/bios.def.h:451-1384`, `docs/main_bios.md:30-42`. MB `src/main/function_table.asm:16-102` (73 entries) | **P-RE only** (MD explicit); MB P-UNK. Tech Bulletin #3 names `MAINENT.I`/`ROM_UTIL.DOC` (not found) | **N under current policy** (OQ-7 forbids disassembly-derived tables), although technically fully described | Clean-room re-derivation of order and semantics | Y (E4) | partial | Y (E4) | **Y (LC)**: OQ-7 |
| API-83 | `$280` system group | LC | partial | MD `lib/main/bios.def.h:451-481`, `docs/main_bios.md:373-383` (empty). MB `src/main/function_table.asm:21-24` | P-RE/P-UNK; **names disagree** (MD: entry/reset/init/init-SP; MB: soft/hard reset, control panel) | N (OQ-7) | Semantics | Y (E4) | partial | Y | Y (OQ-7) |
| API-84 | V-INT handler/wait/flags | LC | Y | MD `docs/main_bios.md:224-238,388-408`, `lib/main/bios.def.h:93,296-334`. MB `src/main/function_table.asm:25-26` ("not available in clownmdemu") | P-RE | N (OQ-7) | - | Y | Y | Y | Y (OQ-7) |
| API-85 | Input | LC | partial | MD `lib/main/bios.def.h:526-560`. MB `src/main/function_table.asm:28-29,65` | P-RE/P-UNK | N (OQ-7) | Repeat-delay semantics | Y | Y | Y | Y (OQ-7) |
| API-86 | VDP/DMA utilities, default registers, VRAM layout | LC | Y | MD `docs/main_bios.md:240-279,428-547`. MB `src/main/function_table.asm:30-46,99-100`, `src/main/vdp.asm` | P-RE/P-UNK | N (OQ-7) | Region-dependent defaults (MD "TODO: confirm") | Y | Y | Y | Y (OQ-7) |
| API-87 | Palette cache and fades | LC | Y | MD `docs/main_bios.md:287-293,579-595,650-666` | P-RE | N (OQ-7) | - | Y | Y | N | Y (OQ-7) |
| API-88 | Nemesis/Enigma decompression | LC | partial | MD `lib/main/bios.def.h:849-865,1084-1086`. MB `src/main/function_table.asm:49-50,66`, `src/main/decompress.asm` | P-RE. The formats themselves are community-documented (not examined, §5) | Cond: formats are public; entry semantics need OQ-7 | Use of the `$FFF700` buffer | Y | Y | N | Y (OQ-7) |
| API-89 | Sprite-object/entity system | LC | partial | MD `docs/main_bios.md:311-343` (incomplete, "unknown byte") | P-RE | N | Field meanings | Y | Y | N | Y (OQ-7) |
| API-90 | Built-in font and print | LC | Y | MD `docs/main_bios.md:349-357`. MB `src/main/splash.asm:19-29` (homebrew and hacks use the font/logo left in VRAM) | P-RE/P-UNK | Cond: supply **our own** font (as MB does). Tile-index placement (base 32) is an RE fact | Glyph mapping beyond ASCII | Y | Y | N | Y (OQ-7) |
| API-91 | PRNG | LC | partial | MD `docs/main_bios.md:345-347,749-759` (multiply-with-carry; constants not given) | P-RE | N | Exact algorithm (games may depend on the sequence) | Y | Y | N | Y (OQ-7) |
| API-92 | Comm sync, Sub-BIOS proxy calls, comm-flag protocol | LC | partial | MD `docs/main_bios.md:359-368,684-742` ("still investigating"). MB stubs 8 such entries as "not available in clownmdemu" (`src/main/function_table.asm:71-83,91`) | P-RE, incomplete even within the RE community | **N**: unknown in all sources examined. Our Sub BIOS would also need the matching responder | Full two-CPU protocol | partial (E4) | N | **Y** | **Y (LC)**: MD says most retail users of `$280` use these (`docs/main_bios.md:363`) |
| API-93 | BCD/time arithmetic | LC | partial | MD `lib/main/bios.def.h:1300-1313,1378`. MB `src/main/function_table.asm:93-94,101-102` | P-RE/P-UNK | N (OQ-7) | Formats | Y | Y | N | Y (OQ-7) |
| API-94 | Main work-area layout | LC | Y | MD `lib/main/bios.def.h:44-399`, `docs/main_bios.md:126-171`, `docs/megacd_dev.md:23-25`. MB `src/main/variables.inc` | P-OFF (Tech Bulletin #3 diagram) + P-RE | N (OQ-7) | Variation between revisions ("may vary by revision") | Y | Y | Y | Y (OQ-7) |
| API-95 | Residual VRAM/VDP/palette state at IP entry | LC | partial | MB `src/main/splash.asm:19-29` | P-UNK (observation of the original) | Cond: our own assets in the same places, confirmed by black-box screenshots | What exactly remains | Y | Y | Y | N |
| API-96 | Return to BIOS / control panel | LC | partial | MB `src/main/function_table.asm:21-24`. MD `lib/sub/bios.def.h:647` (LED "return control to BIOS") | P-UNK/P-OFF | Cond | Entry conditions | Y | Y | Y | N |
| API-98 | Model/region variants | LC | partial | MD `docs/main_bios.md:38` (`$280` fixed across models), `lib/main/bios.def.h:1393-1402` (Sub image offset varies). M1 signature list `src/mode_1/mcd_mode_1.asm:149-178` | P-RE/P-USE | Cond | Per-model extra calls (Wondermega, LaserActive) | partial | N | Y | N |
| API-99 | Region-dependent API behaviour | LC | N | MD `docs/main_bios.md:487` ("TODO: confirm that this is different per region") | P-RE | N | Everything | Y | N | Y | N |
## 3. Per-level summary

The counts come from the table above. A row tagged "LB/LC" is counted once, at LB.

- **Verifiable spec (non-excluded):** column 4 is not N, and column 7 is Y or Cond. Public, non-P-OFF material gives a concrete, testable definition (inputs, outputs, addresses), even when its origin is tainted.
- **Clean today:** column 7 is Y.

| Level | Items enumerated | Verifiable spec from non-excluded sources | Clean today (Y) | Blockers |
| --- | --- | --- | --- | --- |
| LA | 0 | 0 | 0 | None. A minimal boot exposes no API surface (see rom-layout and memory-map). |
| LB | 38 | 37 (all except API-11) | 5 (API-09, 17, 18, 70, 75) | **API-71** (security/region policy, OQ-8). API-23 is listed as a blocker only for its LC part. |
| LC | 50 | 31 | 1 (API-77) | **API-23** (full CDBSTAT structure), **API-45** (drive timing), **API-60** (BRAM media format), **API-82 to API-94** (Main `$280` library, policy-blocked by OQ-7), **API-92** (comm/proxy protocol, not found in the sources examined: MD, CL, MB, M1, E-GPGX-F, E-PICO; corrected during integration review) |
| **Total** | **88** | **68** | **6** | |

**Verdict.**

- **LB:** a MegaDev-class homebrew SP can be specified from public material. Almost all of it is "Cond": the knowledge is public, but it traces back to the leaked manual or to disassembly. E1 (caller census) and E2 (in-situ black-box probe) can establish a clean provenance chain.
- **LC:** cannot be specified from public non-excluded material today. In the sources examined:
  - the Main `$280` library is P-RE (policy-blocked);
  - the comm/proxy protocol is unknown;
  - the BRAM media format and drive timing have no independent spec;
  - the full CD status structure is only guessed.
- **Prior art (new):** MB (0BSD) shows that an independent Main-side boot ROM, including a `$280` table, already exists and runs software in CL. Its Sub side, however, relies on AGPL C traps rather than an actual Sub BIOS. Its provenance (P-UNK) must be clarified with the authors before anyone treats it as a clean-room precedent.

## 4. Feasible legal independent experiments (design only)

None of these uses or distributes a Sega ROM image, and none risks hardware damage. Commercial discs appear only as the tester's own copies, run locally, and are never distributed. E1(b) and E4 still need a maintainer decision under OQ-7.

| Exp. | Closes | Design |
| --- | --- | --- |
| **E1** Caller-side API census | API-01-07, 30, 34, 59, 66; OQ-12 | Instrument an emulator that uses HLE traps and has **no Sega ROM loaded** (a CL-style build, or our own BIOS later). Log every `JSR` into `$5F0A-$5F3A` and `$000280-$0003A3`: the code, `D0/D1/A0/A1`, the caller PC and the bytes at `A0`. Run (a) public homebrew (MegaDev examples, own builds) and (b) the tester's own commercial discs. The output is a usage census, i.e. caller-observed interface facts that are independent of Sega's implementation. |
| **E2** In-situ Sub BIOS probe | API-08, 10, 12, 14, 15, 23, 42, 43 | Run our own code from a Mode-1 flash cart. Use the console's own BIOS in place (M1-style detection and decompression; nothing leaves the console). Put a probe SP at `$6000`. For each code: preset the registers, call, then record the registers, CCR, `$5E80-$5EA7` and the status-struct bytes. Report over the comm registers to the Main side and show on screen. Team A writes specs; team B implements. |
| **E3** BRAM format by construction | API-50-63 | With the E2 probe: `BRMFORMAT`, then write files of known names, sizes and modes one at a time. Dump the internal BRAM bytes after each step. Derive directory, allocation and protect encoding as a written spec. Repeat on a RAM cart. |
| **E4** Black-box `$280` behaviour | API-82-95 | **Only if OQ-7 approves a clean-room protocol.** Call each Main `$4002xx` entry from a Mode-1 cart with controlled inputs inside a sandboxed RAM/VRAM state. Diff Work RAM, VRAM, CRAM and the VDP register cache. Never read ROM code. |
| **E5** Drive timing and state machine | API-20, 23, 26, 31, 42, 45 | Use our own CD-R (own data plus own audio tracks). A Mode-1 probe issues commands and timestamps `CDSTAT` transitions against INT2 ticks and the GA stopwatch. Never issue `CDBPAUSE $FFFF`. |
| **E6** Exception slot mapping | API-08, 80; OQ-12 | Fill every Main and Sub slot with a distinct marker handler. Trigger address error, illegal instruction, divide by zero, CHK, TRAPV, privilege violation, trace, line A/F and TRAP #n. Record which marker runs. |

## 5. Not investigated (this audit)

- **Excluded by Issue #17:** the S-BIOS / S-SDM pages and Tech Bulletins (#1, #3, BIOS TB). Leads from the TOC: call list pp.7-8, reference pp.11-29, bootstrap pp.30-32, jump table and user calls pp.33-35, CD-Boot pp.36-37, Back-up RAM pp.38-45.
- **Files referenced but not found:** `MAINENT.I`, `ROM_UTIL.DOC` and `cabios.i` were not found in the sources examined (MD, CL, MB, M1, E-GPGX-F, E-PICO).
- **Emulators and cores:** BlastEm, Ares, Kega Fusion and the MiSTer MegaCD core were not examined.
- **Game disassemblies:** public disassemblies of commercial games (e.g. Sonic CD) that show BIOS call sites were not examined, because their provenance is policy-sensitive.
- **Forum sources:** Devon's forum notes cited by CL (`source/bus-sub-m68k.c:67-68`) and the gendev threads (`:1-4`) were not read.
- **Compression formats:** community documentation of the Kosinski, Nemesis and Enigma formats was not examined.
- **MB / CL provenance:** we did not ask the MB and CL authors how they obtained their knowledge. Upstream `Clownacy/clownmdemu-core` history was checked only for `mega-cd-boot-rom.c` (last update `c36f6542bc`, 2025-09-07).
- **Inaccessible pages:** O-SEGAJP returned HTTP 403 again on 2026-10-08 and needs a check by a human in a browser (OQ-15). I-RHOPE was not re-read (TLS problem, OQ-15).
- **Hardware variants:** Wondermega, LaserActive and CDX specific extensions, and 32X+CD interaction (`MAINCPU.INC`, quoted only in MD `docs/main_bios.md:87-100`).
## 6. Findings against existing docs (for the integrator; other files were not edited)

- [bios-api.md](../bios-api.md) §1 cites MD `lib/sub/cdrom.macro.s:34` for the `JSR` calling convention. At the pinned commit that line is a comment. The `JSR _CDBIOS` is in the `BIOSCALL` macro, `lib/sub/sub.macro.s:32-34`.
- bios-api.md A-11/A-12 cite MegaDev only. An independent 0BSD reimplementation of the Main `$280` table (73 entries, `$280-$3A3`) and of the work area exists in MB. It does not resolve OQ-7, because its provenance is undeclared, but OQ-7 should record it.
- OQ-12 has a second resolution route that needs no P-OFF material: CL's HLE treats `$11/$12/$13` as play-all / play-once / repeat (`source/bus-sub-m68k.c:87-101`), and E1 can confirm this.