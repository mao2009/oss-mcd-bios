# Specification gap triage

## Baseline and limitations

PR #21 reported LC **193/406 = 47.5%**, a count of currently enumerated commercial-game specification claims. This is **not** implementation progress, number of working games, completeness of all requirements, or probability of success. Some hardware fields (VDP/Z80/PCM, etc.) are not in the denominator. The reported script was rerun to reproduce arithmetic, not to independently audit every claim. This document does not change those results.

Commercial retail-game compatibility, starting with JP games, is the product goal. Self-authored CD boot and minimal ROM startup are diagnostics only.

## Independent classification axes

| Axis | Values | Purpose |
| --- | --- | --- |
| Domain | Boot / ABI / CD / Memory / IRQ / BURAM / Audio / Region / Other | Parent owner, #22–#29 |
| Impact | BLOCKING / COMMON / TITLE-SPECIFIC / POSTPONABLE / UNDETERMINED | Evidence-based priority |
| Technical support | UNKNOWN / HYPOTHESIS / SINGLE-SOURCE / CORROBORATED / MEASURED / VERIFIED-IN-SCOPE | Evidence strength |
| Provenance | APPROVED / REVIEW-PENDING / RESTRICTED / INADMISSIBLE | Source admissibility |
| Experiment | DOCUMENT / EMULATOR / REFERENCE-BLACKBOX / OWN-HARDWARE / NO-KNOWN-TEST | Available test |
| Implementation | UNSTARTED / PARTIAL / IMPLEMENTED / TESTED | Actual code progress |
| Region | JP / US / EU / ALL-TESTED / UNKNOWN | Proven applicability |

Do not assign guessed values as established truth. Multiple emulators may share lineage. A functional behavior observation is different from permission to reuse the source of the observation.

## Triage on the critical path of one JP commercial title

1. Identify a legitimately testable JP release and precise scenario with a defined checkpoint.
2. Obtain **permitted** execution observations of the software's calls and hardware effects.
3. Build the dependency chain from boot, CD read and Main/Sub communication through menu, audio, input, save/load and gameplay.
4. Identify earliest reproducible divergence. Classify as BIOS API semantics, RAM side effect, CD, IRQ/timing, region, emulator or unknown.
5. Derive an original synthetic test for the generic behavior, not a title-specific patch.
6. Implement independently, rerun the synthetic test and all previously verified games.
7. Promote only the actually observed test stage.

When legally usable discs/reference environment are unavailable, record BLOCKED, never PASS.

## Example per-gap record

- GAP-ID:
- Parent Issue:
- Required observable behavior:
- Game/release/region/scenario:
- Sources with exact URL and revision:
- Technical status / permission status / lineage:
- Missing input/output/state/timing detail:
- Competing hypotheses:
- Distinguishing synthetic test:
- Need permitted commercial/reference BIOS environment?:
- Requires real hardware?:
- Observation/evidence hash:
- Outcome and independent reviewer:
- Next action:

## Prioritize completion of behavior, not count inflation

The most useful metric is how many **necessary behavioral contracts** are verified for a given game scenario, plus breadth of independently tested titles. PR #21's 47.5% stays an audit baseline, with uncovered and unenumerated regions transparently labelled.
