# Genesis Plus GX investigation (Issue #5)

Investigation of the owned fork used as an **external, test-only** emulator for the smoke harness in
[`tools/emu/`](../../tools/emu/README.md). Nothing from the emulator is vendored into this repository;
the harness fetches and builds it at test time at the pinned revision.

- Repository: <https://github.com/mao2009/Genesis-Plus-GX> (default branch `master`)
- Pinned / inspected SHA: `87dd8b80802ff5217ab2f765202b6b14ecd23f94`
  ("Merge feature/phase1-core-instrumentation: Add core instrumentation", 2026-08-21)
- Inspected on: 2026-10-08, read-only clone outside this repository.

All `file:line` citations refer to **the fork pin `mao2009@87dd8b8`**, not upstream. Labels:
**CONFIRMED** = read in source at the pin and/or observed by running the harness;
**UNVERIFIED** = inferred, not yet exercised.

### Fork pin vs upstream `ekeeke@49c5847`

Other project notes (e.g. Agent A's INV docs) cite upstream `ekeeke/Genesis-Plus-GX@49c584764893`
(2026-10-06). The relationship, checked with `git diff 49c5847 87dd8b8` (CONFIRMED):

- Both branch from merge-base `27426f0`. The fork adds 10 commits (instrumentation: `emu_event`, S68K/Z80
  hooks, all under `#ifdef HOOK_CPU`). Upstream has 13 newer commits that the fork lacks. These include
  Main/Sub-CPU synchronization fixes in `core/cd_hw/scd.c` (MCD-verificator IRQ tests), a timer period
  fix, CHD metadata bounds and savestate index validation.
- **Identical** in both: `core/loadrom.c`, `libretro/libretro.c`, `core/macros.h`, `core/cd_hw/scd.h`,
  `libretro/link.T`, `Makefile.libretro`, `libretro/Makefile.common`. Line citations in these files
  are valid for both revisions.
- **Different**: `core/cd_hw/scd.c` and `core/cd_hw/cdd.c` (fork: `HOOK_CPU` includes and event pushes;
  upstream: the sync fixes and CHD bounds). Line numbers in those two files are **fork-only**.
- Consequence: Mega-CD CPU-synchronization behaviour at the fork pin is older than upstream. A
  discrepancy between the two must not be resolved by adapting the BIOS to either one (see
  `docs/reuse-from-projects.md`, convention 4). Re-pinning to a fork commit rebased on upstream is
  future work.

## 1. License

| Finding | Status | Evidence |
| --- | --- | --- |
| Core code is under a custom **non-commercial** license: redistributions "may not be sold, nor may they be used in a commercial product or activity"; modified redistributions must ship full source. This is **not MIT-compatible** for inclusion. | CONFIRMED | `LICENSE.txt:1-12` |
| `LICENSE.txt` also lists third-party components with their own licenses (e.g. Nuked OPN2 under LGPL-2.1, further notices below it). Bundled deps compiled into the core include libchdr, zstd, LZMA SDK, zlib and Tremor. | CONFIRMED (presence) | `LICENSE.txt`, `core/cd_hw/libchdr/deps/`, build object list |
| The new instrumentation files carry the same non-commercial header. | CONFIRMED | `core/debug/emu_event.h:1-37`, `core/debug/cpuhook.h:1-38` |
| The repository tracks a prebuilt `builds/genesis_plus_gx_libretro.dll`; the harness does **not** use it (it builds from source so the SHA identifies the binary). | CONFIRMED | `git ls-files builds/` at the pin |

Consequence: the harness only stores the **repo URL + SHA** (`tools/emu/gpgx.lock`). Source and binaries
live in a cache **outside the repository tree** (`$GPGX_CACHE_DIR`, default `<user cache dir>/oss-mcd-bios/gpgx`)
and must never be committed, attached to releases or uploaded as CI artifacts of this project. The harness host (`tools/emu/libretro_host.py`) is original code written
against the public libretro C ABI and does not include or link emulator source at build time.

## 2. How a Mega-CD BIOS ROM is loaded

### 2a. Normal path: BIOS from the system directory + CD image

| Finding | Status | Evidence |
| --- | --- | --- |
| libretro frontend paths: `bios_CD_E.bin` (PAL), `bios_CD_U.bin` (NTSC-U), `bios_CD_J.bin` (NTSC-J) inside the frontend *system directory*. | CONFIRMED | `libretro/libretro.c:3416-3418` |
| CD BIOS files are treated as required; a missing file logs `Unable to open CD BIOS`. | CONFIRMED | `libretro/libretro.c:337-343` |
| `load_bios(SYSTEM_MCD)` picks the file by `region_code` (USA → `_U`, Europe → `_E`, else `_J`) and loads at most `sizeof(scd.bootrom)` = 128KB. | CONFIRMED | `core/loadrom.c:394-417`, `core/cd_hw/scd.h:73` |
| No size/checksum validation beyond `size > 0`. Hardware model is chosen from the 16 bytes at `$120`: `WONDER-MEGA BOOT`, `WONDERMEGA2 BOOT`, `CDX BOOT ROM    `, otherwise default model. | CONFIRMED | `core/loadrom.c:419-442` |
| On little-endian hosts the BOOT ROM is byte-swapped per 16-bit word after load. | CONFIRMED | `core/loadrom.c:444-453` |
| A BIOS file larger than 128KB is truncated, not rejected. The only hard limit is `MAXROMSIZE`. | CONFIRMED (code) | `libretro/libretro.c:354-363` |
| For a CD image the region comes from the security-code byte at disc header `$20B` (`0x64` Europe, `0xA1` Japan, else USA). The core option `genesis_plus_gx_region_detect` overrides it before `load_bios` runs. | CONFIRMED (code) | `core/loadrom.c:1056-1073, 1155-1158`, `core/loadrom.c:579-591, 718-733` |
| A cooked (2048-byte sector) image is accepted as a Mega-CD disc when its first 14 bytes are `SEGADISCSYSTEM`; no further content is required for the core to enter Mega-CD mode and load the system-directory BIOS. | CONFIRMED (code + harness run) | `core/cd_hw/cdd.c:584-602` (fork line numbers) |

**Harness default (`--mode system`)** follows this normal path. The ROM is copied unchanged to
`bios_CD_U.bin`, `bios_CD_E.bin` and `bios_CD_J.bin` (one file under each name, so region choice cannot
pick a missing file). A synthetic 32KB disc image is inserted; it contains only the `SEGADISCSYSTEM` ID
and no program, and is generated per run. **No emulator-specific requirement is placed on the BIOS ROM.**

### 2b. Optional harness path (`--mode bootrom`, emulator-specific): BIOS image loaded *as content* ("BR" boot ROM)

When a cartridge-style image (≤ 8MB) is loaded with add-on mode not `none`, the core switches to
Mega-CD hardware and copies the image into the BOOT ROM if the header type field contains `BR`:

| Condition (in order) | Status | Evidence |
| --- | --- | --- |
| Extension not `.sms/.gg/.sg` → Mega Drive hardware. The harness copies the ROM to `bios.bin`. | CONFIRMED | `core/loadrom.c:621-640` |
| A 512-byte copier header is stripped if `$100` ≠ `SEGA` and the size is an odd multiple of 512. | CONFIRMED | `core/loadrom.c:667-682` |
| Region for this path comes from the **cartridge** country field at `$1F0` (`U`/`J`/`E`, …), unless overridden by core option `genesis_plus_gx_region_detect` (`ntsc-u`/`pal`/`ntsc-j`). | CONFIRMED | `core/loadrom.c:48-59, 692, 1076-1118`; `libretro/libretro.c:1504-1515` |
| Requires `cart.romsize <= 0x800000` and `config.add_on != HW_ADDON_NONE` (libretro default is `HW_ADDON_AUTO`). | CONFIRMED | `core/loadrom.c:736`; `libretro/libretro.c:1076`; `core/cart_hw/md_cart.h:59-62` |
| If the I/O-support field (`$190`, 14 bytes) contains `C` (CD-ROM), the domestic name contains `FLUX`, add-on is forced to `sega/mega cd`, or a CD image is loaded, the image is booted as a **Mode 1 cartridge** with the BIOS taken from the system directory instead. | CONFIRMED | `core/loadrom.c:73, 193, 290-295, 760-788` |
| Otherwise, if the header type at `$180` contains `BR`, the core enables Mega-CD hardware, selects the model from the domestic name, sets boot-from-CD (`scd.cartridge.boot = 0`), and copies exactly 128KB into `scd.bootrom`. | CONFIRMED (code + harness run) | `core/loadrom.c:790-829` |
| With boot-from-CD, the BOOT ROM is mapped at main-CPU `$000000-$01FFFF` (mirrored), so the main 68000 reset vectors come from the image. | CONFIRMED (code + harness run) | `core/cd_hw/scd.c:1598-1620` |
| TMSS boot ROM is off by default in the libretro core (`config.bios = 0`). | CONFIRMED | `libretro/libretro.c:1074` |

Implication for this project: these are **emulator-loader conditions** (Agent A's INV-009 rates them
ESTIMATED and emulator-only). The BIOS must not be shaped to satisfy them. The harness applies them
only in the opt-in `--mode bootrom`, and reports `BLOCKED` with the reason when a ROM does not meet them.
The default `--mode system` (2a) has no header requirement.

## 3. Headless options

| Option | Status | Notes / evidence |
| --- | --- | --- |
| **libretro core + tiny host (chosen).** `Makefile.libretro` builds `genesis_plus_gx_libretro.{so,dll,dylib}`; the host drives `retro_init/retro_load_game/retro_run` via Python `ctypes` (stdlib only). No window, audio or input needed. | CONFIRMED | Built on Windows 11 + MinGW-w64 GCC (`mingw32-make -f Makefile.libretro -j4`) in ~25 s, DLL ~3.5 MB, statically linked libgcc (`Makefile.libretro:521-523`). Platform auto-detect: `Makefile.libretro:19-39`. |
| Linux build with `make -f Makefile.libretro` (unix target, `.so`). | UNVERIFIED | Same makefile, `Makefile.libretro:51-55`; not run here. |
| macOS (`.dylib`). | UNVERIFIED | `Makefile.libretro:108-112`. |
| `retro_get_system_info`: `need_fullpath = true`; valid extensions include `bin`. | CONFIRMED | `libretro/libretro.c:3043-3052` |
| SDL frontend (`sdl/Makefile.sdl2`) — needs SDL2 and a window; not used. | UNVERIFIED | `sdl/` |

## 4. Observable CPU / memory state

| Observable | Via | Status | Evidence |
| --- | --- | --- | --- |
| Main 68000 work RAM `$FF0000-$FFFFFF` (64KB) | `retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM)` and memory map `68KRAM` | CONFIRMED | `libretro/libretro.c:3626-3637`, `2670-2688` |
| Sub 68000 PRG-RAM (512KB, sub-CPU `$000000`) | memory map descriptor `PRGRAM` (published via `RETRO_ENVIRONMENT_SET_MEMORY_MAPS` **only in Mega-CD mode**) | CONFIRMED (pointer obtained) | `libretro/libretro.c:2670-2688, 3584`; `core/cd_hw/scd.h:74` |
| Byte order of both buffers on little-endian builds: 16-bit words stored host-native, i.e. 68K byte `A` is at `buf[A ^ 1]`. The host un-swaps before dumping/asserting. | CONFIRMED | `core/macros.h:6, 15`; `core/cd_hw/scd.c:160-178`; build flag `-DLSB_FIRST` |
| Mega-CD mode indicator: presence of the `PRGRAM` descriptor (only published when `system_hw == SYSTEM_MCD`). | CONFIRMED | `libretro/libretro.c:2672` |
| Core log messages (format strings only; printf args not expanded by the ctypes host). | CONFIRMED | `libretro/libretro.c:3704` |
| CPU registers (PC/SR/Dn/An) of main or sub CPU | not exposed by the libretro API. `retro_serialize` contains state but in an internal, platform-dependent layout. | CONFIRMED (absent) | `libretro/link.T` exports `retro_*` only |
| Fork instrumentation: unified event ring buffer (`emu_event_*`: M68K/S68K/Z80 exec, gate-array R/W, comm registers, CDD commands, CDC DMA, frame boundaries) and `cpu_hook`. | CONFIRMED (code) / not reachable | `core/debug/emu_event.h`, push sites e.g. `core/cd_hw/scd.c:542-543, 1091-1092`, `core/mem68k.c:362, 678`. Compiled only with `HOOK_CPU=1` (`Makefile.libretro:6`, `libretro/Makefile.common:20-22`) and **not exported** from the shared library (`libretro/link.T`), and not wired into `libretro.c`. |
| Gate-array / communication registers, word RAM, VDP | no libretro accessor | CONFIRMED (absent) | — |

Future work (outside this repository): to get PC traces or sub-CPU register/comm-register traces, the
fork would need to export an accessor for the event ring buffer (e.g. a `retro_`-prefixed debug
function, or a memory-map descriptor) and be built with `HOOK_CPU=1`. Then bump `gpgx.lock`.

## 5. Harness observations at the pin

The following were observed on Windows 11 with MinGW-w64 GCC and Python 3.14 (**CONFIRMED**). The
synthetic fixture is `gpgx_harness.py make-fixture`: 128KB, hand-assembled `move.l #'OKOK',$FF0000`
followed by `bra.s *`, country `U`.

- The fixture gives `PASS` (checkpoint `startup`) with `--expect main:FF0000=4F4B4F4B` in both
  `--mode system` and `--mode bootrom`. In `--mode system` it passes even with the `BR` header bytes blanked.
- A "do-nothing" ROM (same vectors, idle loop only) gives `FAIL`. With `--expect main:FF0000=00000000`
  it fails because the value equals the power-on state, which reads `00000000` at this pin. With
  `=4F4B4F4B` it fails because the assertion does not hold.
- The power-on snapshot is taken right after `retro_load_game`, which resets the system, and before
  the first `retro_run`.
- Records emitted for PASS, FAIL, SKIP and BLOCKED pass the rules of `validate()` from the evidence
  tool on branch `agent-d/issue-6-evidence` (PR #13).
- This proves only the harness/loader path: stage *bios-loaded*, then one main-CPU checkpoint. It says
  nothing about sub-CPU startup, disc handling or compatibility of this project's BIOS. No result for
  an actual oss-mcd-bios ROM exists yet, because none is built.

## 6. Open / unverified items

- Linux/macOS builds and the harness there (UNVERIFIED; expected to work with `make`).
- Sub-CPU execution: the sub 68000 stays in reset until the main CPU releases it; harness only reads PRG-RAM.
- Region override (`--region pal/ntsc-j`) has been read in code only; it has not been exercised (UNVERIFIED).
- The power-on RAM contents at other pins or on other hosts may differ. The harness snapshots them on
  every run instead of assuming zeros.
