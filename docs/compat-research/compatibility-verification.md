# Evidence-based commercial game compatibility

## Staged evidence

| Tier | What actually ran | Allowed claim |
| --- | --- | --- |
| T0 | Documentation/license checks | Source-level sanity only |
| T1 | Assembler/linker plus ROM structural validator | Reproducibly built image |
| T2 | Real pinned Genesis Plus GX emulator core with reset trace | Startup checkpoint observed in that emulator |
| T3 | Independent emulator with same original fixture | Emulator differential agreement or mismatch |
| T4 | Permitted commercial title in a controlled local environment | Named game edition reached measured checkpoint |
| T5 | Safe real-hardware test | Named hardware model passed stated scenario |
| T6 | Audio, input, save/load, continued play and completion test | Named game's tested path is playable/completion tested |

T1 ≠ T2, mocks ≠ real GPGX, T4 ≠ all games. No proprietary game/BIOS data may be checked into CI, Git or uploaded logs.

## Trace metadata contract

Collect scenario ID; outcome PASS/FAIL/SKIP/BLOCKED; emulator and core commit SHA; BIOS SHA-256; fixture ID and source hash; CPU/register/event observations; region of disc, console and video clock; model; elapsed logical sequence; environment capability; expected and actual assertion; first divergence; sanitized evidence path; reviewer status. Undefined data stays UNKNOWN/null, never invented.

## Per-game matrix

Each row identifies title, exact release/edition, region, input legal-use state, emulator+SHA, BIOS build+hash, mode/model, boot checkpoint, audio, video, input, save/load, persistence, gameplay duration, end-to-end checkpoint, failure class, owner and evidence link.

Never mark game as fully supported solely because a splash/menu appears. Treat version/region variants separately. Game-specific workarounds should be a last resort; first seek general contract fixes.

## Regression discipline

- Add smallest original synthetic reproducer for every observed compatibility bug.
- Preserve previously working game scenarios.
- Distinguish emulator bug, BIOS bug, game-region mismatch and unknown.
- If normalizing timestamps or status fields for differential comparison, prove the normalization cannot hide a game-relevant difference.
- For fail-closed CI: do not convert unavailable reference inputs, OOM failures or absent emulator cores into PASS.

## Relationship to pending PRs

PR #11 toolchain, #13 evidence model, #14 doctor/CI, #15 GPGX harness, #16 specification and #21 gap audit may all be unmerged or under review. This document defines intent and does not supersede their implementation schemas or assert their tests ran.
