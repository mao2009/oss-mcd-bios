# Build-input policy and manual provenance review

The automated gate (`tools/policy/policy_check.py`, policy in `policy/allowlist.toml`, CI in `.github/workflows/policy.yml`) is a **default-deny heuristic**. It reduces the chance that obviously unsuitable material enters a build. It **does not and cannot detect all unauthorized or proprietary material**: copied disassembly, hand-transcribed ROM data, or text-encoded binaries can pass it. A green policy run is not a provenance or licensing approval. Manual review, as described below, is always required.

## What the gate checks

Run locally with `python -I -B tools/policy/policy_check.py` (Python 3.11+, stdlib only; use `-B` so `__pycache__` is not written under `tools/`).

- Tracked files are listed with `git ls-files`. Every tracked file must match a location in the policy (`source`, `fixture`, `tool`, `build`, `docs`, `meta`); anything else is rejected (default deny).
- Files under `artifact` locations (`build/`, `dist/`) must never be tracked.
- Symlinks and submodules are rejected.
- Denied extensions (ROM, disc image and archive formats such as `.bin`, `.rom`, `.gen`, `.smd`, `.iso`, `.cue`, `.chd`, `.zip`) are rejected anywhere, case-insensitively.
- Every tracked file must be UTF-8 text without NUL bytes and at most `max_file_bytes`. Binary files are rejected and reported as ROM-like when a Mega Drive (`SEGA` at 0x100) or Mega-CD (`SEGADISCSYSTEM`) header is found. `.md` is not a denied extension because it is also Markdown; `.md` files must pass this text check like every other file.
- Untracked files, including git-ignored ones, and uncommitted modifications under build-input locations (`src/`, `tests/`, `tools/`, top-level `Makefile`) are rejected, as are uncommitted edits to the policy file itself.
- The policy file must be a tracked file in the repository.

Exit code `0` means no violation was detected, `1` means violations were found, and `2` means the policy or git state could not be read or validated. CI treats every non-zero exit as failure (fail closed).

## Not yet a merge gate

On its own, a failing `Policy gate` workflow only marks the pull request red. It **cannot block a merge** until a maintainer enables branch protection on `main` and adds the `policy` job as a required status check. Code Owner review is enforced only through the same setting. Contributors and automation cannot change it. Until a maintainer enables it, reviewers must check the workflow result and the Code Owner approval by hand before merging.

## If the gate fails

Report the violation in the pull request and remove or replace the offending input. **Do not widen the allowlist to make a check pass.** A policy change is acceptable only when the new location or file type is genuinely required and has gone through the review below in its own, clearly labelled pull request.

## Changing the policy

`.github/CODEOWNERS` assigns `policy/`, `tools/policy/`, all workflows under `.github/workflows/`, `arch/rules.toml`, `CODEOWNERS` and this document to the maintainer. This is enforced only when branch protection on `main` requires Code Owner review (see above).

A pull request that changes the policy must explain:

1. Which location, extension or limit changes, and why the project needs it.
2. What material is expected to enter through the change, and its origin.
3. Why a narrower alternative (a more specific path, a generated file, an external test dependency) is not sufficient.

## Manual licensing and provenance review

The reviewer checks every contribution, not only policy changes, against [provenance rules](provenance.md):

1. **Authorship.** Code and data are independently written. No Sega BIOS dumps, extracted assets, binary patches derived from copyrighted ROMs or verbatim disassembly.
2. **Sources.** Hardware facts cite public documentation or original experiments. Uncertain behavior is labelled as a hypothesis.
3. **Third-party material.** The license is identified and confirmed MIT-compatible before integration, with attribution recorded. Emulators with incompatible licenses (for example Genesis Plus GX, non-commercial) stay external test dependencies and are never vendored.
4. **Fixtures.** Test fixtures are synthetic and generated from tracked source where possible. Reference binaries stay outside the repository and outside CI.
5. **Release artifacts.** Artifacts are built in CI from a clean checkout that passed this gate. Manually produced binaries are not published.

When provenance is uncertain, open an issue and do not merge until it is resolved. Clean-room process and this review reduce, but do not eliminate, legal risk.
