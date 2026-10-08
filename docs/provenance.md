# OSS reuse, rights and provenance rules

This project aims to distribute an independently redistributable Mega-CD / Sega CD replacement BIOS, **not Sega-owned ROM code or assets**. Reuse appropriately licensed OSS rather than reinventing it. The BIOS may consist of original code plus audited third-party code or modifications with their own notices/terms: "independent firmware" must **not** mean "all code written from scratch."

## Reuse order

1. **DIRECT:** reuse an existing technically compatible OSS routine unchanged, where its *actual file and dependencies* allow our proposed firmware distribution.
2. **ADAPTED:** legally port/modify suitable code for the 68000, assembler ABI, ROM map and hardware boundary; document what changed.
3. **REFERENCE_ONLY:** take behavior, API contracts and test inspiration from published research or compatible emulators, without copying source or proprietary data. A line-by-line translation is not independent merely because the language changes.
4. **NEW:** implement genuinely missing or unsuitable behavior and document why existing code cannot be reused.

Technical fit is separate from permission to copy. An HLE emulator model is not automatically a faithful BIOS or CD drive model.

## Never import

- Proprietary Sega or third-party BIOS dumps, extracted graphics/audio, copied disassembly, copyrighted disc sectors, game assets, patches containing protected bytes or illegal firmware derivatives.
- Source with missing/unclear rights, non-commercial restrictions incompatible with our planned MIT distribution, or obligations which the ROM/source/release cannot fulfill.
- Copyleft or exception-bearing code without reviewing the actual integration/distribution scenario and honoring its source/binary/notice duties. Repository-level license badges alone are not sufficient.

**Important:** [Genesis Plus GX](https://github.com/libretro/Genesis-Plus-GX/blob/master/LICENSE.txt) has a *custom default license with non-commercial and no-sale restrictions*, not a general MIT/GPL grant. Its `core/cd_hw` source MUST NOT be embedded in MIT-distributed firmware without verified file-specific exception or permission from the applicable rights holder. External use as a validation emulator is separate and also subject to its applicable terms. Do not assume third-party emulator output proves target hardware.

## Required human-reviewed import record

Before committing an external file, translated routine or substantial fragment to a distributable firmware source, CI binary or release:

- Source repository URL, immutable 40-hex commit, exact file path, blob hash; upstream authors and other rightsholders.
- Exact file header/explicit license and its text, linked/generated/transitive dependencies, nested origins and exceptions.
- Use mode: DIRECT, ADAPTED, REFERENCE_ONLY, or REJECTED.
- Legal assessment: copying, translating, altering, linking and source/binary **ROM distribution**, commercialization, attribution, copyright/NOTICE inclusion, source disclosure/modification record and third-party license separation.
- Technical fit: 68000 ABI, toolchain dialect, ROM mapping, interrupt/Word RAM/CSDD-CDC responsibilities, boundary conditions.
- Status: APPROVED / PENDING / RESTRICTED; reviewer and review date, rationale, related Issue/PR, exact validation/test evidence.
- Store required full upstream licenses, permission/copyright notices and modifications in source/release distribution as their actual licenses require. Never silently relicense external source as project-owned MIT.

Pending/restricted candidates may be documented but **not** embedded or released. When provenance is uncertain, create an Issue and stop the import before merge. No automated check or wording in a report substitutes for the rights holder's license or a human's actual approval.

## Test/reference safety

- Prefer public hardware descriptions, synthetic homebrew fixtures and observable emulator traces. Record facts with source/commit, evidence strength and unresolved discrepancies.
- Keep lawful private reference BIOSes and licensed commercial disc data out of Git, CI, release builds and logs. Do not copy proprietary traces containing protected bytes.
- Emulator harnesses and test tools retain their separate licenses; if tools/binaries are shipped, audit their distribution too.
- Verify reset vectors, CDD/CDC and CD-DA behavior in pinned emulator targets; distinguish source review, ROM build, emulator boot, disc read, homebrew boot and commercial compatibility. A documentation-only green CI is not BIOS functionality evidence.
- The project is not affiliated with or endorsed by Sega. Trademarks belong to their respective owners.

See [candidate inventory](reuse-inventory.md) and [architecture](architecture.md). This policy is not a legal warranty.
