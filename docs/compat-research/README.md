# Commercial-game BIOS compatibility research

Status: **research method and work plan**, not a confirmed hardware specification or a completed compatibility test. Updated: 2026-10-08.

## Mission and scope

oss-mcd-bios aims to run **commercial Mega-CD/Sega CD titles without requiring a proprietary BIOS**. Japanese retail releases are the minimum intended region; North American and European releases, cross-region operation and eventually real hardware are long-term goals. All known games working is an **aspirational** endpoint, not a claim or a release deadline. Starting a homebrew disc is a diagnostic milestone, not project completion.

**Compatibility means observable behavior, not internal algorithm identity.** A different algorithm is permitted only when games see the required API, memory, timing, interrupt, audio, disc, save and error behavior. A passing title is evidence for that title and scenario, never for all titles.

The delivered product is a **redistributable 68000 BIOS ROM**, which must run through the ordinary BIOS-loading path in independent emulators and eventually on compatible hardware. Emulator-resident HLE can be a **research oracle/candidate** but is not the distributable BIOS.

## Reading order

1. [Source inventory and provenance](sources-and-provenance.md): where information may be found, which sources are contaminated/conditional, and what can be transferred.
2. [Behavioral contracts](behavioral-contracts.md): reproducible API and hardware-contract template.
3. [Investigation techniques](experimental-methods.md): emulator comparison, external HLE, black-box, game-side analysis, self-authored probes and fuzzing.
4. [Gap triage matrix](gap-closure-matrix.md): convert unverified specifications into executable work without inflating percentages.
5. [Experiment catalog](experiment-catalog.md): specific experiments proposed for API, CD, CPU, save and regional behavior.
6. [Compatibility verification](compatibility-verification.md): legal fixtures, reproducibility, trace shape, comparison and pass criteria.
7. [Priorities and decisions](priorities-and-gates.md): staged execution strategy toward JP retail games and region-independent architecture.

## Relationship to existing work

- [docs/architecture.md](../architecture.md), [docs/provenance.md](../provenance.md), [docs/compatibility.md](../compatibility.md) remain the higher-level project policies.
- Specification source material is under PR [#16](https://github.com/mao2009/oss-mcd-bios/pull/16) and audit material under PR [#21](https://github.com/mao2009/oss-mcd-bios/pull/21); **neither is assumed merged, approved or legally cleared**.
- Issue [#17](https://github.com/mao2009/oss-mcd-bios/issues/17) governs unresolved provenance policy; [#20](https://github.com/mao2009/oss-mcd-bios/issues/20) tracks specification unknowns.
- Feature parent issues: [#22 boot](https://github.com/mao2009/oss-mcd-bios/issues/22), [#23 API](https://github.com/mao2009/oss-mcd-bios/issues/23), [#24 CD](https://github.com/mao2009/oss-mcd-bios/issues/24), [#25 memory](https://github.com/mao2009/oss-mcd-bios/issues/25), [#26 interrupts](https://github.com/mao2009/oss-mcd-bios/issues/26), [#27 saves](https://github.com/mao2009/oss-mcd-bios/issues/27), [#28 audio](https://github.com/mao2009/oss-mcd-bios/issues/28), [#29 regions](https://github.com/mao2009/oss-mcd-bios/issues/29).
- Build/emulator instrumentation work remains in separate PRs; this directory introduces **no runnable ROM, test success or changes to permission policy**.

## Vocabulary

| Term | Meaning |
| --- | --- |
| Source observation | What a reference or implementation actually says, scoped to exact version/path |
| Hypothesis | Proposed behavior not independently validated |
| Experiment observation | A recorded execution outcome (with environment, input, trace and uncertainties) |
| Behavioral contract | Inputs, outputs, persistent state, timing, errors and externally visible effects the BIOS promises |
| Implementation | Source code in oss-mcd-bios; can differ internally from a reference |
| Verification | Repeatable evidence that specified contract assertions hold in defined environments |
| Provenance gate | Separate review of the *right to use* source materials; technical agreement does not clear licensing |
| Game compatibility | Measured game/scenario behavior, not count of documented API names |

**Documentation does not authorize use of a restricted reference.** Unclear origins or permissions are blockers for importing implementation details until #17 is resolved by the maintainer.
