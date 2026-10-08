# Reuse and adaptation from related projects

This document records **ideas and engineering practices to adapt**, not code already imported. Each transfer requires an independent license/provenance review and evidence of value.

| Priority | Source | Reusable idea | Adaptation for oss-mcd-bios | Constraint / acceptance gate |
| --- | --- | --- | --- | --- |
| P0 | [Genesis-Plus-GX](https://github.com/mao2009/Genesis-Plus-GX) | Mega-CD emulator test environment | Pin a reproducible upstream/fork revision and provide a headless BIOS-only smoke harness, including CPU/register traces | Emulator license is non-commercial: use as an **external test dependency** only; do not vendor/relicense core into MIT BIOS; avoid coupling ROM to emulator quirks |
| P0 | [PSXRecompStudio](https://github.com/mao2009/PSXRecompStudio) | Synthetic fixtures, bounded E2E checkpoints, diagnostic reports, explicit compatibility states | Build original m68k/CD test fixtures, record ROM hash, emulator revision, trace assertions and minimal sanitized failure bundle | Distinguish compilation, ROM load, observed checkpoint and game boot. Do not distribute proprietary BIOS/game images |
| P0 | [PolicySharp](https://github.com/mao2009/PolicySharp) | Default-deny policies and guarded policy changes | Implement standalone repository scripts/checks for permitted build inputs, source provenance, fixture paths and release artifacts; require human-reviewed changes to allowlists | PolicySharp is Roslyn/.NET-specific; **not** directly usable for assembler or C. Avoid promising impossible perfect detection of proprietary code |
| P1 | [vn-wine](https://github.com/mao2009/vn-wine) | Gate-driven compatibility, versioned baselines and environment capability checks | Provide `doctor`-style toolchain/emulator diagnostics and progressive test tiers (structural/smoke/E2E/hardware) | Do not demand optional emulators/hardware for ordinary source checks; failures must not be silently recorded as passes |
| P1 | [clownmdemu-core](https://github.com/mao2009/clownmdemu-core) | Independent emulator implementation, portability concerns | Use as a **secondary research/test candidate** only after verifying which Sega CD capabilities exist | Its core does not automatically establish complete Mega-CD coverage; respect third-party licensing |
| P1 | [ArchitectureAnalyzer](https://github.com/mao2009/ArchitectureAnalyzer), [ArchLintCpp](https://github.com/mao2009/ArchLintCpp) | Executable architecture contracts | Document and enforce source-dir dependency boundaries via simple repo-specific static checks, later Clang tools if C/C++ host tooling appears | C# Roslyn and C++ Clang analyzers cannot enforce raw m68k assembly semantics |
| P2 | [PureSharp](https://github.com/mao2009/PureSharp), [ReadableSharp](https://github.com/mao2009/ReadableSharp) | Immutability, determinism and readable code | Apply conventions to host-side scripts, pure ROM header/checksum computation and test helpers | C# analyzer packages only apply if .NET host tools are actually introduced; avoid adding a .NET dependency just to use them |
| P2 | [PSXRecompStudio](https://github.com/mao2009/PSXRecompStudio), [vn-wine](https://github.com/mao2009/vn-wine) | CI gates, release evidence and non-secret synthetic demos | Use build reproducibility gates, provenance audit, target matrix and evidence-based release notes | ROM claims need executable tests; docs-only checks are insufficient |

## Proposed shared conventions

1. **Small and deterministic.** Prefer assembly for ROM-critical paths; allow host test tools in Python/C/Rust/C# only when justified. Pin compilers/emulators and verify binary hashes.
2. **Fail closed for releases.** Each release artifact should prove its inputs came from tracked original source and approved redistributable tools. A filename blacklist is insufficient; review provenance separately.
3. **Evidence before compatibility claims.** Use staged checkpoints in `docs/compatibility.md` with exact versions, hashes and reproducible commands.
4. **Independent implementations as oracles, not specification authority.** Compare two emulators when possible; resolve discrepancies against documented hardware measurements instead of hard-coding one emulator's behavior.
5. **No upstream code transfer by default.** For emulator or Wine-derived components, check permissions and licenses; prefer writing original wrappers and tests. In particular Genesis Plus GX states a non-commercial license, whereas this repository is MIT.
6. **Regression ratchet.** Record passing checkpoints, refuse unexplained regressions and label genuinely unverified hardware behavior instead of reporting it as supported.

## Recommended execution order

- [ ] Issue #1: verified ROM format, boot flow, sources and assumptions
- [ ] Genesis Plus GX pinned smoke harness (new issue)
- [ ] Synthetic test fixture + machine-readable compatibility evidence (new issue)
- [ ] Build provenance and allowlist gate (new issue)
- [ ] Multi-emulator test and environment diagnostics (new issue)
- [ ] Optional language-specific linters only after choosing a host tooling stack

**Status:** design-only reuse plan; no source code or infrastructure has been imported from the referenced repositories.
