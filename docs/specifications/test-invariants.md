# ROM structural invariants

[invariants.json](invariants.json) is the machine-readable source of truth for the ROM validator. This page explains it. A structural check proves only the **ROM-built** stage in [compatibility.md](../compatibility.md). It does not prove that the image loads or boots.

## Rules for the validator

* Fail the build only for `enforceable: true`. Report all other entries as warnings, with their `status`.
* `enforceable: true` is allowed only when `status` is `CONFIRMED`. The validator should reject an invariants file that breaks this rule.
* `scope` is informational: `hardware`, `software-compat`, or `emulator:<name>`. An `emulator:*` invariant protects the image's behaviour in that emulator. It is **not** a hardware claim.
* Offsets are image-relative and in decimal in the JSON. Multi-byte reads are big-endian. `mask` is applied before comparison; `16777215` (`0xFFFFFF`) models the 68000's 24-bit address bus.

## Check vocabulary

| `type` | Parameters | Passes when |
| --- | --- | --- |
| `size_equals` | `bytes` | file length == `bytes` |
| `u32_even` | `offset`, `mask` | `(u32(offset) & mask) % 2 == 0` |
| `u32_range` | `offset`, `mask`, `min`, `max` | `min <= (u32(offset) & mask) <= max` |
| `u32_in_ranges` | `offset`, `mask`, `ranges` (list of inclusive `[lo, hi]`) | the masked value lies in at least one range |
| `u32_even_each` | `start`, `end` (inclusive), `step`, `exclude`, `mask` | `u32_even` holds for every offset in the sequence except `exclude` |
| `u32_each_in_ranges` | `start`, `end`, `step`, `exclude`, `mask`, `ranges` | `u32_in_ranges` holds for every offset in the sequence except `exclude` |
| `u16_in` | `offset`, `values` | `u16(offset)` is one of `values` |
| `bytes_equal` | `offset`, `ascii` | the bytes at `offset` equal the ASCII string |
| `bytes_equal_any` | `offsets`, `ascii` | `bytes_equal` holds at one or more of the offsets |
| `bytes_not_in` | `offset`, `length`, `ascii_values` | the `length` bytes at `offset` equal none of the strings |

## Current list

| ID | Summary | Status | Enforced |
| --- | --- | --- | --- |
| INV-001 | Size exactly 131072 bytes | CONFIRMED | yes |
| INV-002 | Initial PC even | CONFIRMED | yes |
| INV-003 | Initial PC in `0x000008..0x01FFFE` | CONFIRMED (derived) | yes |
| INV-004 | Initial SSP even | CONFIRMED (derived) | yes |
| INV-005 | Vectors 2–63 even, except `0x070` | CONFIRMED (derived) | yes |
| INV-006 | No GPGX model string at `0x120` | CONFIRMED (emulator:gpgx) | yes |
| INV-007 | SSP is 0 or in Work RAM | ESTIMATED | no |
| INV-008 | `"SEGA"` at `0x100` | ESTIMATED | no |
| INV-009 | `"BR"` at `0x180` (GPGX cartridge-load detection) | ESTIMATED | no |
| INV-010 | `"BOOT"` at `0x124`/`0x128` (PicoDrive cartridge-load detection) | ESTIMATED | no |
| INV-011 | `0x070` high word is `0x00FF` or `0xFFFF` | UNCONFIRMED | no |
| INV-012 | Vectors point to ROM or Work RAM | ESTIMATED | no |

These invariants do **not** cover provenance: they cannot detect copied Sega code. That needs the separate build-provenance gate in [reuse-from-projects.md](../reuse-from-projects.md).

## Candidates not yet expressible

* A Main-side jump table at `0x280` (R-25 / OQ-7) is blocked on the clean-room decision.
* Sub-CPU program image layout (vector table and the `$5E80-$5FFF` common area after copying to PRG-RAM) depends on our own link layout. Define it when the toolchain issue lands.
