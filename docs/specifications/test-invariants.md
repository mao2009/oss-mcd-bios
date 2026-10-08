# ROM structural invariants

[invariants.json](invariants.json) is the machine-readable source of truth for the ROM validator. This page is its **normative schema**: a validator should implement exactly what is written here. A structural check proves only the **ROM-built** stage in [compatibility.md](../compatibility.md). It does not prove that the image loads or boots.

## 1. File format (`schema_version` 2)

The file is UTF-8 JSON. The top level is an object:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `schema_version` | integer | yes | Format version of this file, currently `2`. The validator must reject any version it does not implement. Version history: `1` was the initial draft; `2` added the `PROJECT-RULE` status, the `project` scope and the enforceability rule in §2. |
| `description` | string | no | Human-readable summary |
| `sources_doc` | string | no | Repository path of the source register |
| `invariants` | array of objects | yes | The invariants (§2) |

The validator should ignore unknown top-level fields.

## 2. Invariant object

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string matching `^INV-[0-9]{3}$` | yes | Stable identifier, unique in the file. IDs are never reused. |
| `description` | string | yes | What must hold, and why |
| `status` | `"CONFIRMED"` \| `"ESTIMATED"` \| `"UNCONFIRMED"` \| `"PROJECT-RULE"` | yes | The first three are evidence labels, defined in [README.md](README.md). `PROJECT-RULE` means the requirement is our own build-quality policy, not a claim about hardware or emulator behaviour. |
| `enforceable` | boolean | yes | `true`: a failing check fails the build. `false`: report a warning that includes `id` and `status`. |
| `scope` | `"hardware"` \| `"software-compat"` \| `"project"` \| `"emulator:<name>"` (`<name>` matches `^[a-z0-9-]+$`) | yes | What the invariant protects. An `emulator:*` scope describes one emulator's behaviour and is **never** a hardware claim. |
| `source` | array of strings | yes | Evidence references: section IDs in these docs (`rom-layout.md#R-12`) or source IDs from the register with a location (`E-GPGX core/loadrom.c:422-442`). |
| `check` | object | yes | Machine check (§3) |

**Enforceability rule.** The validator must reject the file as malformed if any entry breaks this rule. `enforceable: true` is allowed only when either:

* `status == "CONFIRMED"` **and** `scope == "hardware"`, or
* `status == "PROJECT-RULE"`.

So emulator-scoped, ESTIMATED and UNCONFIRMED entries are always advisory.

## 3. `check` vocabulary

General rules:

* Offsets and lengths are image-relative non-negative integers, written in decimal in JSON.
* `u16(o)` and `u32(o)` read big-endian values at offset `o`.
* `mask` is optional and defaults to `0xFFFFFFFF`. When present it is ANDed with the value before comparison; `16777215` (`0xFFFFFF`) models the 68000's 24-bit address bus.
* Ranges are inclusive `[lo, hi]` pairs.
* Sequences run `start, start+step, …` up to and including `end`, skipping every offset listed in `exclude`, which is optional and defaults to `[]`.
* `ascii` strings are compared byte-for-byte as ASCII, with no terminator.
* If a read would go past the end of the image, the check **fails**. It does not raise an error.
* An unknown `type` is a schema error, and the file must be rejected.

| `type` | Parameters | Passes when |
| --- | --- | --- |
| `size_equals` | `bytes` | image length == `bytes` |
| `u32_even` | `offset`, `mask?` | `(u32(offset) & mask) % 2 == 0` |
| `u32_range` | `offset`, `mask?`, `min`, `max` | `min <= (u32(offset) & mask) <= max` |
| `u32_in_ranges` | `offset`, `mask?`, `ranges` | the masked value lies in at least one range |
| `u32_even_each` | `start`, `end`, `step`, `exclude?`, `mask?` | `u32_even` holds at every offset of the sequence |
| `u32_each_in_ranges` | `start`, `end`, `step`, `exclude?`, `mask?`, `ranges` | `u32_in_ranges` holds at every offset of the sequence |
| `u16_in` | `offset`, `values` | `u16(offset)` is in `values` |
| `bytes_equal` | `offset`, `ascii` | the bytes at `offset` equal `ascii` |
| `bytes_equal_any` | `offsets`, `ascii` | `bytes_equal` holds at one or more of `offsets` |
| `bytes_not_in` | `offset`, `length`, `ascii_values` | the `length` bytes at `offset` equal none of `ascii_values`. Each value must be exactly `length` bytes, or the file is a schema error. |

## 4. Validator output

For every invariant, report `id`, `status`, `scope`, `enforceable` and pass/fail. Exit non-zero only when at least one `enforceable: true` invariant fails, or the file is malformed.

## 5. Current list

| ID | Summary | Status | Scope | Enforced |
| --- | --- | --- | --- | --- |
| INV-001 | Size exactly 131072 bytes | CONFIRMED | hardware | yes |
| INV-002 | Initial PC even | CONFIRMED | hardware | yes |
| INV-003 | Initial PC in `0x000008..0x01FFFE` | CONFIRMED (derived) | hardware | yes |
| INV-004 | Initial SSP even | CONFIRMED (derived) | hardware | yes |
| INV-005 | All vectors 2–63 even, except `0x070` | PROJECT-RULE | project | yes |
| INV-006 | No GPGX model string at `0x120` | CONFIRMED | emulator:gpgx | no |
| INV-007 | SSP is 0 or in Work RAM | ESTIMATED | hardware | no |
| INV-008 | `"SEGA"` at `0x100` | ESTIMATED | software-compat | no |
| INV-009 | `"BR"` at `0x180` (GPGX cartridge-load detection) | ESTIMATED | emulator:gpgx | no |
| INV-010 | `"BOOT"` at `0x124`/`0x128` (PicoDrive cartridge-load detection) | ESTIMATED | emulator:picodrive | no |
| INV-011 | `0x070` high word is `0x00FF` or `0xFFFF` | UNCONFIRMED | hardware | no |
| INV-012 | Vectors point to ROM or Work RAM | ESTIMATED | hardware | no |

These invariants do **not** cover provenance: they cannot detect copied Sega code. That needs the separate build-provenance gate in [reuse-from-projects.md](../reuse-from-projects.md).

## 6. Candidates not yet expressible

* A Main-side jump table at `0x280` (R-25 / A-11, UNCONFIRMED) is blocked on the clean-room decision in OQ-7.
* Sub-CPU program image layout (vector table and the `$5E80-$5FFF` common area after copying to PRG-RAM) depends on our own link layout. Define it when the toolchain issue lands.
