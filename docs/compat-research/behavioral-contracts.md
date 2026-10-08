# Behavioral contract for BIOS services and hardware effects

The specification target is **observable software compatibility**. Internal algorithms, program structure and private caching may differ from Sega's BIOS; API-visible behavior, shared state and timing must match whatever commercial software actually relies on. Testing that one game happens to boot is not proof that all legal inputs have the same behavior.

## Contract record (one operation or separable behavior per record)

| Area | Required questions |
| --- | --- |
| Identity | Function/entry name, numbered selector if known, Main/Sub CPU context, region/model and BIOS revision scope |
| Call mechanics | Entrypoint, PC return behavior, stack/frame alignment, register width, supervisor state, calling convention |
| Preconditions | Power-on state, initialized subsystems, RAM ownership, prior command completion, tray/disc present |
| Inputs | Exact register/memory arguments, widths, valid/invalid ranges, pointers, pointer alignment, endian assumptions |
| Outputs | Return registers, condition codes, preserved registers, output memory layout, status codes |
| Side effects | RAM modifications, communication registers, gate array, CDC/CDD, LEDs, audio, interrupts, queues |
| Asynchrony | Immediate vs pending completion, polling signals, callbacks, interrupt delivery/acknowledgment |
| Timing | Ordered-before/after constraints and measurable tolerances; do not invent cycle-accurate numbers |
| Errors | Invalid args, media errors, absence of disc, empty/full queues, repeated calls, recovery and retries |
| State machine | States, transitions, forbidden transitions, interactions with other BIOS operations |
| Cross-region | JP/US/EU profile and hardware video-mode dependencies, determined by tests |
| Evidence | Observation references, test IDs, source lineage, provenance disposition and confidence |
| Regression | Golden traces, bounded invariant assertions, commercial title scenarios, emulator/hardware versions |

### Contract state and confidence are orthogonal

Use independent status fields:

- `spec_status`: UNCONFIRMED / HYPOTHESIS / CORROBORATED / OBSERVED / VERIFIED (meaning must be scoped)
- `provenance_status`: REVIEW-PENDING / APPROVED / RESTRICTED / INADMISSIBLE
- `implementation_status`: NOT-STARTED / PARTIAL / IMPLEMENTED / TESTED
- `compatibility_status`: NOT-RUN / BLOCKED / FAIL / PASS-SCENARIO

Do not auto-promote an HLE-reported behavior to verified hardware behavior. Do not mark a test pass when a required fixture is absent.

## Example: unknown CD-sector service (illustrative, NOT an API claim)

- ID: `API-CD-READ-CANDIDATE`; related parent issue #24.
- Entry: *unknown*: do not invent an address or command code.
- Inputs: destination, sector selection, length and transfer mode: **to be measured**.
- Output: status, bytes transferred and completion signal: **to be measured**.
- Candidate corner cases: disc absent, track boundary, repeated read request, status polled before completion, DMA ownership change, reentrant call.
- Observable outputs: return register snapshots, changed RAM ranges, CDC status, event ordering, timestamps.
- Evidence: synthetic disc test plus, where legally feasible, a black-box reference run; corroborate on two different emulators.
- Permitted implementation: any independently written algorithm that matches the behavior contract for the tested scenarios.

No number, opcode, register address, memory length or timing constant in this example is normative.

## Invariants for any service

1. API A must not silently corrupt RAM not declared as its output or scratch area.
2. Preserved registers must remain unchanged under test, including failing paths.
3. Completion and status polling must be consistent; no false completion prior to transfer.
4. Multiple calls and interrupts must follow observed state-machine order.
5. Power/reset/reopen cycles restore the expected externally visible state.
6. Where title B exhibits different expectations, record a distinct evidence-backed contract variant, not a hardcoded title name without justification.
7. Known supported scenarios must continue to pass after every ABI/behavior change.

## Multi-region contract rules

Track **game release region**, **emulated console region**, **video timing (NTSC/PAL)**, **BIOS profile**, **emulator model** and **physical model** separately. They are not synonyms. An emulator's selection UI does not prove a physical region-free BIOS is possible.

Default design: region-independent services and a small verified region behavior layer. Explicit JP/US/EU images may be needed even if a future “universal” ROM is feasible.

## Relation to issue hierarchy

- #22: reset and boot contracts
- #23: ABI and jump table contracts
- #24: disc/CDD/CDC contracts
- #25: Main/Sub and Word RAM contracts
- #26: interrupts and user callbacks
- #27: backup RAM
- #28: CD-DA, PCM and associated media controls
- #29: region and profile compatibility

The parent issues **do not mean** the listed APIs or their addresses are confirmed; PR #16/#21 remain under review.
