# Sources, confidence and provenance register

This is a **starting inventory**, not proof that each source is legally reusable or technically correct. First-party claims are attributed to the authors and sources. Statements about accessibility or licensing should be rechecked at the exact commit or page revision used in an implementation.

## Research starting points

| ID | Source | Potential evidence | Use status in this project |
| --- | --- | --- | --- |
| S-CPU | [Motorola/NXP M68000 user manual](https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf) | CPU vectors, exception semantics, alignment, instruction behavior | Vendor-published reference; cite facts, do not rehost manual. Confirm revision and applicable model. |
| S-MEGADEV | [MegaDev](https://github.com/drojaazu/megadev) and its [docs](https://github.com/drojaazu/megadev/tree/main/docs) | Homebrew boot, API surface hypotheses, headers, conventions | Project is MIT, but some knowledge may come from reverse engineering: provenance assessment required **per claim**. Do not equate permissive repo license with provenance clearance. |
| S-GPGX | [Genesis Plus GX upstream](https://github.com/ekeeke/Genesis-Plus-GX) and [own fork](https://github.com/mao2009/Genesis-Plus-GX) | Hardware behavior and LLE integration; test harness | Source has non-commercial restrictions. External test dependency; no vendoring into MIT BIOS. Record exact revision/patches. |
| S-PICO | [PicoDrive](https://github.com/notaz/picodrive) | Independent emulator implementation for corroboration | Review licenses/lineage and pin revision; do not copy code. Its 32X HLE does **not** establish Mega-CD BIOS HLE. |
| S-CLOWN | [ClownMDEmu core](https://github.com/Clownacy/clownmdemu) and [maintainer HLE explanation](https://clownacy.wordpress.com/2023/10/13/clownmdemu-high-level-emulation/) | Architectural example of bypassing Mega-CD BIOS with emulator HLE | **Methodological use only pending #17**. Do not copy ROM, constants, precise ABI contracts or code based only on this source. |
| S-CLOWN-BOOT | [ClownMDEmu minimal boot ROM example](https://github.com/kirisamemofo/clownmdemu-mcd-boot) | Evidence that a separate minimal boot-ROM approach exists | Provenance review **required**: related project history explicitly describes reverse engineering Sega BIOS. No code, asset or binary transfer pending review. |
| S-CLOWN-REPORT | [ClownMDEmu v1.1 report](https://clownacy.wordpress.com/2025/02/10/clownmdemu-v1-1/) | Examples of CDC repeated-call edge cases, CD FIFO and fader research limitations | *Candidate experimental questions only*. Author describes learning from original BIOS disassembly for some topics. Confirm behavior independently. |
| S-PSX | [PSXRecompStudio](https://github.com/mao2009/PSXRecompStudio) | Test orchestration, evidence bundles, bounded checkpoints | Transfer design and test *practice*, not MIPS/PS1 specification. |
| S-WINE | [vn-wine](https://github.com/mao2009/vn-wine) | Tiered compatibility gates, environment doctor, synthetic fixtures | Transfer process, not Mega-CD hardware claims. |

**Do not use third-party-hosted scans marked “CONFIDENTIAL / PROPERTY OF SEGA” as implementation authority until Issue #17 is explicitly settled.** A URL or a paraphrase is not itself a provenance clearance.

### Especially important provenance trap

The ClownMDEmu author explains an emulator-resident HLE strategy, but the [Sonic CD boot write-up](https://clownacy.wordpress.com/2023/10/11/clownmdemu-booting-sonic-cd/) expressly reports consulting disassemblies of a commercial game and the Mega-CD BIOS. The [v0.7 article](https://clownacy.wordpress.com/2024/04/01/clownmdemu-v0-7/) describes a more developed stub BIOS resulting from studying the original BIOS. The [v1.1 write-up](https://clownacy.wordpress.com/2025/02/10/clownmdemu-v1-1/) mentions original BIOS disassembly for fader detail. Therefore:

- **Good to learn:** test methodology, boundary between HLE and physical ROM, kinds of observable failure and candidate questions to investigate.
- **Not automatically safe to transplant:** implementation flow/structure, copyrighted data, call tables, timing constants, graphics, disassembled instructions or reconstructed ROM code.
- **Must separately verify:** whether an individual *functional behavior* can be established from an authorized public specification or independent black-box experiment.

A source can be technically useful but inadmissible for implementation under the project's currently chosen review policy. The restriction is precautionary; it is **not** a legal conclusion that reverse engineering is universally unlawful.

## Evidence and origin labels

Every claim must have **two independent fields**:

| Axis | Values | Question |
| --- | --- | --- |
| Technical confidence | UNKNOWN / HYPOTHESIS / SINGLE-SOURCE / CORROBORATED / MEASURED / VERIFIED-IN-TARGET | How well is behavior established? |
| Provenance disposition | APPROVED / REVIEW-PENDING / RESTRICTED / INADMISSIBLE | May the development team adopt this basis? |
| Scope | emulator:<id>@<sha> / jp-bios:<revision> / region:<id> / hardware:<model> / game:<id> | To what environment does the claim apply? |
| Source lineage | independent / shared ancestry / unknown | Are “two sources” actually independent? |

A claim marked CORROBORATED but REVIEW-PENDING **must not** become enforceable BIOS behavior solely from the reviewed source. A TEST PASSED on an emulator does **not** mean VERIFIED-IN-TARGET on real hardware.

## Acceptance steps for a technical claim

1. Identify the exact claim (one input/output/state/timing condition, not an entire subsystem).
2. Record source IDs, URL, revision, path and any restrictions or inaccessible parts.
3. Identify whether upstream emulators share data, code or reverse-engineering lineage.
4. Prefer a permitted independent source or a self-authored black-box test.
5. Record raw observations **without distributing proprietary reference code or ROM images**.
6. Write a behavioral contract in the project's own words; review for non-literal copying.
7. Have a reviewer separate from the observer inspect the evidence and disposition.
8. Promote technical status only after the required target environment has been tested.

## No contamination in repo

- Never check in Sega BIOS images, commercial disc sectors, game binaries or disassemblies.
- Never copy third-party emulator/HLE functions into the BIOS and merely rename variables.
- Keep legally obtained reference files outside Git, CI and uploaded diagnostic bundles.
- Document how a reference was acquired and tested without embedding its bytes.
- Make a policy exception only through maintainers; never by autonomous agent.

## Source register template

| Field | Required |
| --- | --- |
| source_id, source_type | yes |
| title, author/maintainer | yes |
| URL, exact version/commit/page | yes |
| observed fact / claim IDs | yes |
| lineage and legal/provenance caveats | yes |
| what was *not* inspected | yes |
| reviewer, review date and disposition | yes |
