# Cross-project OSS reuse inventory

Status: **candidate inventory only** (2026-10-09); all candidates are `PENDING`, none is approved for firmware inclusion. Do not treat a repository's apparent license badge as complete provenance. See [reuse policy](provenance.md).

## Candidate source assessment

| Candidate / pinned commit | Candidate sources | Actual observed license | Use in Mega-CD ROM | Decision |
| --- | --- | --- | --- | --- |
| [Genesis Plus GX](https://github.com/libretro/Genesis-Plus-GX/tree/58c341487e5bfcf979ea68413c7987633adb0c56) · `58c341487e5bfcf979ea68413c7987633adb0c56` | `core/cd_hw/cdd.c`, `cdc.c`, `scd.c` and associated headers; emulator has detailed CDD/CDC timing models | Root `LICENSE.txt` is a **custom non-commercial/no-sale license** by default, with full-source obligations for modified distributions. Some files may have separate notices—each needs audit. **Not MIT/GPL by default.** | Cannot silently copy/port into planned MIT firmware; external reference/emulator testing subject to license | **RESTRICTED for direct import pending separately granted rights**; behavioral research only subject to rights/provenance review |
| [PCSX-Redux Nugget OpenBIOS](https://github.com/pcsx-redux/nugget/tree/c950e18a168944ec2d4e6d3c408fc224317483a7/openbios) · `c950e18a168944ec2d4e6d3c408fc224317483a7` | `openbios/cdrom/statemachine.c`, `openbios/cdrom/filesystem.c`, `openbios/kernel/events.c` | Root MIT; inspected candidate files contain MIT headers, but all dependencies not audited | Cross-console CD state/TOC/ISO9660 model and synthetic tests **only if behavior matches**; PS1 hardware registers are not Mega-CD registers | **PENDING — REFERENCE_ONLY** by default |
| [HuCC/HuC](https://github.com/pce-devel/huc/tree/54f5c73606c1e7142e8095c727cab2767e2b3cb3/include/hucc) · `54f5c73606c1e7142e8095c727cab2767e2b3cb3` | `hucc-math.asm`, `hucc-systemcard.asm`, `vdc.asm` | Examined file headers say **Boost Software License 1.0**; check dependencies and LICENSE_1_0.txt | Useful for `oss-pce-cd-bios` on HuC6280; **not executable as Mega-CD 68000 code**; shared conceptual tests only | **PENDING — NOT directly applicable to 68000** |
| [Hu-Go!](https://github.com/mckayemu/hugo/tree/64ed226da2288738781743eeef228c069e8973a4) · `64ed226da2288738781743eeef228c069e8973a4` | `bios.c`, `cd.c`, `pcecd.c` | Default project code **GPL-2.0**; `pcecd.c` has a separate modified-BSD exception as described in COPYING | Hardware platform differs; use only non-copied behavioral research/test ideas. Do not conflate GPL with the exception | **PENDING — REFERENCE_ONLY** |
| [NeoCD-Libretro](https://github.com/libretro/neocd_libretro/tree/b1e04c738cb48a1dae0574b8877f6a116d270ca1/src) · `b1e04c738cb48a1dae0574b8877f6a116d270ca1` | `hlebios.cpp`, `cdromtoc.cpp`, `cdromcontroller.cpp` | Repository `LICENSE.md` **LGPL-3.0**; file/dependency obligations unreviewed | HLE examples of TOC/track/playback and state tests; Neo Geo CD architecture differs | **PENDING — REFERENCE_ONLY** |

## Common logical CD tasks vs machine-specific operations

| Possible shared specification + test fixtures | **Mega-CD** hardware adapter must stay separate | **PC Engine CD-ROM²** adapter must stay separate | **PS1 Runtime** adapter must stay separate |
| --- | --- | --- | --- |
| MSF <-> LBA math, BCD validity and conversions, TOC track order and first/last track, CD-DA start/pause/stop error cases, 75 frames/s boundary vectors, sector read request/result states | CDD commands/status, CDC sector buffer and DMA, Word RAM ownership, Sub-CPU/Main CPU IPC, interrupts and audio control | HuC6280 banking, System Card entry ABI, CD interface, ADPCM, IRQ and CD-DA command path | R3000A BIOS A0/B0/C0 ABI, CD-ROM registers/IRQ2/DMA3, device scheduler, memory card/SIO0 |

These are **candidate generic contracts**, not accepted cross-system ABI semantics. Physical sector layouts, lead-in conventions, absolute/relative MSF offsets, error/status codes and loop/audio semantics **can differ by system and operation**. Only promote a shared helper after both testable contracts are independently validated; prefer sharing deterministic input/output vectors and host-side tooling over falsely claiming portable ROM assembly.

## Prioritized work and non-goals

1. Finish current Mega-CD bootstrap PRs (toolchain, default-deny provenance, fixtures, emulator harness), rather than pre-empting unmerged hardware work.
2. In [#31](https://github.com/mao2009/oss-mcd-bios/issues/31), pin each reused file revision/blob, check license/dependencies and gain reviewer approval. Check copyright notice distribution in the **ROM release artifact**, not source alone.
3. In [#24](https://github.com/mao2009/oss-mcd-bios/issues/24) and [#28](https://github.com/mao2009/oss-mcd-bios/issues/28), separate logical CD operations from CDD/CDC/PCM hardware timing. Keep Genesis Plus GX as non-embedded external reference unless permission is established.
4. Coordinate synthetic fixture specifications with [oss-pce-cd-bios](https://github.com/mao2009/oss-pce-cd-bios) and [PSXRecompStudio #730](https://github.com/mao2009/PSXRecompStudio/issues/730).
5. Do not claim a bootable Mega-CD firmware, retail compatibility or successful emulator execution merely because these documents/host tests exist.

**No third-party implementation is copied or imported by this inventory.**
