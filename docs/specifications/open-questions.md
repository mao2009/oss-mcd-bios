# Open questions, contradictions and verification proposals

When sources disagree, we record the disagreement here. We do not settle it by guessing. Each entry lists the sources, why it matters, and a proposed **independent** verification program. The programs are described only; nothing is implemented in this PR. They must follow the [provenance rules](../provenance.md): our own test code only, no Sega code or dumps in the repository or in CI, and any observation of reference hardware or BIOS behaviour recorded as clean-room behaviour notes.

## A. Contradictions between sources

| ID | Topic | Sources and what each says | Impact |
| --- | --- | --- | --- |
| OQ-1 | H-INT vector high word (`$000070-71`) | E-GPGX forces `$FFFF` at hard reset (`core/cd_hw/scd.c:1801-1803`). E-PICO forces `$FF` bytes only with no cartridge and otherwise uses ROM bytes (`pico/cd/mcd.c:80-81`). I-MEGADEV says the boot ROM leaves `$00FF` (`lib/main/gate_arr.def.h:261-262`). | Decides what our ROM puts at `$70`, and whether the gate array overrides it. Matters for H-INT in both Mode 1 and Mode 2. |
| OQ-2 | Default Main stack top after boot | I-MEGADEV `docs/megacd_dev.md:21,29` (stack `$FFFC00-$FFFD00`, "leaving it at `$FFFC00` as it is from boot") vs `docs/megacd_dev.md:89` ("allocated to `$FFFD00` by default"). Self-inconsistent. | Software may assume an SP value when the IP starts. |
| OQ-3 | Main-CPU `$040000-$1FFFFF` | S-HW §1-3 p.16: "reserved by the system". E-GPGX mirrors ROM and PRG-RAM every 256 KiB (`core/cd_hw/scd.c:1596-1642`). E-PICO maps only `$000000-$01FFFF` (`pico/cd/memory.c:1232-1233`). | The BIOS must not rely on mirrors. Tests must not assume either behaviour. |
| OQ-12 | MegaDev internal duplicates | `lib/sub/bios.def.h:235,242` define `BIOS_UNKNOWN11=$0011` and `BIOS_UNKNOWN12=$0012`, while `:252,262` define `BIOS_MSC_PLAY=$0011` and `BIOS_MSC_PLAY1=$0012`. `lib/main/memmap.def.h:92-93` assigns `$FFFD80` to both `EXVEC_ADDRERR` and `EXVEC_ILLEGAL`. | Function-code and exception-slot tables cannot be taken from MegaDev without an official cross-check (S-BIOS §2-2 pp.7–8). |

## B. Unknowns (no adequate source)

| ID | Question | Status | Proposed independent verification |
| --- | --- | --- | --- |
| OQ-1 (cont.) | See above | UNCONFIRMED | **Mode-1 probe cartridge** (our own code, run from a flash cartridge on real hardware with the stock Mega-CD attached). Read `$400070-$400073` and `$A12006`; write patterns to `$A12006` and re-read; take an H-INT and record the jump target. Compare with GPGX and PicoDrive running the same probe. |
| OQ-4 | Does a Sub access to 2M Word RAM owned by the Main CPU stall, return open bus, or fault? | UNCONFIRMED | Mode-1 probe: Main keeps Word RAM. The Sub test program, loaded by our probe into PRG-RAM, touches `$080000`, and a timer-interrupt watchdog reports via the communication registers whether it returned. |
| OQ-5 | Does any software or hardware require `"SEGA"` at ROM `$100` (seen at `$400100` in Mode 1)? | ESTIMATED (E-PICO comment only) | Survey public homebrew sources (e.g. MSU-MD drivers) for the check. Mode-1 probe reads `$400100-$40010F`. Until resolved, the ROM should place `"SEGA"` at `$100` (non-enforced recommendation). |
| OQ-6 | Is TMSS involved when booting the Mega-CD boot ROM in Mode 2 on TMSS consoles? | UNCONFIRMED | Hardware test with our own ROM on TMSS and non-TMSS Mega Drive units once a flashable boot path exists (M4). Until then, the BIOS should write `"SEGA"` to `$A14000` when the version register indicates TMSS (standard Mega Drive practice, ESTIMATED). |
| OQ-7 | Main-side `$000280` jump table and `$FFFDB4+` work area: existence, entries, order, semantics | UNCONFIRMED (I-MEGADEV only, from reverse engineering of unknown method: `docs/main_bios.md:12,30-44`) | **Needs a maintainer/legal decision before any work.** MegaDev's knowledge comes from reverse engineering of Sega ROMs. Proposed clean-room protocol: team A writes behaviour specs (inputs/outputs only) from public docs and black-box tests of retail games. Team B implements from the specs alone. Do not consult disassembly. |
| OQ-8 | Disc security / region check. I-RHOPE says the original BIOS compares disc boot data `$200-$783` against an internal region-specific copy. | ESTIMATED (single independent source, unverified TLS) | **Policy + legal decision.** An independent BIOS cannot contain Sega's security block. Options: (a) boot any disc with a valid system ID; (b) check only the region byte at `0x20B`. Needs legal review (cf. trademark-based lockout precedent) before choosing. Test with our own discs carrying each region byte. |
| OQ-9 | Valid disc system IDs and their semantics (`SEGADISCSYSTEM`, `SEGABOOTDISC`, `SEGADISC`, `SEGADATADISC`) | ESTIMATED | Review S-FMT §3-2/3-3 pp.6–7 and Appendix 2 pp.18–19. Build our own test discs for each ID and record emulator behaviour. |
| OQ-10 | Is the gate-array "forced reset" sequence (S-HW §4-1 p.56) required at BIOS start, and in which mode? | UNCONFIRMED | Read S-HW §3-1 pp.22–25 and §4-1 pp.56–57 fully. Mode-1 probe: compare register state before and after the sequence. |
| OQ-11 | CDD command/status protocol details (timing, checksum, command set) | ESTIMATED | Review S-HW §3-6 pp.31–33 and S-BIOS §3-D p.12. Diff GPGX `core/cd_hw/cdd.c` against PicoDrive `pico/cd/cdd.c` and record each difference as a separate test case. |
| OQ-13 | Power-on value of `$A12000-$A12003` (SRES/SBRQ, MODE/RET) | ESTIMATED (both emulators; PicoDrive says "tested") | Mode-1 probe reads the registers as its first instructions after cold boot. |
| OQ-14 | Bit positions of BK0/1 and WP0-7 in `$A12002-3` | ESTIMATED (official scan p.57 is cropped) | Find a complete scan (MegaDev `docs/main_bios.md` mentions three independent scan sets). Mode-1 probe: write each bit and observe the PRG-RAM window contents. |
| OQ-16 | Is the boot ROM 128 KiB in all regions and models (JP/US/EU, Model 1/2, CDX, Wondermega, LaserActive)? | ESTIMATED | Use public PCB photos/schematics: ROM chip markings and pin count give capacity without dumping. Record the source per model. |
| OQ-17 | Sub-CPU address decoding (1 MiB mirroring) | UNCONFIRMED | Sub-side probe reads a known PRG-RAM pattern at `+$100000`. |

## C. Source and process gaps

| ID | Gap | Action |
| --- | --- | --- |
| OQ-15 | Inaccessible sources. O-SEGAJP returns HTTP 403 (Cloudflare challenge). I-RETROSIX requires login. I-RHOPE has a TLS certificate mismatch (cert for `www.retrodev.com`; HTTP gives 502). | A human checks O-SEGAJP and I-RETROSIX in a browser and records the version/date. Ask the I-RHOPE author about the certificate, or find a mirror with integrity. |
| OQ-18 | Official pages not reviewed in this PR: S-SDM (all), S-FMT (all), S-HW pp.13, 15, 17–29, 31–55, 58–63, S-BIOS pp.5–29, 31–32, 34–45 | Review page by page. Paraphrase facts and upgrade ESTIMATED items (B-08, B-09, B-10, A-01, A-02, register bit layouts, function codes). |
| OQ-19 | Legal status of citing leaked "CONFIDENTIAL" manuals | Maintainer/legal confirmation that paraphrased citation (no reproduction) is acceptable under the project's provenance policy. **Blocks merging PR #16** (see the notice in [README.md](README.md)). |
| OQ-20 | E-GPGX citations use upstream `49c5847`. The PR #15 harness pins fork `mao2009@87dd8b8`, where line numbers in `scd.c`, `mem68k.c`, `cdc.c` and `cdd.c` are shifted. | Before the harness relies on a cited behaviour, re-verify it in the fork and record any behavioural (not only line-number) difference. |

## D. Proposed GitHub issues (deduplicated)

1. OQ-1 H-INT vector high word: emulator divergence and Mode-1 probe
2. OQ-3 + OQ-17 address mirroring (Main and Sub)
3. OQ-2 default Main stack pointer at IP entry
4. OQ-12 MegaDev table inconsistencies vs official BIOS call list
5. OQ-4 Word RAM access by non-owner
6. OQ-5 + OQ-6 header `"SEGA"` / TMSS requirements
7. OQ-7 clean-room protocol for the Main-side `$280` jump table (needs maintainer/legal)
8. OQ-8 disc security/region policy (needs legal)
9. OQ-9 disc system IDs
10. OQ-10 + OQ-13 + OQ-14 gate-array reset state and register bit layout
11. OQ-11 CDD protocol specification and emulator diff
12. OQ-16 per-model ROM capacity from public PCB evidence
13. OQ-15 + OQ-18 + OQ-19 source access, remaining official pages, citation policy
14. Mode-1 probe cartridge (shared infrastructure for 1, 2, 5, 6, 10)
15. OQ-20 re-verify E-GPGX citations against the harness fork `mao2009@87dd8b8`
