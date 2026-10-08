# Mega-CD spec-coverage matrix (integration of audit areas A–E)

> [!WARNING]
> **Research notes only. Not an implementation basis. Do not merge before PR #16.**
> Issue #17 (provenance policy for CONFIDENTIAL / PROPERTY-OF-SEGA material) is **still undecided** as of 2026-10-08. In every "implementable from public material only" judgement below, CONFIDENTIAL-marked material (S-HW, S-BIOS, S-SDM, S-FMT, Tech Bulletins, Sega SDK files known only by reference) is **excluded**. The headline rate also excludes rows whose only basis derives from that material or from reverse engineering. It is recorded only as existing material with a usage problem, and as a lead for independent experiments. No Sega BIOS binary, dump or disassembly was obtained, read or used by any audit agent or by this integration.

Integration date: 2026-10-08 (revised the same day after an independent review; see §8). Base: `origin/agent-a/issue-1-rom-layout` @ `c2abc36` (PR #16). Inputs, merged from their branches (corrections made during integration review are listed in §8):

| Area | File | Prefix | Items |
| --- | --- | --- | --- |
| A ROM, CPU startup, memory map | [coverage/rom-cpu-memmap.md](coverage/rom-cpu-memmap.md) | `ROM-` | 87 |
| B Main/Sub comms, Word RAM, interrupts | [coverage/comm-wordram-irq.md](coverage/comm-wordram-irq.md) | `COM-` | 89 |
| C BIOS API, jump tables, calling conventions | [coverage/bios-api.md](coverage/bios-api.md) | `API-` | 88 |
| D CDC/CDD, disc format, boot sequence | [coverage/cd-boot.md](coverage/cd-boot.md) | `CD-` | 105 |
| E Source provenance and experiments | [coverage/provenance-experiments.md](coverage/provenance-experiments.md) | `PRV-` | 37 |

Levels: **LA** = minimal BIOS boot, **LB** = boot a homebrew CD program, **LC** = commercial-game-compatible BIOS. Evidence labels follow [README.md](README.md). Emulator behaviour is a model, not hardware truth. This integration did not re-run every citation. The independent review sampled 29 rows against the pinned clones; the over-claims it found are corrected in the area files (§8).

## 日本語要約

- **目的**: オリジナル BIOS を使わず、公開資料・独立資料だけで Mega-CD 互換 BIOS を実装できるかを判定する。5 領域 (A–E) の監査結果 406 項目を 1 つの表 (§7) に統合した。
- **前提**: Issue #17 (CONFIDENTIAL 資料の扱い) は**未決定**。CONFIDENTIAL / PROPERTY OF SEGA 表示のある資料は「公開資料のみ」の判定から**除外**した。
- **カバレッジ率** (§4、`tools/audit/coverage_rate.py` で算出。レベルは累積):
  - **見出し値**: **LA 71/93 = 76.3%、LB 139/228 = 61.0%、LC 193/406 = 47.5%**。次の 3 条件をすべて満たす項目を数えた。
    - 検証可能な仕様が定義済みである。
    - 根拠が除外資料・リバースエンジニアリング (RE) 由来・出所不明の資料だけではない。
    - 領域間の不一致グループ (X-nn) の全行が定義済みである。
  - 参考値 (副次ビュー):
    - 出典条件のみ: LA 80/93、LB 151/228、LC 209/406。
    - 不一致条件のみ: LA 71/93、LB 172/228、LC 257/406。
    - マニュアル/RE 由来も含む緩い値: LA 80/93 = 86.0%、LB 192/228 = 84.2%、LC 285/406 = 70.2%。
  - 領域 C (BIOS API) の見出し値は LB 2/38。LA は項目 0 件のため**算出不能**。
  - VDP/Z80 初期化、PCM、BIOS UI、機種バリアントは**どの領域でも列挙されておらず算出不能**。
  - 率は列挙の仕方に依存する値であり、ハードウェア検証済みの割合ではない。
- **最終判定** (§2):
  - **A) 最小 BIOS 起動: 条件付き可能**。エミュレータのモデルに対しては実装可能。実機では次の点が条件になる。
    - COM-86 (ゲートアレイ初期化の要否)
    - CDD の立ち上げとタイミング
    - 自前の実測値がないこと
  - **B) 自作 CD プログラム起動**: 条件付き可能なのは **B1 (自前 ABI のプログラム) のみ**。
    - **B2 (MegaDev 系 homebrew 互換) は現時点では困難**。調査した資料の範囲では、Sub BIOS API の知識として、除外マニュアル・RE・出所不明以外に由来するものは見つからなかった (X-04)。
    - B2 には Issue #17 / OQ-7 の決定か、クリーンルーム観測 (LEGAL-REVIEW 要) が必要。
  - **C) 市販ゲーム互換 BIOS: 現時点では困難**。調査した資料の範囲では、次の項目に非除外の仕様が見つからなかった。
    - セキュリティブロックの依存関係
    - Main `$280` ライブラリ (OQ-7)
    - BRAM 媒体フォーマット
    - CD ステータス構造
    - 通信フラグ規約
    - タイミング
- **開発停止級の欠落** (§1): 最優先は次の 5 点。
  - Issue #17 の決定
  - Sub BIOS API の出典
  - CDD プロトコルの独立検証
  - IP/SP 進入時の Word RAM 状態
  - セキュリティ/リージョン方針 (OQ-8)
- **領域間の不一致** 22 件 (X-01–X-22) は §3 に両論併記で記録し、率の計算にも反映した。どちらかに統合したり、ブロッカーを書き換えたりはしていない。
- **統合レビューでの修正**: §8 に一覧を載せ、該当する領域ファイルの行にも注記した。

## 1. Development-stopping gaps (prioritised)

A gap is **development-stopping** when at least one area marks it as a blocker: the Blocker column starts with Y, says "Y for" a stage, or inherits a blocker "via" another row. Gaps are ordered by the lowest level they stop, then by how many items depend on them. Blocker text is as written by the area files. Where areas disagree, both positions are kept (see §3).

| # | Gap | Stops | Items (blocker as marked by the area) | Disagreement | What could close it (legal, independent) |
| --- | --- | --- | --- | --- | --- |
| G-1 | **Issue #17 undecided.** Status of CONFIDENTIAL-marked manuals. PR #16 cannot merge; items whose only official cross-check is excluded stay ESTIMATED. | all levels (process) | PRV-01 (Y) | none | A maintainer decision. Not closable by experiment. |
| G-2 | **Sub-BIOS API provenance.** Entry points (`$5F0A-$5F3A`), function codes, register ABI. In the sources examined (MegaDev, clownmdemu HLE, the 0BSD boot ROM, the Mode-1 library, GX, PicoDrive), every listing traces to the excluded manual, to RE, or to an undeclared method. | LB (MegaDev-class homebrew), LC | CD-080 (Y, LB); PRV-02 (Y, LB); PRV-12 (Y, LB); CD-091 (Y, LC). Area C marks most of API-01…API-46 Cond and **not** blocking (its blockers there are API-23 and API-45, at LC only). | **X-04** | #17 / OQ-7 decision (option CR-C). Or the caller census E1(a) on public homebrew (no Sega code), plus in-situ observation E2 / EXP-04 (LEGAL-REVIEW: uses the console's own BIOS). A BIOS that defines its **own** ABI for its **own** SDK does not need this. |
| G-3 | **CDD command/status protocol independence.** Area E: one code lineage examined (PicoDrive's CDD is Genesis Plus GX code), no measurement. Area D: BlastEm `cdd_mcu.h` enum names agree with GX, but its independence from GX is unproven (header read via WebFetch only, no licence text). | LB (any disc read); LA on real hardware | PRV-15 (Y, LB); CD-030 / CD-039 ("Y for real-HW LA") | **X-09** | Mode-1 CDD logger probe (area D experiment 2, EXP-02): our own Sub code on our own CD-R. Reading BlastEm / ares source (licence check first) for a possible second lineage. |
| G-4 | **Word RAM mode and owner at IP/SP entry.** clownmdemu hands 2M to Sub; the 0BSD boot ROM sets 1M; the original's choice was not found in any non-excluded source examined. | LB / LC | COM-52 (Y, LB/LC); CD-117 (Y, LC); ROM-65 (N); API-72 (N) | **X-01** | For our own SDK, a documented choice. For compatibility, the E-5 / X-9 IP-entry recorder (LEGAL-REVIEW: runs under the original BIOS). |
| G-5 | **Security / region check policy** for our BIOS. | LB per area C; LC per areas A, D, E | API-71 (Y, LB policy); ROM-101 (Y); CD-130 (Y); PRV-05 (Y for LC) | **X-06** (CD-132 says our own discs boot without any check: Y) | OQ-8 legal decision. Negative tests EXP-05 on our own discs. |
| G-6 | **Gate-array "forced reset" / init necessity on real hardware.** The only statement found is in excluded S-HW. | LA on real hardware | COM-86 (Y); ROM-44 (Cond, N) | X-11 | X-2 init-necessity experiment (two builds, 1000 cold/warm boots; own code). |
| G-7 | **No hardware measurements of our own.** Every hardware-scope claim rests on emulators, SDKs or second-hand "verified on real hardware" comments. Also covers TMSS on TMSS units, and Mode-2-only behaviour. | LA hardware claims, release | PRV-22 (Y for release); PRV-27 (Y for TMSS hardware boot); PRV-25 (Y for a Mode-2 hardware claim); PRV-14 / PRV-16 (Y for hardware claims); CD-030 / CD-039 (Y for real-HW LA) | X-15 (ROM-31 marks TMSS N) | E-1 / X-1 / EXP-01 Mode-1 probe; EXP-10 timing. Mode-2 boot-ROM placement needs an FPGA host (unverified) or chip replacement (out of scope: hardware modification). |
| G-8 | **Retail security block** that every commercial IP runs first, and what it expects from the boot ROM. | LC | CD-131 (Y); PRV-07 (Y); PRV-05 (Y) | X-06 | Only by clean-room observation (EXP-09, area D experiment 6). LEGAL-REVIEW before anyone runs it. |
| G-9 | **Main `$280` library, BIOS work area** (`$FFFDB4+`) **and the Main-side comm-flag / Sub-proxy protocol.** Not found in the sources examined (MegaDev, the 0BSD boot ROM, clownmdemu, GX, PicoDrive, the megadrive.org TOC) except as RE-derived material (MegaDev) or material of undeclared origin (0BSD boot ROM). The protocol part is "not well understood" even in the RE source. | LC | ROM-11, ROM-71, COM-35, COM-82, API-82…API-94, API-92, PRV-03 (all Y) | X-08 | OQ-7 clean-room protocol (CR-A / CR-D) plus E4 black-box `$280` calls (needs OQ-7 approval first). |
| G-10 | **BRAM on-media format** compatible with existing saves and RAM carts. | LC (interoperability) | ROM-90 (Y); API-60 (Y); API-56 (`BRMFORMAT`, Blocker "via API-60": inherited); PRV-13 ("Y only for save interoperability") | **X-07** (PRV-13 marks it Cond; ROM-90 / API-60 mark it N) | E-4 / E3 / EXP-08: format and save with own homebrew, then read the raw data back. Data, not code; LEGAL-REVIEW (light). |
| G-11 | **CD status block and CD service semantics** (`CDBSTAT` fields, CD-DA services, `_CDBOOT`, contested function codes). | LC (LB only if homebrew polls `$5E80`) | API-23 (Y, LC); CD-081 (Y); CD-083 (Y); CD-089 (Y); CD-091 (Y) | **X-05**, X-17, X-18 | E2 / E5 probes; E1 census for which codes are actually called. |
| G-12 | **Sub user-call contract** (registers, SR, return codes, cadence). | LC | COM-32 (Y, LC); COM-33 (Y, LC) | X-12 | E2 register-diff probe; E-5 SR recorder (LEGAL-REVIEW). |
| G-13 | **CPU / comm state at IP and SP entry** that games rely on. | LC | CD-117 (Y); COM-36 (Y) | X-02 | E-5 / X-9 (LEGAL-REVIEW). |
| G-14 | **Drive and seek timing** that games sync against. | LC | API-45 (Y); CD-107 (Y); CD-037 ("Y for LC") | X-19 | E5 / area D experiment 4 / EXP-10 on our own CD-R. Own code only. |
| G-15 | **Masked Sub-interrupt latch semantics.** Emulators conflict. | LC | COM-66 (Y) | none | X-3 latch matrix (own code). |
| G-16 | **Mode-1 Sub-BIOS discoverability** (compressed Sub BIOS location and signature). | LC (Mode 1 subset) | ROM-10 (Y); COM-58 (Y) | **X-13** (API-76: N, "design constraint"; offsets differ) | E-3 / X-10: public Mode-1 homebrew in emulators with our ROM. |
| G-17 | **CDD drive reaction to a bad command checksum**, and whether the BIOS must verify the status checksum. | LC robustness | CD-033 ("N (LA) / Y for LC robustness") | none | Area D experiment 2: the probe sends a deliberately bad checksum (harmless). |
| G-18 | **Legal basis for observation and for reading disassembly.** | LC | PRV-26 (Y); PRV-34 (Y for CR-A) | none | Not closable by experiment: LEGAL-REVIEW. |
| G-19 | **Release-only reviews**: patent / trademark / naming; per-model variants. | release; broad LC claims | PRV-35 (Y for release); PRV-29 (Y for broad LC claims) | none | Legal review; EXP-07 public PCB evidence. |
| G-20 | Boot-header IP layout parity; reference comparison of test discs; Main `$FFFD00` full slot map. | LC parity | CD-022 ("Y for LC parity"); PRV-09 ("Y for the reference comparison"); PRV-04 ("Y for full LC") | X-16, X-03 | E6 slot mapping; EXP-05. |

The remaining (non-stopping) gaps are in §5.

## 2. Final judgement

Each verdict lists the blockers it depends on. "Not found" always means **not found in the sources examined** (§6), never "does not exist". All rates quoted here are the §4 headline (defined, provenance-clean and undisputed) unless labelled otherwise.

### A) Is the spec sufficient for a minimal BIOS boot? **条件付き可能 (conditional)**

- Cumulative LA headline: 71/93 = 76.3% (lenient view: 80/93 = 86.0%).
  - CPU behaviour has a vendor source (M68000 UM).
  - Gate-array, PRG-RAM and Sub-reset behaviour, and CDD/CDC bring-up, are defined by emulator and SDK sources.
- **Emulator target: feasible against the emulator models.**
  - Prior art: an independently written 0BSD minimal boot ROM (`clownmdemu-mcd-boot`) runs in clownmdemu (area A §3). Its knowledge provenance is undeclared, so it may be studied for facts but not copied.
  - The LA rows outside the headline are:
    - the CDD frame rows CD-031, CD-034 and CD-035, disputed through X-09 (they agree with GX, but independence is unproven, and PRV-15 rates the protocol N);
    - ROM-41, ROM-44 and ROM-63, disputed through X-21, X-11 and X-20;
    - ROM-05, ROM-09, ROM-31, ROM-43, COM-14 and CD-030, which have a recorded conflict or UNCONFIRMED hardware behaviour;
    - COM-86, which is a Cond blocker.
  - None of these stops an emulator build that targets GX's behaviour. Each of them stops a hardware claim.
- **Real hardware: conditional** on:
  - G-6 (COM-86, init necessity);
  - G-3 (CDD bring-up and INT4 timing, CD-030 / CD-039);
  - G-7 (no measurements; TMSS, PRV-27).
- **Process:** G-1 (Issue #17) blocks merging PR #16. The LA headline does not depend on excluded material: the provenance-clean view keeps all 80 lenient LA items, and the drop to 71 comes only from disputes.
- **How far legal independent experiments close it:** almost entirely.
  - These use only our own code on a flash cart and our own CD-R: E-1 / X-1 / EXP-01 (Mode-1 probe), X-2 (init necessity), area D experiment 2 (CDD logger) and EXP-10.
  - What remains is Mode-2-only behaviour (boot ROM at `$000000`). It needs an FPGA host (not verified), because ROM replacement is out of scope (PRV-25).

### B) Is the spec sufficient to boot our own CD program? **条件付き可能 (conditional) only for B1 (own-ABI program); B2 (MegaDev-class homebrew) 現時点では困難**

Area C defines LB as "MegaDev-class" homebrew (`coverage/bios-api.md` §1). The verdict is therefore split, and the conditional verdict applies **only to B1**.

- Cumulative LB headline: 139/228 = 61.0%.
  - Lenient view: 192/228 = 84.2%.
  - Provenance-clean only: 151/228 = 66.2%.
  - Area C's headline LB is 2/38.
- **B1, a program written for our own BIOS ABI** (our SDK, our boot header handling, our Word RAM hand-off): **条件付き可能**, in emulators.
  - Defined: the disc format and boot header (CD-001…CD-011; API-70; PRV-10, now Cond).
  - Our own design: IP/SP loading (CD-115, CD-132).
  - Condition G-3: the CDD protocol is an emulator model only, its independence is unproven, and there is no measurement. PRV-15 marks disc reading N with Blocker Y at LB.
  - Condition G-5: a written OQ-8 policy that our BIOS performs no security check.
- **B2, MegaDev-class homebrew compatibility (area C's LB definition): 現時点では困難 (currently difficult)**, pending Issue #17 / OQ-7 or a clean-room observation route.
  - It depends on G-2 (X-04). Areas D and E mark the Sub API as an LB blocker; area C marks the same items Cond and non-blocking. Both positions are kept, and the rate counts these items as disputed.
  - In the sources examined, no listing of the Sub-BIOS API was found whose origin is something other than the excluded manual, RE, or an undeclared method.
  - It also depends on G-4 (COM-52, Word RAM at entry), and on G-11 if homebrew polls `$5E80`.
- **How far legal independent experiments close it:**
  - B1: almost completely, through the EXP-02 / EXP-03 Mode-1 harnesses and the synthetic disc suite.
  - B2: partly. The caller census E1(a) on public homebrew yields interface facts with no Sega code involved. The semantics and exact ABI need either E2 / EXP-04, which use the console's own BIOS (LEGAL-REVIEW), or a #17 / OQ-7 decision.

### C) Is the spec sufficient for a commercial-game-compatible BIOS? **現時点では困難 (currently difficult)**

- Cumulative LC headline: 193/406 = 47.5% (lenient view: 285/406 = 70.2%). Even the headline overstates readiness, because the undefined items are the ones every retail disc touches.
- It depends on:
  - G-8 (security block, CD-131 / PRV-07);
  - G-9 (`$280` library, OQ-7);
  - G-10 (BRAM format);
  - G-11 (CD status and services);
  - G-12 (user-call contract);
  - G-13 (entry state);
  - G-14 (timing);
  - G-15, G-16, G-17 and G-18;
  - all of A and B2.
- Not found in the sources examined:
  - the on-media BRAM directory, allocation and protect format (ROM-90, API-60);
  - the Main-side comm-flag / Sub-proxy protocol (API-92, COM-35), which is "not well understood" even in the RE source;
  - the full `CDBSTAT` field layout (API-23, CD-081);
  - the comm state at IP/SP entry (COM-36);
  - the boot-time budget (CD-121);
  - the disc-change and lid-open status sequences (CD-051, CD-054, CD-143).
- **How far legal independent experiments close it:** partly.
  - Own code and own media can close timing (E5, EXP-10), latch semantics (X-3), the CDD checksum reaction (area D experiment 2) and Mode-1 discoverability (E-3, X-10).
  - With light LEGAL-REVIEW, the BRAM format can be closed too (E-4, E3, EXP-08). These experiments read data written by the original BIOS, not code.
  - The security-block dependencies, the `$280` library, the user-call contract and the entry state need observation of the original BIOS or of retail discs (EXP-09, X-9, E4, CR-A / CR-D).
    - These require a maintainer decision and LEGAL-REVIEW before any work starts (PRV-26, PRV-34, OQ-7, OQ-8).
    - They also need a two-team process that is hard to sustain in a volunteer project (area E §6).

### Sensitivity note (not the verdict): if the maintainer permits paraphrased citation of CONFIDENTIAL-marked manuals

This is a separate what-if. **No audit agent read the excluded pages for this audit.** What they cover is inferred only from the table-of-contents titles that the area files record as leads (megadrive.org TOC), so it may be wrong.

- **A:** class unchanged (条件付き可能). S-HW §4-1 p.56 appears to describe the forced-reset pattern (COM-86) and the power-on register values. That would settle G-6 on paper, but hardware measurement (G-7) is still owed before any release claim.
- **B1:** unchanged (条件付き可能).
- **B2:** would likely become **実装可能** in emulator scope.
  - S-BIOS appears to cover G-2 / X-04, the Sub stack and system area (ROM-45…ROM-47), and the user-call contract (COM-32 / COM-33). The relevant pages are the call list (pp.7–8), the reference (pp.11–29), bootstrap (pp.30–32), and the jump table and user calls (pp.33–35).
  - S-HW §3-6 pp.31–33 appears to cover the CDD protocol (G-3, on paper only).
  - S-FMT System ID pp.18–19 appears to cover CD-020 / PRV-11.
  - In rate terms, the 76 rows demoted by provenance (§4) would return to the provenance-clean view. Disputes still apply until the disagreeing rows are re-rated.
- **C:** stays **現時点では困難**.
  - For the Main `$280` library, only RE-derived material was found in the sources examined. Its official documents (`ROM_UTIL.DOC`, `MAINENT.I`) were not found.
  - The security-block dependencies, retail timing, the region legal questions (OQ-8) and the observation basis (PRV-26 / PRV-34) are not addressed by the manuals as far as their TOCs show.
  - S-BIOS "Back-up RAM" pp.38–45 may or may not include the on-media format (G-10): unknown.

## 3. Cross-area overlaps and disagreements

The same behaviour sometimes appears in several area files. Every row is kept as written by its area. Rows in a group carry the tag `[X-nn]` in the ID cell of the matrix (§7). The column that disagrees is named; nothing was merged or reworded. **This table is data:** `tools/audit/coverage_rate.py` reads the Items column to build the tags and to apply rule 6 of §4 (a row is undisputed only if every row of each of its groups is defined).

| Tag | Topic | Items | What disagrees |
| --- | --- | --- | --- |
| X-01 | Word RAM mode/owner at IP/SP entry | ROM-65, COM-52, COM-63, API-72, CD-117 | **Level**: ROM-65 LC; COM-52 / API-72 LB; CD-117 LB/LC. **Blocker**: COM-52 Y (LB/LC), CD-117 Y (LC), ROM-65 / API-72 / COM-63 N. **Facts**: clownmdemu gives 2M to Sub; the 0BSD boot ROM's Sub init sets 1M (API-72 calls it an apparent disagreement that may reflect different phases). |
| X-02 | Main CPU state at IP entry | ROM-68, ROM-70, COM-81, API-73, CD-117 | **Implementable**: Cond (ROM-68, ROM-70, COM-81, API-73) vs **N** (CD-117). **Blocker**: CD-117 Y (LC); others N. **Facts**: SSP `$FFFD00` vs `$FFFC00` (OQ-2). |
| X-03 | Main `$FFFD00` jump table | ROM-26, ROM-27, COM-79, API-80, API-81, PRV-04 | Mostly agree. **Address convention**: ROM-26 / COM-79 give JMP-entry addresses, MegaDev and API-80 / PRV-04 give operand addresses (entry + 2), e.g. shared slot `$FFFD7E` (ROM-27) = `$FFFD80` (PRV-04). **Blocker**: PRV-04 "Y for full LC"; others N. ROM-27 says the duplicate slot is corroborated by a second source (updates OQ-12). |
| X-04 | Sub-BIOS API provenance | API-06, API-10, API-32, API-37, CD-080, PRV-02, PRV-12 | **Blocker at LB**: CD-080, PRV-02, PRV-12 Y; area C marks the API items Cond and N (its only LB blocker is API-71). **Implementable**: all Cond. Same underlying sources (MegaDev, clownmdemu). |
| X-05 | `CDBSTAT` / status block at `$5E80` | API-16, API-23, CD-081 | **Implementable**: API-23 Cond for LB and N for LC; CD-081 **N**. **Blocker**: API-23 Y (LC); CD-081 Y (LC; LB if homebrew polls it). |
| X-06 | Security block and region check | ROM-101, API-71, CD-130, CD-131, CD-132, CD-133, PRV-05, PRV-06, PRV-07 | **Level**: API-71 is LB with Blocker Y (policy, OQ-8); CD-132 (LB) says our own discs boot without Sega code: Y, not a blocker; ROM-101 / CD-130 / PRV-05 put the check at LC. |
| X-07 | BRAM on-media format | ROM-90, API-60, PRV-13 | **Implementable**: ROM-90 / API-60 **N**; PRV-13 **Cond**. **Blocker**: ROM-90 / API-60 Y; PRV-13 N, "Y only for save interoperability". |
| X-08 | Main `$280` library, work area, comm-flag protocol | ROM-11, ROM-71, COM-35, COM-82, API-82, API-83, API-92, API-94, PRV-03 | Agree on blocker (Y, OQ-7). **Names**: MegaDev and the 0BSD boot ROM name the `$280` system entries differently (API-83). API-88 / API-90 are Cond (formats or own font), the rest N. |
| X-09 | CDD protocol: second independent lineage? | CD-031, CD-034, CD-035, PRV-15, PRV-19 | **Implementable / blocker**: area D rates the CDD frame Cond, LA, not blocking, because GX and BlastEm agree (its wording "two independent lineages" was corrected during integration review to "agree; independence from GX unproven"); PRV-15 says only one lineage was examined (GX ≈ PicoDrive), **N**, Blocker Y (LB). BlastEm was read only as `cdd_mcu.h` enum names through WebFetch, with no licence or copyright text in the file. |
| X-10 | CDC datasheet | CD-060, PRV-16 | **Existence**: area D located an LC8950/LC8951 design-manual scan (LCDM, provenance unverified; a Sega-marked copy is excluded); PRV-16 says the chip datasheet was not found in the sources it examined. Both Cond. |
| X-11 | Gate-array init / forced reset | ROM-44, COM-86 | **Blocker**: COM-86 Y (LA on real hardware); ROM-44 N (Cond: "which steps are mandatory"). |
| X-12 | Sub user-call contract | ROM-49, COM-32, COM-33, API-07, API-14, CD-116 | **Blocker**: COM-32 / COM-33 Y (LC); the others N. **Level**: ROM-49 LC; the others LB. |
| X-13 | Mode-1 compressed Sub BIOS | ROM-10, COM-58, API-76, API-77, CD-120 | **Facts**: ROM-10 gives one location (`$16000`) and COM-58 only the signature; API-76 lists `$15800`, `$16000`, `$1AD00` from a Mode-1 library survey. **Blocker**: ROM-10 / COM-58 Y; API-76 N ("design constraint"). **Implementable**: CD-120 N ("how a cartridge obtains the CD BIOS"), while API-77 is Y (caller contract public in a 0BSD Mode-1 library). |
| X-14 | Sub stack | ROM-47, API-15 | ROM-47 records a conflict (`$5D80-$5E80` vs excluded `$5C00`); API-15 Cond without the conflict. |
| X-15 | TMSS | ROM-31, PRV-27 | **Blocker**: ROM-31 N; PRV-27 "Y for a hardware boot on TMSS units until resolved". |
| X-16 | Boot header IP/SP fields | CD-022, CD-023, API-70, PRV-10 | **Implementable**: API-70 / PRV-10 Y; CD-022 / CD-023 Cond. **Units**: CD-022 uses byte offsets `$30/$34/$40/$44`, API-70 word offsets `$18/$1A/$20/$22` (same fields). |
| X-17 | Contested CD function codes (OQ-12) | API-30, API-34, CD-091 | **Blocker**: CD-091 Y (LC); API-34 N unless E1 finds callers. API-30 says clownmdemu's HLE resolves `$11-$13` (Cond); CD-091 says the authoritative list is only in excluded S-BIOS (N). |
| X-18 | `_CDBOOT` services | API-05, API-65, API-66, CD-089 | **Implementable**: API-65 Cond; API-66 / CD-089 N. **Blocker**: CD-089 Y; API-05 / API-65 / API-66 N. |
| X-19 | Drive / seek timing | API-45, CD-037, CD-107 | **Level**: CD-037 LB (N for LB, Y for LC); API-45 / CD-107 LC, Y. Agree it is unmeasured. |
| X-20 | PRG-RAM write-protect scope | ROM-43, ROM-63, COM-09 | **Facts**: ROM-43 says emulators disagree on whether WP blocks Main writes; clownmdemu `source/bus-main-m68k.c:972` blocks Main writes below WP×512. COM-09 is Y for Sub writes; its "emulators: no" for Main writes was corrected during integration review (GX and PicoDrive: no; clownmdemu: yes). |
| X-21 | SRES=0 forces SBRQ=1 | ROM-41, COM-05 | **Level**: ROM-41 LA (part of the handshake, Cond); COM-05 LC, emulators disagree. ROM-41 cited PicoDrive `memory.c:187` as support, but the rule is commented out there (corrected during integration review). |
| X-22 | Gate-array power-on state | ROM-40, COM-04 | **Implementable**: ROM-40 Cond; COM-04 Y. Same sources. |

Source-level disagreements (no item row):

- **S-1, replacement boot ROM source.** Areas A and B cite `Clownacy/clownmdemu-mcd-boot@ebdf03c` (2025-09-07); area C cites `kirisamemofo/clownmdemu-mcd-boot@6025457` (2026-01-27) for the same project, so line numbers may differ. Area D and area E (L-16) record the clownmdemu boot-ROM blob as having no source in the examined repository; areas A–C found the source repository. The provenance of its interface knowledge is undeclared in all accounts.
- **S-2, Genesis Plus GX revision.** Areas A, B, C and D cite the fork `87dd8b8` (the PR #15 harness pin). PR #16 and **area E** cite upstream `49c5847`: area E's `gpgx/…` line numbers match upstream, not the fork (e.g. PRV-10's `cdd.c:1181` is `:1168` in the fork). Area E now states this (corrected during integration review). Line numbers in `scd.c`, `mem68k.c`, `cdc.c`, `cdd.c` differ between the trees (OQ-20).
- **S-3, independence of "emulators agree".** Areas A and B count GX + PicoDrive agreement as support for many items; PRV-19 shows PicoDrive's CDD, CDC and graphics code is GX code. For those subsystems the agreement is not two independent confirmations.

## 4. Coverage rate

### Definition

**Coverage rate = (items for which a verifiable spec is defined from non-excluded sources) / (items enumerated).**

- Levels are cumulative: LA uses LA items, LB uses LA + LB items, LC uses all items.
- A row tagged "LB/LC" counts at LB.
- Each row of §7 is one item, so a behaviour that several areas enumerate (§3) counts once per area.

The **headline** counts an item only when all six rules hold. `tools/audit/coverage_rate.py` applies them mechanically:

1. The "Implementable from public material only?" cell starts with **Y** or **Cond**.
2. None of the cells "Existing material", "Exact reference", "Provenance" or "Implementable" records an unresolved conflict (`UNCONFIRMED`, `conflict`, `disagree`, `contradict`).
3. If the item is **Cond**, or its existing material is not plainly **Y** (partial or N), then "Coverable by own test?" must start with **Y**. This is how the area file shows that acceptance is verifiable.
4. A **Cond** item that is blocking is not counted. Blocking means the Blocker cell starts with **Y**, or the item inherits a blocker ("via API-60").
5. **Provenance-clean.** The provenance cell does not show that the row's basis derives from the excluded manuals, from RE, or from an undeclared-origin source.
   - "as above" / "as <ID>" references are expanded before the check.
   - Keywords that fail the check: `P-OFF`, `P-RE`, `P-UNK`, `RE`, "RE-derived", "reverse engineer", "disassembly", "official BIOS manual", "derived from L-0…", "derive from XS", "second-hand from XS", "quotes official".
   - The Implementable cell must also not say that the item rests on excluded material ("only via an excluded", "rests on an excluded", "origin is the excluded", "attributes them to the excluded").
   - Every keyword hit was checked by hand:
     - **Newly matched by the patterns added during integration review, and confirmed as derived:**
       - ROM-67: MegaDev quotes official text.
       - ROM-69: inherits ROM-67's provenance through "as above". Its other basis is a clownmdemu comment saying "what Sega's BIOS does", which PRV-32 treats as a lead only.
       - API-75 and API-95: P-UNK.
       - CD-003: the 2 s pregap rule is second-hand from excluded S-FMT.
       - CD-023: the placement is confirmed only through an excluded document.
     - **Checked and judged not derived:** COM-56, COM-65, COM-75, COM-78, CD-022, CD-073, PRV-14 and PRV-16. In these rows "official" or "excluded" refers to the M68000 vendor manual, or to the official manual not being used; the basis is emulator source. The narrowed patterns do not match them.
     - **Overridden:** keyword hits whose hand-check found an independent non-excluded basis. The script reads this table:

   | Override | Item | Independent basis (why the keyword hit is not the only basis) |
   | --- | --- | --- |
   | H-01 | ROM-28 | "as above" chains to ROM-26's MegaDev note, but the row cites GX, PicoDrive and clownmdemu source, which agree |
   | H-02 | ROM-30 | "as above" chain; the basis is M68000 UM §6.3.1 (vendor manual) |
   | H-03 | COM-83 | "as above" chain; the clock and timer base come from GX `scd.h` and PicoDrive `mcd.c` |
   | H-04 | CD-008 | MegaDev (RE caveat) gives disc-type codes, but the requirement is our own "do not hang" rule, classified from the TOC data flag (GX) |
   | H-05 | PRV-32 | A process rule (treat emulator claims about Sega's BIOS as leads); it needs no source fact |

6. **Undisputed.** If the item belongs to cross-area groups (§3), every row of each of those groups satisfies rules 1–4. This is the reviewer's conservative reading: a row is not counted while another area rates the same behaviour N or blocking.

The **secondary views** relax rule 5, rule 6, or both, and are kept for comparison only. The lenient view (rules 1–4 only) means "defined by any cited source, including manual/RE-derived". It must not be quoted as the coverage rate.

Limits that apply to every view:

- No view counts hardware-verified behaviour, because there are no measurements in this project (PRV-22).
- The provenance check is keyword-based plus the hand-check above. A row can still be counted when its origin is unstated in a way the patterns cannot see, for example an emulator source whose own origin is unknown (PRV-32 treats such sources as leads).

### Computed rates

Generated by `python tools/audit/coverage_rate.py --write`; do not edit by hand.

<!-- BEGIN GENERATED: rates -->
**Headline: defined, provenance-clean and undisputed**

| Scope | LA (LA items) | LB (LA+LB items) | LC (all items) |
| --- | --- | --- | --- |
| All areas | 71/93 = 76.3% | 139/228 = 61.0% | 193/406 = 47.5% |
| A rom-cpu-memmap | 31/38 = 81.6% | 45/59 = 76.3% | 54/87 = 62.1% |
| B comm-wordram-irq | 19/23 = 82.6% | 38/51 = 74.5% | 60/89 = 67.4% |
| C bios-api | 0/0: not computable | 2/38 = 5.3% | 2/88 = 2.3% |
| D cd-boot | 14/19 = 73.7% | 39/55 = 70.9% | 60/105 = 57.1% |
| E provenance-experiments | 7/13 = 53.8% | 15/25 = 60.0% | 17/37 = 45.9% |

**Secondary: defined and provenance-clean (cross-area disputes ignored)**

| Scope | LA (LA items) | LB (LA+LB items) | LC (all items) |
| --- | --- | --- | --- |
| All areas | 80/93 = 86.0% | 151/228 = 66.2% | 209/406 = 51.5% |
| A rom-cpu-memmap | 34/38 = 89.5% | 48/59 = 81.4% | 58/87 = 66.7% |
| B comm-wordram-irq | 20/23 = 87.0% | 40/51 = 78.4% | 62/89 = 69.7% |
| C bios-api | 0/0: not computable | 2/38 = 5.3% | 3/88 = 3.4% |
| D cd-boot | 17/19 = 89.5% | 44/55 = 80.0% | 66/105 = 62.9% |
| E provenance-experiments | 9/13 = 69.2% | 17/25 = 68.0% | 20/37 = 54.1% |

**Secondary: defined and undisputed (manual/RE-derived sources allowed)**

| Scope | LA (LA items) | LB (LA+LB items) | LC (all items) |
| --- | --- | --- | --- |
| All areas | 71/93 = 76.3% | 172/228 = 75.4% | 257/406 = 63.3% |
| A rom-cpu-memmap | 31/38 = 81.6% | 50/59 = 84.7% | 61/87 = 70.1% |
| B comm-wordram-irq | 19/23 = 82.6% | 41/51 = 80.4% | 63/89 = 70.8% |
| C bios-api | 0/0: not computable | 23/38 = 60.5% | 44/88 = 50.0% |
| D cd-boot | 14/19 = 73.7% | 42/55 = 76.4% | 71/105 = 67.6% |
| E provenance-experiments | 7/13 = 53.8% | 16/25 = 64.0% | 18/37 = 48.6% |

**Secondary: defined by any cited source, including manual/RE-derived (lenient)**

| Scope | LA (LA items) | LB (LA+LB items) | LC (all items) |
| --- | --- | --- | --- |
| All areas | 80/93 = 86.0% | 192/228 = 84.2% | 285/406 = 70.2% |
| A rom-cpu-memmap | 34/38 = 89.5% | 53/59 = 89.8% | 65/87 = 74.7% |
| B comm-wordram-irq | 20/23 = 87.0% | 43/51 = 84.3% | 65/89 = 73.0% |
| C bios-api | 0/0: not computable | 31/38 = 81.6% | 56/88 = 63.6% |
| D cd-boot | 17/19 = 89.5% | 47/55 = 85.5% | 77/105 = 73.3% |
| E provenance-experiments | 9/13 = 69.2% | 18/25 = 72.0% | 22/37 = 59.5% |

**Secondary: headline items whose Implementable cell is Y**

| Scope | LA (LA items) | LB (LA+LB items) | LC (all items) |
| --- | --- | --- | --- |
| All areas | 49/93 = 52.7% | 83/228 = 36.4% | 102/406 = 25.1% |
| A rom-cpu-memmap | 21/38 = 55.3% | 24/59 = 40.7% | 27/87 = 31.0% |
| B comm-wordram-irq | 18/23 = 78.3% | 36/51 = 70.6% | 46/89 = 51.7% |
| C bios-api | 0/0: not computable | 2/38 = 5.3% | 2/88 = 2.3% |
| D cd-boot | 5/19 = 26.3% | 12/55 = 21.8% | 17/105 = 16.2% |
| E provenance-experiments | 5/13 = 38.5% | 9/25 = 36.0% | 10/37 = 27.0% |

Items enumerated by minimum level: LA 93, LB 135, LC 178, total 406.

Demoted by provenance (defined, but manual/RE/undeclared-origin) (76): ROM-26, ROM-27, ROM-45, ROM-46, ROM-67, ROM-69, ROM-94, COM-31, COM-76, COM-79, API-01, API-02, API-03, API-04, API-05, API-06, API-07, API-08, API-09, API-10, API-12, API-14, API-15, API-16, API-17, API-20, API-21, API-22, API-24, API-25, API-27, API-28, API-29, API-31, API-32, API-33, API-35, API-36, API-37, API-38, API-39, API-42, API-43, API-44, API-46, API-50, API-51, API-52, API-53, API-54, API-55, API-57, API-58, API-61, API-62, API-65, API-74, API-75, API-76, API-80, API-81, API-95, API-96, CD-003, CD-021, CD-023, CD-028, CD-029, CD-055, CD-082, CD-084, CD-085, CD-086, CD-087, PRV-04, PRV-13.

Demoted by cross-area dispute (defined, but another row of its X-group is not) (28): ROM-41, ROM-44, ROM-63, ROM-70, COM-09, COM-63, API-05, API-06, API-07, API-10, API-14, API-15, API-16, API-32, API-37, API-65, API-76, API-77, CD-031, CD-034, CD-035, CD-116, CD-132, CD-133, PRV-06, PRV-13, PRV-19, PRV-27.

Marked Y or Cond by the area file but not defined by rules 1-4 (49): ROM-03, ROM-05, ROM-09, ROM-10, ROM-29, ROM-31, ROM-38, ROM-43, ROM-47, ROM-49, ROM-65, ROM-68, ROM-86, ROM-102, COM-05, COM-13, COM-14, COM-17, COM-32, COM-33, COM-41, COM-47, COM-52, COM-58, COM-60, COM-80, COM-81, COM-86, API-13, API-23, API-26, API-30, API-40, API-56, API-71, API-72, API-73, API-88, API-90, API-98, CD-030, CD-065, CD-080, CD-083, CD-140, PRV-02, PRV-05, PRV-12, PRV-21.
<!-- END GENERATED: rates -->

### Comparison with the area files' own counts

Each area used a slightly different rule. Its self-reported "spec defined" numbers (non-cumulative, by minimum level) therefore differ from the uniform rule above:

| Area | Self-reported LA / LB / LC (defined / enumerated) | Area rule |
| --- | --- | --- |
| A | 36/38, 18/21, 16/28 | Y or Cond, material not N, no unresolved conflict |
| B | 23/23, 28/28, 28/38 | Y or Cond |
| C | 0/0, 37/38, 31/50 | material not N, Y or Cond |
| D | 18/19, 33/36, 31/50 | Y or Cond |
| E | 7/13, 6/12, 2/12 | judgement; emulator-scoped claims count only for emulator-scoped or process items |

None of the area rules considers provenance taint or cross-area disputes, so the uniform headline is lower than every area's self-reported figure.

### Enumeration caveats (read before quoting any rate)

- **Area C, LA: not computable.** Area C enumerated no LA items. It argues that a minimal boot exposes no API surface.
- **Not enumerated in any area, so not computable:**
  - VDP / Z80 / PSG / controller initialisation beyond ROM-36. Area A deferred this to a "VDP/IO area" that was not assigned.
  - PCM (RF5C164) initialisation and behaviour. Only ROM-44, ROM-85, CD-072 and PRV-33 touch it.
  - The BIOS's own user interface (CD player, BRAM manager, control panel). Only API-96 and CD-119 touch it.
  - Generic Mega Drive behaviour such as the TMSS details and the `$A10001` version register. ROM-31, ROM-34 and ROM-35 rely on emulator/SDK statements.
  - The Mega-CD + 32X, LaserActive, Wondermega, X'Eye and CDX variants, which several areas list as not investigated.
- **Granularity differs.** Area C groups several function codes per row, while area D splits drive behaviour finely. Every row has equal weight, so the "All areas" figures are artifacts of how each area enumerated. The denominators are a lower bound of the true number of required behaviours, and the rates are **not** a measure of total coverage.
- **Overlaps count more than once** (§3). For example, CD-117, COM-52, ROM-65 and API-72 describe related entry-state questions.
- **X-group membership may be incomplete.** The independent review could not confirm that every overlap is tagged. Rule 6 does not cover untagged overlaps.
- A high rate does not mean the remaining items are minor. In LC the undefined items are concentrated where every retail disc depends on them (§2 C).

## 5. Other gaps (not development-stopping)

These items are rated **N** in the Implementable cell, but no area marks them as a blocker:

- LA: CD-040; PRV-35 (blocker only "for release").
- LB: API-11; CD-037 (blocker only "for LC").
- LC: ROM-37, ROM-61, ROM-83, ROM-103, COM-19, COM-28, COM-29, COM-42, COM-77, COM-85, API-34, API-41, API-59, API-63, API-66, API-99, CD-024, CD-027, CD-042, CD-043, CD-051, CD-054, CD-074, CD-077, CD-088, CD-106, CD-120, CD-121, CD-141, CD-143, PRV-29, PRV-30, PRV-36.

Two blocking items are rated Cond and therefore appear in §1:

- CD-033: Blocker "Y for LC robustness" (G-17).
- API-56: Blocker "via API-60", inherited (G-10).

Notable among the non-stopping gaps:

- **CD-040 (LA)**: whether software must pace HOCK/CDCK nibble accesses. Every emulator uses a pure register model, and nothing on this was found in the sources examined. Area D experiment 2 could close it.
- **API-11 (LB)**: which BIOS calls are legal from interrupt / USERCALL2 context. Not found in the sources examined. It does not block homebrew that calls from USERCALL1, but it is a robustness risk for LC.
- The generated rate block (§4) lists every item demoted by provenance or by dispute, and every Y/Cond item that rules 1–4 do not count.

## 6. Sources examined (union of the area files) and access status

| Source | Pin / status | Licence or terms | Used by |
| --- | --- | --- | --- |
| Motorola M68000 UM, <https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf> | SHA-256 `89b690b1…a18e1`; HTTP 200 with curl's default UA, 404 with a browser UA | Proprietary, cite only | A, B, E |
| Genesis Plus GX fork, <https://github.com/mao2009/Genesis-Plus-GX> | `87dd8b8` | Non-commercial, cite only | A, B, C, D |
| Genesis Plus GX upstream, <https://github.com/ekeeke/Genesis-Plus-GX> | `49c5847` | Non-commercial, cite only | E (its `gpgx/…` line numbers; S-2) and PR #16 |
| PicoDrive, <https://github.com/notaz/picodrive> | `26ecb2b` | Non-commercial (MAME-style), cite only; CDD/CDC/gfx are GX code | A–E |
| clownmdemu-core fork, <https://github.com/mao2009/clownmdemu-core> | `15c6cba` | AGPL-3.0, cite only | A–E |
| clownmdemu-mcd-boot, <https://github.com/Clownacy/clownmdemu-mcd-boot> / <https://github.com/kirisamemofo/clownmdemu-mcd-boot> | `ebdf03c` / `6025457` (S-1) | 0BSD; knowledge provenance undeclared | A, B, C |
| Mode-1 library, <https://github.com/kirisamemofo/mega-cd> | `74aa087` | 0BSD | C |
| MegaDev, <https://github.com/drojaazu/megadev> | `7a7246c` | MIT; partly RE; Sub side attributed to the official manual; `lib/security.c` excluded (Sega code) | A–E |
| BlastEm `cdd_mcu.h`, <https://www.retrodev.com/repos/blastem/file/07ed42bd7b4c/cdd_mcu.h> | hg `07ed42bd7b4c`, WebFetch only; agrees with GX, independence unproven | GPL-3.0 per `COPYING` (area E); no licence text in the file (area D, review) | D, E |
| ECMA-130, ECMA-119 | 2nd ed. 1996; ECMA-119 not pinned | Free public standards | D |
| LC8950/LC8951 design manual scan (bitsavers mirror) | undated scan; markings not checked by a human | Provenance unverified | D |
| MegaCD_MiSTer, <https://github.com/MiSTer-devel/MegaCD_MiSTer> | `a3a3da8`; `docs/mcd logs` not opened; hosts Sega-marked PDFs (excluded) | GPL-3.0 | D, E |
| ares, jgenesis | `9408cb4`, `c45e314`; licence files only | ISC; GPL-3.0 | E |
| I-RHOPE, <https://rhope.retrodev.com/segacd.html> | TLS certificate mismatch; fetched insecurely; integrity not guaranteed | No licence | D, E (and PR #16) |
| megadrive.org Sega manual TOC | HTTP 200; TOC titles only | **CONFIDENTIAL-marked scans: excluded** (Issue #17) | C, D, E |
| <https://www.sega.jp/history/hard/mega-cd/> | **HTTP 403** (Cloudflare challenge) on 2026-10-08 in every area; content not verified | n/a | A–E |
| I-RETROSIX, Sega Retro, Plutiedev | login wall; Anubis bot challenge; not read | n/a | E |
| gendev / SpritesMind threads, krikzz mcd-verificator | not fetched / not obtained (known second-hand from emulator comments) | unknown | B, D |

Not examined by any area (from the areas' "not investigated" lists):

- the content of the excluded manuals and Tech Bulletins;
- BlastEm, ares, jgenesis and MiSTer source code;
- the krikzz mcd-verificator test list;
- Kosinski / Nemesis / Enigma format documentation;
- LC89513K, LC7883 and RF5C164 datasheets;
- public game disassemblies (policy-sensitive);
- patents and FCC filings;
- per-model hardware variants;
- public Mode-1 homebrew such as the MSU-MD drivers.

## 7. Consolidated matrix

This table holds all 406 rows of the five area files, verbatim as corrected per §8, in area order. Only two mechanical edits were made:

- relative link targets were rebased from `coverage/` to this directory;
- `[X-nn]` tags (§3) were appended to the ID cell.

`python tools/audit/coverage_rate.py --check` fails if this table drifts from the area files. Abbreviations inside cells are defined in the source-register section of each area file.

<!-- BEGIN GENERATED: matrix -->
| ID | Required behavior | Level | Existing material (Y/N/partial) | Exact reference URL + location | Provenance & usage terms | Implementable from public material only? (Y/Cond/N + why) | Specific missing information | Coverable by own test? | Verifiable in emulator only? | Real hardware needed? | Blocker? (Y/N + why) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ROM-01 | Mode 2: the boot ROM occupies Main `$000000-$01FFFF` (128 KiB) | LA | Y. ESTIMATED from public sources (CONFIRMED only with excl: S-HW p.12/16) | GPGX-F `core/cd_hw/scd.h:73`, `core/cd_hw/scd.c:1605-1614`. PICO `pico/pico_int.h:556`, `pico/cd/memory.c:1232-1233`. CLOWN `source/bus-main-m68k.c:508-520`. MCDBOOT `src/main/core.asm:61` (pads to `$20000`). MEGADEV `docs/main_bios.md:30` | emu NC/AGPL cite-only; MCDBOOT 0BSD; MEGADEV MIT | Y: five public sources agree | ROM chip capacity per model (OQ-16) | Y (ROM validator) | Y | N for LA (Y before release) | N |
| ROM-02 | Emit exactly 131072 bytes, every byte defined | LA | Y (PROJECT-RULE) | PR #16 `docs/specifications/rom-layout.md` R-02, `invariants.json` | project rule | Y | — | Y | Y | N | N |
| ROM-03 | Same size and layout across JP/US/EU and all models | LC | partial (ESTIMATED) | GPGX-F `core/loadrom.c:405-420` (one 128 KiB buffer for all three regions) | emu cite-only | Cond: an emulator assumption only | Per-model capacity (Model 1/2, CDX, Wondermega, X'Eye, LaserActive) | N (needs physical evidence) | N | Y (public PCB photos / chip markings, no dumping) | N |
| ROM-04 | Mode 1 (cartridge boot): boot ROM at `$400000-$41FFFF` | LC | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.c:1598-1614`. PICO `pico/cd/memory.c:1226-1233`. MEGADEV `lib/main/memmap.def.h:30-63` (Mode-1 Word RAM `$600000`, PRG window `$420000`) | as above | Cond: emulators and SDK agree; no non-excluded hardware document | Hardware confirmation | Y (Mode-1 probe cartridge, OQ-1) | Y | Y | N |
| ROM-05 | BIOS must not rely on anything in `$040000-$1FFFFF` (mirrors) | LA | partial (UNCONFIRMED: GPGX mirrors every 256 KiB; PICO and CLOWN do not) | GPGX-F `core/cd_hw/scd.c:1613,1626-1645`. PICO `pico/cd/memory.c:1232-1233`. CLOWN `source/bus-main-m68k.c:427-536` | as above | Y as an avoidance rule | Real address decode (OQ-3) | Y | N | Y (to characterise only) | N |
| ROM-06 | ROM header starts with `"SEGA"` at `$100`. It is the source of the TMSS write, and Mode-1 software reads it at `$400100` | LA | partial (ESTIMATED) | MCDBOOT `src/main/main.asm:30-33` (copies the long at ROM `$100` to the TMSS register), `src/main/header.asm:95`. PICO `pico/cd/memory.c:1220-1223` (comment) | as above | Cond: the TMSS mechanism is generic Mega Drive knowledge outside the examined set; the detection use is an emulator comment | Whether TMSS inspects the expansion ROM (OQ-6) | Y | Y (no TMSS model for MCD in GPGX) | Y | N |
| ROM-07 | ROM-type field `"BR"` at `$180` (emulators then treat a side-loaded image as a boot ROM) | LA | Y (CONFIRMED, scope emu) | GPGX-F `core/loadrom.c:48,791-829` (identical to upstream). PICO `pico/media.c:373-381` (`"BOOT"` at `$124`/`$128`). MCDBOOT `src/main/header.asm:99` | as above | Y (developer convenience) | — | Y | Y | N | N |
| ROM-08 | 16-byte model string at `$120` selects the GPGX fader model | LC | Y (scope emu only) | GPGX-F `core/loadrom.c:422-442`, `core/cd_hw/scd.c:1504-1525` | emu | Cond: meaning is emulator-only | Whether any real software reads it | Y | Y | N | N |
| ROM-09 | Boot-ROM header checksum not checked | LA | partial | GPGX-F `core/loadrom.c:279-288`. PICO `pico/media.c:256-381` | emu | Y (scope emu); hardware UNCONFIRMED | Hardware/TMSS check | Y | Y | Y | N |
| ROM-10 [X-13] | Mode-1 compatibility: Kosinski-compressed Sub-CPU BIOS at ROM `$16000`, with `"SEGA"` at offset `$6D` of the compressed data, because Mode-1 software finds and unpacks it itself | LC | partial (ESTIMATED, single source) | MCDBOOT `README.md` § "Mode 1 Compatibility"; `src/main/core.asm:48-55` | 0BSD; origin of the offsets **undocumented** | Cond: one source with unstated provenance; Kosinski format spec not examined | Detection algorithm used by Mode-1 software; per-region variance; whether a bit-exact compressor is required | Y (public Mode-1 homebrew in an emulator with our ROM) | Y | Y | **Y** for the LC Mode-1 subset: single source, unknown provenance |
| ROM-11 [X-08] | Main-side "boot ROM library" branch table at ROM `$000280` (soft/hard reset, control panel, controllers, VDP helpers…) | LC | partial (UNCONFIRMED) | MEGADEV `docs/main_bios.md:12,30-44`. MCDBOOT `src/main/function_table.asm:17-102` (a second, 0BSD, implementation of the same table) | MEGADEV states the table is known **from reverse engineering**; MCDBOOT origin unstated | N until OQ-7 is decided. A second public source exists, but it may share the same origin | Clean-room entry list and semantics | Y (clean-room black-box tests with retail titles) | N | Y (or original-BIOS observation under a clean-room protocol) | **Y**: legal/process (OQ-7) |
| ROM-20 | Reset vectors: SSP long at `$000000`, PC long at `$000004` | LA | Y (CONFIRMED) | M68K §6.3.1 p.6-11–6-12; Table 6-2 p.6-7 | vendor manual, cite only | Y | — | Y | Y | N | N |
| ROM-21 | Initial PC even and inside the ROM window | LA | Y (CONFIRMED derived) | M68K §6.3.10 p.6-19; ROM-01 | as above | Y | — | Y (validator) | Y | N | N |
| ROM-22 | Initial SSP even and inside Work RAM | LA | Y (CONFIRMED derived) | M68K §6.2.5 p.6-10, §6.3.10 p.6-19 | as above | Y | — | Y | Y | N | N |
| ROM-23 | After reset S=1, T=0, I=7, and no context is stacked | LA | Y (CONFIRMED) | M68K §6.3.1 p.6-11 | as above | Y | — | Y | Y | N | N |
| ROM-24 | All vectors 2–63 point to valid handlers (bus/address error, illegal, zero divide, CHK, TRAPV, privilege, trace, line A/F, uninitialised interrupt 15, spurious 24, autovectors 25–31, TRAP 32–47, reserved) | LA | Y | M68K Table 6-2 p.6-7, §6.3.3–6.3.4 p.6-13. MCDBOOT `src/main/header.asm:21-89` (complete example) | as above | Y | — | Y (validator: every vector even and inside ROM/RAM) | Y | N | N |
| ROM-25 | Main interrupt sources: level 2 external port, level 4 H-INT, level 6 V-INT, autovectored | LA | partial (CPU part CONFIRMED; level→source ESTIMATED) | M68K p.5-10 (autovector = `$18` + level), §6.3.2 p.6-12. MEGADEV `lib/main/memmap.def.h:69-74`. MCDBOOT `src/main/header.asm:49-55` | as above | Cond: the level→source mapping is generic Mega Drive knowledge from SDKs | — | Y | Y | N | N |
| ROM-26 [X-03] | ROM vectors point into a Work-RAM table of 6-byte `JMP abs.l` entries at `$FFFD00`: exception/reset `$FFFD00`, V-INT `$FFFD06`, H-INT `$FFFD0C`, level 2 `$FFFD12`, TRAP #0–15 `$FFFD18-$FFFD72`, CHK `$FFFD78`, address error `$FFFD7E`, zero divide `$FFFD84`, TRAPV `$FFFD8A`, line A `$FFFD90`, line F `$FFFD96`, privilege `$FFFD9C`, trace `$FFFDA2`, cart-BRAM `$FFFDAE` | LB | partial (ESTIMATED; two sources agree) | MEGADEV `lib/main/memmap.def.h:68-99` (gives the **operand** address, entry + 2). MCDBOOT `include/mcd_main.inc:83-112` (entry address), `src/main/call_table.asm:21-50` | MEGADEV MIT, partly RE; MCDBOOT 0BSD, provenance caveat | Cond: two public sources agree once the +2 offset is normalised; they may share an origin | Use of `$FFFDA8`; which entries are initialised before IP entry | Y (homebrew IP patches `$FFFD06`) | Y | N | N |
| ROM-27 [X-03] | Address error and illegal instruction share one jump slot (`$FFFD7E`) | LC | partial (ESTIMATED) | MEGADEV `lib/main/memmap.def.h:92-93`. MCDBOOT `include/mcd_main.inc:104-105` | as above | Cond. **Updates OQ-12:** the MegaDev "duplicate" is corroborated by a second source, so it is probably intentional rather than a typo | Original-BIOS confirmation | Y (clean-room observation) | N | Y | N |
| ROM-28 | Reads of the H-INT vector low word (`$000072`) return gate-array register `$A12006` | LB | partial (ESTIMATED) | GPGX-F `core/mem68k.c:553-556,1279-1281`. PICO `pico/cd/memory.c:129-131,235-242`. CLOWN `source/bus-main-m68k.c:511-516,695,1188-1189`. MEGADEV `lib/main/gate_arr.def.h:261-266` | as above | Cond: four public sources agree; no non-excluded hardware document | Write width (byte vs word) | Y | Y | Y | N |
| ROM-29 | H-INT vector high word at `$000070`, and the power-on value of `$A12006` | LC | N (UNCONFIRMED; sources conflict: GPGX `$FFFF:$FFFF`; PICO `$FF` bytes when no cartridge; MEGADEV `$00FF`; CLOWN low word `$FD0C`) | GPGX-F `core/cd_hw/scd.c:1810-1812`. PICO `pico/cd/mcd.c:80-81`. MEGADEV `lib/main/gate_arr.def.h:261-262`. CLOWN `source/clownmdemu.c:135` | as above | Cond: sidestep by design (ROM holds `$FFFF` at `$70`; BIOS writes `$A12006`=`$FD0C` before IP entry) | Real power-on value | N | N | Y (Mode-1 probe, OQ-1) | N (mitigable) |
| ROM-30 | Main init: `SR=$2700`, SP loaded, interrupts masked until the jump table exists | LA | Y | M68K §6.3.1 p.6-11. MCDBOOT `src/main/main.asm:21-23` | as above | Y | — | Y | Y | N | N |
| ROM-31 [X-15] | TMSS: if `$A10001 & $0F` ≠ 0, write `"SEGA"` to `$A14000` before touching the VDP | LA | partial | MCDBOOT `src/main/main.asm:30-33` | 0BSD | Cond: generic Mega Drive knowledge (MD documentation not examined); Mega-CD relevance UNCONFIRMED (OQ-6) | Whether expansion boot engages TMSS | Y | Y | Y | N |
| ROM-32 | Tell cold boot from soft reset (I/O control registers non-zero ⇒ soft reset) | LA | partial (ESTIMATED) | MCDBOOT `src/main/main.asm:25-28`. CLOWN `source/clownmdemu.c:79-81` ("standard Sega SDK bootcode") | as above | Cond | I/O control register values after the Mega-CD reset button | Y | Y | Y | N |
| ROM-33 | Cold boot clears Main Work RAM (power-on contents undefined) | LA | Y (design) | MCDBOOT `src/main/main.asm:36-46` (clears only `$FF8000-$FFFFFF`). CLOWN `source/clownmdemu.c:63-67` | as above | Y | How much of the IP area must survive | Y | Y | N | N |
| ROM-34 | Detect the attached Mega-CD: `$A10001` bit 5 reads 0 | LB | partial | CLOWN `source/bus-main-m68k.c:598-600` | AGPL cite-only | Cond: one emulator in the examined set | — | Y | Y | Y | N |
| ROM-35 | Read region and TV standard from `$A10001` bits 7/6 | LB | partial | CLOWN `source/bus-main-m68k.c:600` | as above | Cond | — | Y | Y | N | N |
| ROM-36 | Before IP entry: VDP in a known state, PSG silent, Z80 initialised, controllers initialised | LA | partial | MCDBOOT `src/main/main.asm:52-73` | 0BSD | Cond: generic Mega Drive VDP/Z80 knowledge, outside this area | (VDP/IO area) | Y | Y | N | N |
| ROM-37 | Effect of the 68000 `RESET` instruction on Mega-CD hardware (gate array, Sub CPU) | LC | N | M68K §5.5 p.5-29 (asserts RESET for 124 clocks; CPU itself not reset), §6.3.1 p.6-12 | vendor | N: Mega-CD `/RESET` wiring not in non-excluded sources | What `RESET` resets on Mega-CD | N | N | Y | N (the BIOS need not execute `RESET`) |
| ROM-38 | Mega-CD side of a console soft reset (reset button): what is reset | LC | partial (UNCONFIRMED) | GPGX-F `core/cd_hw/scd.c:1867-1874` (TODO comment; communication registers kept) | emu | Cond | Full list of reset registers | Y (Mode-1 probe + reset button) | N | Y | N |
| ROM-40 [X-22] | Power-on: Sub CPU held in reset with its bus requested (`$A12001`: SBRQ=1, SRES=0) | LA | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.c:1814-1816,1859-1862`. PICO `pico/cd/mcd.c:76-79` (comment "tested"). CLOWN `source/clownmdemu.c:99-100` | emu | Cond: three emulators agree | Hardware read-back (OQ-13) | Y (Mode-1 probe) | Y | Y | N |
| ROM-41 [X-21] | SRES/SBRQ handshake: write, then poll the read-back until it latches. The Sub resets on an SRES 0→1 edge, and SRES=0 forces SBRQ to read 1 | LA | partial (ESTIMATED) | GPGX-F `core/mem68k.c:715-756` (comments "verified on real hardware" at :748, :752). PICO `pico/cd/memory.c:186-208` (the "verified" SRES=0 => SBRQ=1 rule at :186-187 is commented out, so PICO does not apply it; cf. COM-05) (corrected during integration review). MCDBOOT `src/main/main.asm:75-97` | as above | Cond | Latch timing | Y | Y | Y | N |
| ROM-42 | Sub reset vectors come from PRG-RAM `$000000/$000004`, so the BIOS writes a Sub vector table and program to PRG-RAM before releasing SRES | LA | Y | M68K §6.3.1 p.6-11. GPGX-F `core/cd_hw/scd.c:1698-1699`. CLOWN `source/bus-sub-m68k.c:709-711`. MCDBOOT `src/main/main.asm:83-93`, `src/sub/header.asm:21-22` | as above | Y: CPU rule plus three consistent maps | — | Y | Y | N | N |
| ROM-43 [X-20] | Clear PRG-RAM write protection before loading the Sub program; set it again afterwards | LA | partial (emulators disagree) | MCDBOOT `src/main/main.asm:83-89` (WP=0, then `$2A`). CLOWN `source/bus-main-m68k.c:972` (Main writes obey WP). GPGX-F `core/cd_hw/scd.c:160-182,1624-1645` (only Sub writes checked) | as above | Cond: clearing WP first is safe either way | Whether WP applies to Main-CPU writes | Y | Y | Y | N |
| ROM-44 [X-11] | Sub hard-reset init: clear status/communication registers, reset peripherals (`$FF8001` bit 0), mask IRQs (`$FF8032`=0), set Word RAM mode, reset the stopwatch, init PCM | LA | partial | MCDBOOT `src/sub/main.asm:21-53` | 0BSD | Cond | Which steps are mandatory | Y | Y | N | N |
| ROM-45 | Sub system area: `$5E80` common work, `$5EA0` BOOTSTAT, BIOS entries `$5F0A-$5F22`, USERCALL0-3 `$5F28-$5F3A`, SP header `$6000` | LB | partial (ESTIMATED) | MEGADEV `lib/sub/memmap.def.h:64-95`, `lib/sub/bios.def.h:50-127`. MCDBOOT `include/mcd_sub.inc:213-226`. excl: S-BIOS p.4 | MegaDev says the values come from the official BIOS manual (excluded); MCDBOOT states no origin (corrected during integration review) | Cond: two public SDKs agree; MegaDev attributes them to the excluded manual (Issue #17) and MCDBOOT's origin is unstated (corrected during integration review) | — | Y | Y | N | N |
| ROM-46 | Sub exception jump table `$5F40-$5FFF` of 6-byte `JMP` entries (address error `$5F40` … level 1 `$5F76` … level 7 `$5F9A`, TRAPs after) | LB | partial (ESTIMATED) | MEGADEV `lib/sub/memmap.def.h:64-95`. MCDBOOT `include/mcd_sub.inc:227-242` | as ROM-45 | Cond | — | Y | Y | N | N |
| ROM-47 [X-14] | Sub stack location and size | LB | partial (conflict) | MCDBOOT `src/sub/variables.inc:23-24` (`$5D80-$5E80`). excl: S-BIOS p.4 (heap/stack `$5C00`) | as above | Cond | Stack depth that SPs expect | Y | Y | N | N |
| ROM-48 | Sub IRQs enabled before user code (at least level 2 from Main and level 4 CDD) | LB | partial | MCDBOOT `src/sub/main.asm:56` | 0BSD | Cond | The original's full enable set | Y | Y | N | N |
| ROM-49 [X-12] | SR and register state when the BIOS calls USERCALL0 (init) and USERCALL1 (main) | LC | partial (design only) | MCDBOOT `src/sub/main.asm:62-72` (`$2200` during init, `$2000` after; registers zeroed) | 0BSD | Cond: the original state is UNCONFIRMED | Original values | Y (an SP that reports SR via the communication registers) | N | Y | N |
| ROM-50 | Main V-INT handler raises Sub level 2 (IFL2, `$A12000` byte bit 0) every frame; this drives `_WAITVSYNC` and USERCALL2 | LB | partial | MCDBOOT `src/main/interrupt.asm:23,131-135`, `include/mcd_main.inc:36`. GPGX-F `core/mem68k.c:689` | as above | Cond | — | Y | Y | N | N |
| ROM-51 | Main↔Sub boot handshake through the communication flags/registers (own protocol; registers cleared before IP entry) | LA | Y (design) | MCDBOOT `src/main/main.asm:61`, `src/sub/main.asm:21-27` | — | Y: our own design | What the original leaves in the registers (LC) | Y | Y | N | N |
| ROM-60 | PRG-RAM window `$020000-$03FFFF` usable only while SBRQ=1 or SRES=0 | LA | partial (ESTIMATED) | GPGX-F `core/mem68k.c:758-800`. PICO `pico/cd/memory.c:203-206`. CLOWN `source/bus-main-m68k.c:525-531,968-970` | emu | Cond: three emulators agree | — | Y | Y | Y | N |
| ROM-61 | Hardware result of a Main access to the PRG-RAM window while the Sub owns it | LC | N (UNCONFIRMED) | CLOWN `source/bus-main-m68k.c:525-528` (logs, reads 0). GPGX-F `core/mem68k.c:786-792` (unused handlers) | emu | N | Hang, open bus or ignored? | Y | N | Y | N (the BIOS avoids it) |
| ROM-62 | PRG-RAM bank select: `$A12003` bits 7-6 choose four 128 KiB banks | LA | partial (ESTIMATED; official scan cropped, OQ-14) | GPGX-F `core/mem68k.c:826-828`. PICO `pico/cd/memory.c:212-219`. CLOWN `source/bus-main-m68k.c:685,1177` | emu | Cond: three emulators agree | Hardware bit check | Y | Y | Y | N |
| ROM-63 [X-20] | `$A12002` write protection: protects (value × 512) bytes from `$0` | LA | partial | GPGX-F `core/cd_hw/scd.c:158-182`. CLOWN `source/bus-main-m68k.c:972`. PICO `pico/cd/memory.c:209-211` | emu | Cond | Scope for Main writes (ROM-43) | Y | Y | Y | N |
| ROM-64 | Power-on Word RAM: 2M mode, owned by Main (RET=1, DMNA=0) | LB | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.c:1815-1830`. PICO `pico/cd/mcd.c:79`. CLOWN `source/clownmdemu.c:104-107` (its comment cites excl: hardware manual p.24) | emu | Cond | — | Y | Y | Y | N |
| ROM-65 [X-01] | Word RAM mode and owner at IP/SP entry | LC | partial (UNCONFIRMED; CLOWN hands it to Sub, MCDBOOT's Sub sets 1M) | CLOWN `source/clownmdemu.c:529-531`. MCDBOOT `src/sub/main.asm:32-38` | as above | Cond | Original state | Y | N | Y | N |
| ROM-66 | Main gate-array registers `$A12000-$A1202F` (GPGX mirrors them to `$A120FF`) | LA | partial | GPGX-F `core/mem68k.c:689-830`. CLOWN `source/bus-main-m68k.c:685-695,1150-1189`. MEGADEV `lib/main/gate_arr.def.h:52-511` | as above | Cond | Mirroring | Y | Y | Y | N |
| ROM-67 | Main Work RAM `$FF0000-$FFFFFF`, with `$FFFD00-$FFFFFF` reserved for the system | LB | partial (ESTIMATED) | MEGADEV `docs/megacd_dev.md:19-31`, `docs/main_bios.md:56-60,116`. MCDBOOT `src/main/variables.inc:42-58` | MEGADEV quotes official text (caveat) | Cond | — | Y | Y | N | N |
| ROM-68 [X-02] | Main SSP at IP entry: `$FFFD00` or `$FFFC00` (OQ-2) | LB | partial (conflict) | MEGADEV `docs/main_bios.md:56-57` (`$FFFD00`), `docs/megacd_dev.md:21,29` (`$FFFC00`). MCDBOOT `src/main/variables.inc:47-48`, `src/main/main.asm:23` (`$FFFD00`) | as above | Cond: use `$FFFD00` (two of three statements) | Original value | Y | N | Y | N |
| ROM-69 | IP runs at `$FF0000` in supervisor mode; extent of the IP area | LB | partial | CLOWN `source/clownmdemu.c:498-524` (copies 32 KiB; comment "This is what Sega's BIOS does"). MCDBOOT `src/main/main.asm:36-46,102`. MEGADEV `docs/main_bios.md:56` | as above | Cond | Maximum IP size; exact copy behaviour | Y | Y | N | N |
| ROM-70 [X-02] | Main register state at IP entry | LC | partial | MCDBOOT `src/main/main.asm:99-102` (D0-A6 and USP zeroed) | 0BSD | Cond: design only | Original state | Y | N | Y | N |
| ROM-71 [X-08] | Main BIOS work variables `$FFFDB4-~$FFFE58` (VDP register cache etc.) | LC | partial (UNCONFIRMED) | MEGADEV `docs/megacd_dev.md:23-27`, `lib/main/bios.def.h:44-146`. MCDBOOT `src/main/variables.inc:49-58` (VDP cache at the same `$FFFDB4`) | RE caveat | N until OQ-7 | Clean-room layout | Y (black-box) | N | Y | **Y**: legal/process (OQ-7) |
| ROM-72 | Mode 2: cartridge slot / expansion area at `$400000-$7FFFFF` | LC | partial | GPGX-F `core/cd_hw/cd_cart.c:246-262`. PICO `pico/cd/memory.c:1242-1248`. CLOWN `source/bus-main-m68k.c:429-468` | emu | Cond | — | Y | Y | Y | N |
| ROM-80 | Sub PRG-RAM `$000000-$07FFFF` (512 KiB) | LA | partial (ESTIMATED; excl: S-HW p.14) | GPGX-F `core/cd_hw/scd.h:74`, `core/cd_hw/scd.c:1689-1699`. CLOWN `source/bus-sub-m68k.c:709` | emu | Cond | — | Y | Y | N | N |
| ROM-81 | Sub writes below the write-protect boundary are ignored | LB | partial | GPGX-F `core/cd_hw/scd.c:158-182` | emu | Cond: one emulator checked | Ignored or faulting? | Y | Y | Y | N |
| ROM-82 | Sub Word RAM `$080000-$0BFFFF` (2M) / `$0C0000-$0DFFFF` (1M bank) | LB | partial | GPGX-F `core/cd_hw/scd.c:1714-1742`. CLOWN `source/bus-sub-m68k.c:256` | emu | Cond | — | Y | Y | N | N |
| ROM-83 | Sub access to Main-owned 2M Word RAM: stall or something else (OQ-4) | LC | N (UNCONFIRMED) | GPGX-F `core/cd_hw/scd.c:1832-1839` (no /DTACK) | emu | N | Hardware behaviour | Y | N | Y | N (the BIOS avoids it) |
| ROM-84 | Backup RAM `$FE0000-$FE3FFF`: 8 KiB on odd addresses | LB | partial (ESTIMATED) | GPGX-F `core/cd_hw/scd.h:77`, `core/cd_hw/scd.c:1760-1768`. PICO `pico/cd/memory.c:945-971` | emu | Cond | Word-access behaviour (PICO flags an anomaly at :953, :969) | Y | Y | Y | N |
| ROM-85 | PCM `$FF0000-$FF7FFF` (mirrored) and Sub registers `$FF8000-$FF81FF` | LA | partial | GPGX-F `core/cd_hw/scd.c:530,1771-1779` | emu | Cond | — | Y | Y | N | N |
| ROM-86 | Sub address decoding mirrors every 1 MiB | LC | N (UNCONFIRMED) | GPGX-F `core/cd_hw/scd.c:1684-1699` | emu | Cond (avoid) | Hardware decode (OQ-17) | Y | N | Y | N |
| ROM-87 | Boot must not clear or format Backup RAM; PRG-RAM and Word RAM power-on contents are undefined | LA | partial (design) | GPGX-F `core/cd_hw/scd.c:1791-1795` (emulator clears its buffers; saves loaded separately) | emu | Y (design rule) | — | Y | Y | N | N |
| ROM-90 [X-07] | On-media format of internal Backup RAM (directory, signature, block size) that existing saves use | LC | N | Not found in the sources examined. CLOWN `source/bus-sub-m68k.c:695,715` has only a block-size macro and an HLE comment ("None of this … is accurate"). MEGADEV `lib/sub/bram.def.h` has function codes only | — | N | Full on-media format | Y (clean-room: format and save with the original BIOS on one's own unit, read back the data) | N | Y | **Y** (LC save interoperability) |
| ROM-91 | Detect "BRAM present / unformatted" at boot | LB | N | Not found in the sources examined | — | Cond: an own format is enough for LB | Original detection rule (LC) | Y | Y | N | N |
| ROM-92 | RAM cartridge: ID at `$400001` (size code), data at `$600001+` (odd bytes), write enable `$7FFFFF` bit 0 | LC | partial | GPGX-F `core/cd_hw/cd_cart.c:42-173,196-244`. PICO `pico/cd/memory.c:672-727` | emu | Cond: both fit size = 8 KiB << ID (GPGX ID 6 = 512 KiB, `cd_cart.c:205`; PICO ID 3 = 64 KiB, `memory.c:680`) | Official size-code semantics; cartridge format | Y | Y | Y | N |
| ROM-93 | RAM cartridge disabled in Mode 1 | LC | partial (emu) | GPGX-F `core/cd_hw/cd_cart.c:184-188` | emu | Cond | — | Y | Y | Y | N |
| ROM-94 | Main `$FFFDAE` cartridge-BRAM handler vector | LC | partial | MEGADEV `lib/main/bramcart.def.h:11`. MCDBOOT `include/mcd_main.inc:112` | RE caveat | Cond | Semantics and function codes | Y | N | Y | N |
| ROM-100 | One region-neutral image (region and TV standard read at runtime) | LB | Y (design) | CLOWN `source/bus-main-m68k.c:600`. MCDBOOT `src/main/header.asm:107` (`"JUE"`) | — | Y | — | Y | Y | N | N |
| ROM-101 [X-06] | Disc region / security-block check | LC | partial | PR #16 R-31 / OQ-8 (I-RHOPE only). CLOWN `source/clownmdemu.c:511` (region byte read, commented out) | single independent source | N (legal) | Policy | Y (own discs) | N | Y | **Y**: legal (OQ-8) |
| ROM-102 | Model differences visible to the BIOS (fader/filter, front panel, LaserActive) | LC | partial | GPGX-F `core/cd_hw/scd.h:53-57`, `core/cd_hw/scd.c:1504-1525`. O-SEGAJP HTTP 403 | emu | Cond | Official model list | N | N | Y | N |
| ROM-103 | Region-dependent behaviour software expects from the BIOS | LC | N | Not found in the sources examined | — | N | Everything | N | N | Y | N |
| ROM-110 | Exception sequence and the 6-byte group 1/2 frame (SR+PC); RTE | LA | Y (CONFIRMED) | M68K §6.2.5 p.6-10 | vendor | Y | — | Y | Y | N | N |
| ROM-111 | Group-0 (bus/address error) long frame; stacked PC unpredictable | LA | Y | M68K §6.2.5 p.6-10, §6.3.9–6.3.10 p.6-16–6-19 | vendor | Y | — | Y | Y | N | N |
| ROM-112 | Interrupt mask; autovector = `$18` + level; level 7 non-maskable | LA | Y | M68K p.5-10, §6.3.2 p.6-12 | vendor | Y | — | Y | Y | N | N |
| ROM-113 | Uninitialised (15) and spurious (24) interrupt vectors | LA | Y | M68K §6.3.3–6.3.4 p.6-13 | vendor | Y | — | Y | Y | N | N |
| ROM-114 | TRAP #0-15 → vectors 32-47 | LB | Y | M68K §6.3.5 p.6-13 | vendor | Y | — | Y | Y | N | N |
| ROM-115 | Illegal, line-A, line-F | LA | Y | M68K §6.3.6 p.6-14 | vendor | Y | — | Y | Y | N | N |
| ROM-116 | Privilege violation, supervisor/user switching, USP initialisation | LA | Y | M68K §6.1.3 p.6-2, §6.3.7 p.6-15 | vendor | Y | — | Y | Y | N | N |
| ROM-117 | Trace | LC | Y | M68K §6.3.8 p.6-15 | vendor | Y | — | Y | Y | N | N |
| ROM-118 | Priority of simultaneous exceptions | LC | Y | M68K §6.2.3 p.6-8 | vendor | Y | — | Y | Y | N | N |
| ROM-119 | Double bus fault halts the CPU; only an external reset recovers | LA | Y | M68K §5.4.4 p.5-28 | vendor | Y | — | Y | Y | N | N |
| ROM-120 | Odd-address word/long access → address error | LA | Y | M68K §6.3.10 p.6-19 | vendor | Y | — | Y | Y | N | N |
| ROM-121 | Byte/MOVEP access to 8-bit odd-address devices (BRAM, PCM, RAM cartridge) | LB | Y | M68K p.2-13 (MOVEP), p.6-19 (MOVEP fault note) | vendor | Y | — | Y | Y | N | N |
| ROM-122 | `TAS` read-modify-write on the Mega Drive / Mega-CD bus | LC | partial | M68K §4.1.3 p.4-5 (indivisible RMW cycle). System-specific write-back behaviour: not found in the sources examined | vendor | Cond: the BIOS can avoid `TAS` | Whether gate-array registers and Word RAM honour the RMW write | Y (hardware probe) | N | Y | N |
| ROM-123 | Exception and instruction timing for timing-sensitive BIOS code | LC | Y | M68K Section 8 (MC68000 execution times; exception table p.8-10 per the TOC) | vendor | Y | Bus wait states on Mega-CD (not in M68K) | Y | Y | Y | N |
| ROM-124 | CPU clocks: Sub 12.5 MHz (50 MHz / 4); Main is the Mega Drive clock | LB | partial | GPGX-F `core/cd_hw/scd.h:60` (`SCD_CLOCK` 50 MHz). PICO `pico/cd/mcd.c:82` (12,500,000) | emu | Cond | Exact hardware tolerances | Y | Y | Y | N |
| COM-01 | SRES hold/release, reset on 0→1 | LA | Y | G `core/mem68k.c:1055-1086`; P `pico/cd/memory.c:183-202`; C `source/bus-main-m68k.c:1122-1151`; CB `src/main/main.asm:75-77,91-93`; MD `lib/main/gate_arr.def.h:25-52`; S-HW §4-1 p.56 (excluded) | Emulators non-commercial/AGPL (facts only); CB permissive; MD MIT | Y: three emulators, MD and CB agree. CONFIRMED (scope: emulator) | Edge-trigger vs level-trigger on hardware | Y | Y (for LA) | Y (before release) | N |
| COM-02 | SRES read-back | LA | Y | MD `lib/main/gate_arr.def.h:38-40`; C `source/bus-main-m68k.c:679-680`; CB `src/main/main.asm:75-77` (polling loop) | as above | Y: ESTIMATED | Delay before read-back changes | Y | Y | Y | N |
| COM-03 | SBRQ request and ack | LA | Y | G `core/mem68k.c:1064-1077`; P `pico/cd/memory.c:183-208`; MD `lib/main/gate_arr.def.h:41-43`; CB `src/main/main.asm:79-81,95-97` | as above | Y: ESTIMATED | Ack latency (emulators make it immediate) | Y | Y | Y | N |
| COM-04 [X-22] | Power-on register state | LA | Y | G `core/cd_hw/scd.c:1814-1816` (`$0002`/`$0001`); P `pico/cd/mcd.c:76-79` ("cold reset state (tested)") | emulators | Y: two emulators agree, P claims a test. ESTIMATED (OQ-13) | Cold-boot probe on hardware | Y | N | Y | N (BIOS writes known values instead of relying on them) |
| COM-05 [X-21] | SRES=0 forces SBRQ=1 | LC | partial | G `core/mem68k.c:1079-1086` ("verified on real hardware"); P `pico/cd/memory.c:186-187` (same rule commented out) | emulators | Cond: emulators disagree. UNCONFIRMED | Hardware read-back after SRES=0 | Y | N | Y | N |
| COM-06 | SBRQ ack 0 while Sub STOPped | LC | partial | G `core/mem68k.c:1088-1092` ("verified on real hardware") | single emulator | Cond: single source. ESTIMATED | Independent confirmation | Y | N | Y | N |
| COM-07 | PRG-RAM window only while bus-requested or reset | LA | Y | G `core/mem68k.c:1094-1128`; P `pico/cd/memory.c:1115-1124`; C `source/bus-main-m68k.c:525`; memory-map.md §1 | emulators | Y: CONFIRMED (scope: emulator) | Value read otherwise (open bus vs fault) | Y | Y | Y | N |
| COM-08 | BK0-1 bank select | LA | Y | G `core/mem68k.c:1172-1174`; P `pico/cd/memory.c:215-219,1119`; C `source/bus-main-m68k.c:1177`; MD `lib/main/gate_arr.def.h:106,110,179` | emulators + MD | Y: bits 6-7 agreed by three emulators and MD. ESTIMATED (OQ-14) | Hardware bit check | Y | Y | Y | N |
| COM-09 [X-20] | WP blocks Sub writes below WP×512 | LA | Y | G `core/cd_hw/scd.c:158-184`; P `pico/cd/memory.c:828-837,1267-1268`; MD `lib/main/gate_arr.def.h:123-124`; CB `src/main/main.asm:83,89` (writes 0, later `$2A`) | emulators + MD + CB | Y: ESTIMATED | Whether Main or CDC-DMA writes are also blocked (G and P: no; C `source/bus-main-m68k.c:972` blocks Main writes below WP×512, cf. ROM-43) (corrected during integration review) | Y | Y | Y | N |
| COM-10 | WP writable only from Main; Sub byte write to `$FF8002` hits mode bits | LC | partial | G `core/cd_hw/scd.c:857-858` (/LDS and /UDS ignored, "verified … mcd-verificator"); P `pico/cd/memory.c:391`; MD `lib/sub/gate_arr.def.h:84-98` | emulators + MD | Cond: ESTIMATED | Whether a Sub word write to the high byte is ignored on hardware | Y | N | Y | N |
| COM-11 | IFL2 raises Sub L2 if IEN2 | LB | Y | G `core/mem68k.c:1149-1164`; P `pico/cd/memory.c:171-182`; C `source/bus-main-m68k.c:1127,1144-1148`; MD `lib/main/gate_arr.def.h:44-46`; S-HW §4-1 p.56 (excluded) | as above | Y: CONFIRMED (scope: emulator), three emulators | none for LB | Y | Y | Y | N |
| COM-12 | IEN2 mirror on Main | LB | Y | G `core/cd_hw/scd.c:1120-1121`; P `pico/cd/memory.c:117-118`; MD `lib/main/gate_arr.def.h:47-48,91` | as above | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-13 | IFL2 read and clear semantics | LC | partial | G `core/cd_hw/scd.c:2379-2384` (cleared on ack; writing 0 ignored at `core/mem68k.c:1149-1164`); P `pico/cd/memory.c:178-181` (writing 0 clears and cancels the IRQ); MD `lib/main/gate_arr.def.h:46` | as above | Cond: emulators **conflict** on writing 0. UNCONFIRMED | Does writing 0 cancel a pending L2 on hardware? | Y | N | Y | N |
| COM-14 | BTST-only on `$A12000`; RMW side effects | LA | partial | MD `lib/main/gate_arr.def.h:50`; CB uses BSET/BCLR on `$A12001`/`$A12000` (`src/main/main.asm:76-96`, `src/main/interrupt.asm:134-135`) | MD (origin unstated), CB | Cond: the safe subset is known (plain byte writes), the hazard is not. UNCONFIRMED | Whether a BSET on `$A12001` disturbs `$A12000` on hardware | Y | N | Y | N (avoid RMW) |
| COM-15 | Register mirroring to `$A120FF` | LC | partial | G `core/mem68k.c:370-371,1048-1049` | single emulator | Cond: CONFIRMED (scope: emulator) only | Hardware decode | Y | N | Y | N |
| COM-16 | `$A12006` H-INT low word | LB | Y | G `core/mem68k.c:553-557,1279-1283`; P `pico/cd/memory.c:129-131,235-242`; C `source/bus-main-m68k.c:692-695,1185-1190`; MD `lib/main/gate_arr.def.h:248-266`; CB `src/main/interrupt.asm:113-119` | as above | Y: ESTIMATED (R-16) | Byte-access behaviour | Y | Y | Y | N |
| COM-17 | H-INT high word at ROM `$70` | LC | partial | G `core/cd_hw/scd.c:1810-1812`; P `pico/cd/mcd.c:80-81`; MD `lib/main/gate_arr.def.h:261-262` | as above | Cond: three sources **conflict** (OQ-1); our ROM picks the value. UNCONFIRMED | Hardware probe (OQ-1) | Y | N | Y | N (our ROM controls `$70`) |
| COM-18 | Stopwatch: 12-bit, 30.72 µs, cleared by Sub | LC | Y | G `core/mem68k.c:559-567`, `core/cd_hw/scd.c:692-697,1443-1452,2005-2012`, `core/cd_hw/scd.h:60,67`; P `pico/cd/memory.c:100-106,444-449`; MD `lib/main/gate_arr.def.h:295-313`, `lib/sub/gate_arr.def.h:239-254`; CB `src/sub/main.asm:40` | as above | Y: ESTIMATED | none for the BIOS (only a clear is needed) | Y | Y | Y | N |
| COM-19 | Stopwatch prescaler phase on clear | LC | partial | P `pico/cd/memory.c:447` (open question in a comment) | single emulator | N: unknown | Whether a clear resets the 384-cycle prescaler | Y | N | Y | N |
| COM-20 | Main flag byte | LA | Y | G `core/mem68k.c:1292-1299`, `core/cd_hw/scd.c:562-570`; P `pico/cd/memory.c:246-249`; C `source/bus-main-m68k.c:1201-1211`; MD `lib/main/gate_arr.def.h:320-331`; CB `src/main/communication.asm:21-28` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-21 | Sub flag byte | LA | Y | G `core/cd_hw/scd.c:1087-1096,1454-1461`, `core/mem68k.c:396-406`; MD `lib/sub/gate_arr.def.h:262-275`; CB `src/sub/main.asm:22-23` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-22 | Byte write to either half updates the writer's own half | LC | partial | G `core/mem68k.c:934-941` ("!LWR is ignored", Space Ace, Dragon's Lair), `core/cd_hw/scd.c:1087-1088` ("verified … mcd-verificator"); P `pico/cd/memory.c:246-248` | emulators | Cond: two emulators agree. ESTIMATED | Hardware confirmation | Y | N | Y | N |
| COM-23 | Command words Main→Sub; Sub writes ignored | LA | Y | G `core/mem68k.c:1301-1309`, `core/cd_hw/scd.c:1151-1156,1576-1581`; P `pico/cd/memory.c:520-524`; C `source/bus-main-m68k.c:713-717`; MD `lib/sub/gate_arr.def.h:278-335` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-24 | Status words Sub→Main; Main writes ignored | LA | Y | G `core/cd_hw/scd.c:1142-1149,1570-1574`, `core/mem68k.c:575-587`; P `pico/cd/memory.c:517-518`; C `source/bus-main-m68k.c:719-723`; MD `lib/sub/gate_arr.def.h:338-391` | as above | Y: CONFIRMED (scope: emulator) | Effect of a Main write on hardware | Y | Y | Y | N |
| COM-25 | Byte access to command and status words | LB | Y | G `core/mem68k.c:409-425,959-964`, `core/cd_hw/scd.c:643-651,1167-1177`; P `pico/cd/memory.c:252-253`; CB `include/mcd_main.inc:46-77` | as above | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-26 | Comm registers cleared on power-on, kept on RES0 | LB | Y | G `core/cd_hw/scd.c:1804-1805,1867-1874` (msu-md-sample observation); P `pico/cd/mcd.c:69,88-105` | emulators | Y: ESTIMATED | Power-on contents on hardware (may be random) | Y | N | Y | N (BIOS clears them anyway) |
| COM-27 | BIOS clears comm registers before IP/SP | LB | partial | CB `src/main/main.asm:61`, `src/main/communication.asm:21-28`, `src/sub/main.asm:22-27` | CB (provenance unstated) | Y: our design choice. Compatibility ESTIMATED | Whether the original leaves non-zero values that software reads (COM-36) | Y | Y | N | N |
| COM-28 | Simultaneous access / tearing | LC | N | Not found in G, P, C, MD, CB (only emulator polling-sync code, e.g. G `core/cd_hw/scd.c:437-509`) | n/a | N: no source | Arbitration on concurrent access | Y (stress test) | N | Y | N (BIOS uses single-writer conventions) |
| COM-29 | Gate-array access wait states | LC | N | Not found in the sources examined. Emulators add ad-hoc delays (P `pico/cd/memory.c:264-270`, "Silpheed") | n/a | N | Cycle-level access cost | Y | N | Y | N |
| COM-30 | Own BIOS boot handshake | LA | Y (design) | Built on COM-20 to COM-24. Reference design: CB `src/main/main.asm:75-102` (no comm handshake; Main jumps to the IP after releasing Sub) | our design | Y: design freedom | none | Y | Y | Y | N |
| COM-31 | Main default V-INT raises IFL2 each frame | LB | Y | CB `src/main/interrupt.asm:21-23,134-135`; MD `docs/main_bios.md:692-698` (RE description of the original); S-HW §3-5 p.30 (excluded) | CB permissive; MD RE | Y: as our design. Compatibility ESTIMATED | Exact point in V-INT (before or after the user handler) | Y | Y | Y | N |
| COM-32 [X-12] | Sub L2 handler calls usercall2 | LB | Y | CB `src/sub/interrupt.asm:21-29`; MD `lib/sub/sp_header.s:23`, `docs/boot.md:19-26`, `lib/sub/cdrom.macro.s:23`; S-BIOS (excluded) | CB, MD | Cond: register/stack contract (CB clears a5) has one non-excluded source | Preserved or cleared registers, IPL during the call, re-entrancy | Y | Y (LB) | Y (LC) | **Y (LC)**: authoritative contract only in excluded S-BIOS |
| COM-33 [X-12] | Sub main loop usercall0/1 and return-code contract | LB | partial | CB `src/sub/main.asm:58-85` (init at SR `$2200`, loop on L2-driven VSync, -1 re-inits); CB `src/sub/module.asm:25-93` (header type parsing); MD `docs/boot.md:19-26` | CB, MD | Cond: one implementation plus SDK header | Official return codes, SR and timing | Y | Y (LB) | Y (LC) | **Y (LC)**: same root as COM-32 |
| COM-34 | Main waits for Sub ready before IP | LB | partial | CB `src/main/main.asm:91-102` (does **not** wait); C HLE-loads the IP (`source/clownmdemu.c:496-527`) | CB, emulator | Y: our design (add a flag handshake) | none | Y | Y | Y | N |
| COM-35 [X-08] | Original Main-BIOS comm-flag semantics | LC | partial | MD `docs/main_bios.md:359-368,680-732` (RE, "not well understood") | MD MIT but **RE-derived** (cf. OQ-7) | N: only an RE source, flagged uncertain by its author | Meaning of Main/Sub flag bits 0, 1, 2 and 6; which games depend on them | Y (black-box) | N | Y | **Y (LC)**: no clean source |
| COM-36 | Comm state expected by games at IP/SP entry and during disc access | LC | N | Not found in G, P, C, MD, CB, or L-VERIF (as reported) | n/a | N | Values and flag bits the original leaves | Y (X-9, needs legal decision) | N | Y | **Y (LC)** |
| COM-37 | Power-on 2M, Main owns | LA | Y | G `core/cd_hw/scd.c:1814-1839`; P `pico/cd/mcd.c:79`; memory-map.md W-01 | emulators | Y: ESTIMATED (W-01's CONFIRMED relies on excluded S-HW) | Hardware probe | Y | Y | Y | N |
| COM-38 | 2M: DMNA=1 gives to Sub, RET→0 | LB | Y | G `core/mem68k.c:1195-1271`; P `pico/cd/memory.c:221-231`; C `source/bus-main-m68k.c:1161-1175`; MD `lib/main/gate_arr.def.h:114-117` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-39 | 2M: Sub RET=1 returns to Main, DMNA clears | LB | Y | G `core/cd_hw/scd.c:1001-1048`; P `pico/cd/memory.c:398-402,420`; C `source/bus-sub-m68k.c:1146-1161`; MD `lib/sub/gate_arr.def.h:93-96` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-40 | 2M: DMNA=0 is a no-op | LC | Y | G `core/mem68k.c:1197`; P `pico/cd/memory.c:222-231` | emulators | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-41 | Non-owner access (Main unmapped; Sub stalls) | LC | partial | G `core/cd_hw/scd.c:80-116,1036-1043`, `core/mem68k.c:1205-1214`; P `pico/cd/memory.c:1131-1136` (Sub "sleeps"); C `source/bus-sub-m68k.c:902-905` (TODO citing S-HW p.24: CPU hangs) | emulators; C cites excluded S-HW | Cond: emulators agree on a stall; hardware UNCONFIRMED (OQ-4) | Hardware behaviour (hang, timeout or bus error) | Y | N | Y | N (BIOS never does it) |
| COM-42 | Switch latency, transient DMNA/RET | LC | partial | P `pico/cd/memory.c:264-270` (24-cycle delay hack, Silpheed) | emulator | N | Real latency | Y | N | Y | N |
| COM-43 | 2M↔1M switch and data re-arrangement | LB | Y | G `core/cd_hw/scd.c:748-808,867-1000`; P `pico/cd/memory.c:404-421`; C `source/bus-sub-m68k.c:1155`; MD `lib/sub/gate_arr.def.h:90-92` | as above | Y: CONFIRMED (scope: emulator); word-alternating interleave per G `scd.c:758-762` | Hardware check of interleave granularity | Y | Y | Y | N |
| COM-44 | 1M: RET selects banks | LB | Y | G `core/cd_hw/scd.c:877-952`; P `pico/cd/memory.c:1179-1195`; C `source/bus-sub-m68k.c:922`; MD `lib/main/gate_arr.def.h:134-136` | as above | Y: agreement (RET=0 → bank 0 to Main). ESTIMATED | none | Y | Y | Y | N |
| COM-45 | 1M swap request by DMNA=0 | LC | Y | G `core/mem68k.c:1185-1193`; P `pico/cd/memory.c:226-228`; C `source/bus-main-m68k.c:1165-1175` (+ L-GD p=16388, "contrary to the official documentation"); MD `lib/main/gate_arr.def.h:118-119` (**worded differently**) | emulators + forum | Cond: three emulators agree; MD wording and (per C) the official docs differ. ESTIMATED | Hardware confirmation | Y | N | Y | N |
| COM-46 | 1M: DMNA=1 remembered for 2M | LC | partial | G `core/mem68k.c:1180-1184`, `core/cd_hw/scd.c:966-998`; P `pico/cd/memory.c:221-225` (`dmna_ret_2m`) | emulators | Cond: the two emulators model it differently. ESTIMATED | Hardware | Y | N | Y | N |
| COM-47 | Owner after 1M→2M | LC | partial | G `core/cd_hw/scd.c:958-999`; P `pico/cd/memory.c:414-421`; C `source/bus-main-m68k.c:1156` (TODO, + L-GD p=15269) | emulators | Cond: UNCONFIRMED (C marks it unknown) | Hardware | Y | N | Y | N |
| COM-48 | Main cell-image view | LC | Y | G `core/cd_hw/scd.c:887-896`, `core/cd_hw/gfx.c:249-300`; P `pico/cd/memory.c:1187-1190`, `pico/cd/cell_map.c` | emulators | Y: ESTIMATED | none (formula in the emulators) | Y | Y | Y | N |
| COM-49 | Sub dot-image view and PM0/PM1 | LC | Y | G `core/cd_hw/scd.c:899-906`, `core/cd_hw/gfx.c:154-248,359-372`; P `pico/cd/memory.c:896-931,1191-1194`; MD `lib/sub/gate_arr.def.h:86,89` | emulators + MD | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-50 | 1M Sub bank at `$0C0000` | LB | Y | G `core/cd_hw/scd.c:908-912`; P `pico/cd/memory.c:1186`; C `source/bus-sub-m68k.c:1115-1123`; CB `include/mcd_sub.inc:23` | as above | Y: ESTIMATED (P maps to `$0EFFFF`, G to `$0DFFFF`) | Extent of the mirror | Y | Y | Y | N |
| COM-51 | Read masks: PM (Main side), BK (Sub side) | LC | Y | G `core/mem68k.c:373-380,533-540`, `core/cd_hw/scd.c:553-560,670-677`; P `pico/cd/memory.c:122,333` | emulators | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-52 [X-01] | Word RAM mode and owner at IP/SP entry | LB | partial | CB `src/sub/main.asm:32-38` (Sub BIOS sets **1M** and RET=1); G and P power-on is 2M/Main (COM-37); not stated in MD | CB vs emulators | Cond: sources **conflict**. Original behaviour UNCONFIRMED | What the original leaves, and what homebrew SDKs and games assume | Y | N | Y | **Y (LB/LC)**: a wrong state breaks software that does not set the mode itself |
| COM-53 | CDC DMA suspend/resume on ownership or SBRQ change | LC | partial | G `core/mem68k.c:1110-1145,1254-1269`, `core/cd_hw/scd.c:1011-1020` | single emulator | Cond: ESTIMATED | Hardware | Y | N | Y | N |
| COM-54 | Gfx needs 2M, Sub-owned | LC | partial | G `core/cd_hw/gfx.c:604-676` (comment at 676) | single emulator | Cond: ESTIMATED | Behaviour if violated | Y | N | Y | N |
| COM-55 | Main loads Sub BIOS into PRG-RAM before reset release | LA | Y | CB `src/main/main.asm:75-97` | CB permissive | Y: own design, proven in ClownMDEmu | none | Y | Y | Y | N |
| COM-56 | Sub reset vectors from PRG-RAM 0 | LA | Y | CB `src/sub/header.asm:21-22`; G `core/cd_hw/scd.c:1859-1862`; S-M68K §6 (reset exception) | CB, emulator, CPU official | Y: CONFIRMED (derived: S-M68K reset + mapping in memory-map.md §2) | none | Y | Y | Y | N |
| COM-57 | SP at `$6000`, BIOS area protected | LB | Y | MD `docs/boot.md:3`; C `source/clownmdemu.c:498-527`; CB `src/sub/main.asm:58-60`, `src/main/main.asm:89` | MD, CB, emulator | Y: ESTIMATED | The original's WP value (CB uses `$2A`, i.e. up to `$5400`) | Y | Y | Y | N |
| COM-58 [X-13] | Mode-1 Sub-BIOS detection signature | LC | partial | CB `README.md:20-28` ("SEGA" at offset `$6D` of the Kosinski-compressed Sub BIOS); P `pico/cd/memory.c:1220-1223` (R-20) | CB (provenance unstated) | Cond: single source | Which software scans how; exact format | Y | N | Y | **Y (LC, Mode 1)**: single unverified source |
| COM-59 | LED bits | LC | Y | MD `lib/sub/gate_arr.def.h:21-62`; G `core/cd_hw/scd.c:839-844` | MD, emulator | Y: ESTIMATED | Hardware polarity | Y | N | Y | N |
| COM-60 | RES0 peripheral reset; reads 1 | LA | Y | G `core/cd_hw/scd.c:599-604,846-855,1867-1874`; P `pico/cd/memory.c:330,387-389`, `pico/cd/mcd.c:88-105`; CB `src/sub/main.asm:29`; MD `lib/sub/gate_arr.def.h:31-34` | as above | Y: ESTIMATED; scope of the reset UNCONFIRMED (G TODO at `scd.c:1869`) | What RES0 resets | Y | N | Y | N |
| COM-61 | Version field | LC | partial | MD `lib/sub/gate_arr.def.h:29,41-42,64-71`; P `pico/cd/memory.c:330` ("ver = 0") | MD, emulator | Cond: ESTIMATED | Values per model | Y | N | Y | N |
| COM-62 | Sub register A1-A8 decode/mirror | LC | partial | G `core/cd_hw/scd.c:550-551,667-668` | single emulator | Cond: CONFIRMED (scope: emulator) | Hardware | Y | N | Y | N |
| COM-63 [X-01] | Sub BIOS sets Word RAM mode at init | LB | partial | CB `src/sub/main.asm:32-38` | CB | Cond: see COM-52 | as COM-52 | Y | N | Y | N (covered by COM-52) |
| COM-64 | Mask `$FF8033` bits 1-6 | LA | Y | G `core/cd_hw/scd.c:1115-1129,1482-1499`; P `pico/cd/memory.c:463-475`; C `source/bus-sub-m68k.c:1224-1233`; MD `lib/sub/gate_arr.def.h:401-419`; CB `src/sub/main.asm:30,56` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-65 | Highest pending level, autovector | LA | Y | G `core/m68k/s68kcpu.c:31-42,207-216`, `core/cd_hw/scd.c:2370-2390`; S-M68K §6.3 (autovectored interrupts) | emulator + CPU official | Y: CONFIRMED (derived from S-M68K priority rules) | Whether the gate array asserts /VPA for every level on hardware | Y | Y | Y | N |
| COM-66 | Pending latch while masked | LC | partial | G: L1/L2/L3/L6 set pending only if enabled (`core/cd_hw/gfx.c:727-735`, `core/mem68k.c:1153`, `core/cd_hw/scd.c:1978-1986`, `core/cd_hw/cdd.c:1771-1778`), L4 always latched (`scd.c:1953-1965`); P raises L4 on unmask (`pico/cd/memory.c:466-471`) | emulators | N: emulators **conflict** and neither cites hardware. UNCONFIRMED | Per-level latch behaviour | Y | N | Y | **Y (LC)**: affects game and BIOS interrupt paths; no reliable source |
| COM-67 | Ack clears pending; L2 ack clears IFL2 | LB | Y | G `core/cd_hw/scd.c:2376-2389`; C `source/bus-sub-m68k.c:387-391` | emulators | Y: CONFIRMED (scope: emulator) | Hardware | Y | Y | Y | N |
| COM-68 | IEN1 off discards pending L1 | LC | partial | G `core/cd_hw/scd.c:1123-1124,1493-1494` ("Batman Returns"); C `source/bus-sub-m68k.c:1232-1233` | emulators | Cond: two emulators agree. ESTIMATED | Hardware | Y | N | Y | N |
| COM-69 | L1 graphics done | LC | Y | G `core/cd_hw/gfx.c:727-735`; C `source/bus-sub-m68k.c:1324-1326`; MD `lib/sub/memmap.def.h:73` | as above | Y: CONFIRMED (scope: emulator) | none | Y | Y | Y | N |
| COM-70 | L2 from Main | LB | Y | see COM-11; MD `lib/sub/memmap.def.h:74`; CB `src/sub/header.asm:50` | as above | Y | none | Y | Y | Y | N |
| COM-71 | L3 timer period | LB | Y | G: period n×384 Sub cycles (`core/cd_hw/scd.c:1098-1113,1463-1480,1968-1988`); P: (n+1)×384, "mcd-verificator results suggest d+1" (`pico/cd/memory.c:453-462`, `pico/cd/mcd.c:207-217`); C: (n+1) (`source/bus-sub-m68k.c:1215-1219`); memory-map.md cites S-HW as (n+1) (excluded) | emulators + L-VERIF hint | Cond: two of three emulators plus a hardware-test hint say (n+1); G differs. ESTIMATED | Hardware period measurement | Y | N | Y | N (BIOS does not depend on it; games may) |
| COM-72 | L4 CDD 75 Hz gated by `$FF8037` bit 2 | LB | Y | G `core/cd_hw/scd.c:1541-1546,1943-1966`; P `pico/cd/memory.c:479-491`, `pico/cd/mcd.c:197-200`; MD `lib/sub/memmap.def.h:76` | as above | Y: CONFIRMED (scope: emulator); rate ESTIMATED | Phase relative to the CDD frame | Y | Y | Y | N |
| COM-73 | L5 CDC /INT falling edge | LB | Y | G `core/cd_hw/cdc.c:306-313`; MD `lib/sub/memmap.def.h:77` | as above | Y: ESTIMATED (CDC details belong to the CD area) | CDC chip interrupt conditions | Y | Y | Y | N |
| COM-74 | L6 subcode | LC | Y | G `core/cd_hw/cdd.c:1771-1778`; MD `lib/sub/memmap.def.h:78` | as above | Y: ESTIMATED | none | Y | Y | Y | N |
| COM-75 | L7, spurious and unused vector safety | LA | Y | S-M68K Table 6-2; CB `src/sub/header.asm:35-55` | CPU official, CB | Y | none | Y | Y | N | N |
| COM-76 | Sub RAM jump table `$5F40-$5FFF` | LB | Y | MD `lib/sub/memmap.def.h:64-95`, `docs/megacd_dev.md:13`; CB `src/sub/header.asm:24-72` (`_LEVELn` symbols) | MD (partly RE), CB | Cond: two non-excluded sources; exact slots ESTIMATED | Official slot list (only in excluded S-BIOS §1-4) | Y | Y (LB with a MegaDev SP) | Y | N (LB: MegaDev defines it; the LC risk is tracked in COM-32) |
| COM-77 | Sub IRQ latency | LC | N | Not found in the sources examined | n/a | N | Cycle timing | Y | N | Y | N |
| COM-78 | VDP V-INT L6, H-INT L4 | LA | Y | S-M68K Table 6-2; G `core/system.c:486,514`; MD `lib/main/memmap.def.h:69-74` | CPU official, emulator, MD | Y: standard Mega Drive (R-14) | none | Y | Y | Y | N |
| COM-79 [X-03] | Main RAM jump table `$FFFD00` | LB | Y | MD `lib/main/memmap.def.h:69-97`, `docs/megacd_dev.md:7-17,85`; CB `include/mcd_main.inc:83-100` (JMP at `$FFFD06`/`$FFFD0C`/`$FFFD12`; operands at +2 match MD's `$FFFD08`/`$FFFD0E`/`$FFFD14`) | MD (RE), CB | Cond: two sources agree on slots (possibly not independent). ESTIMATED (R-15) | Official statement (none in non-excluded sources) | Y | Y | Y | N (LB) |
| COM-80 | No Sub→Main IRQ; Main L2 = external only | LB | partial | Not found in the sources examined. G Main IRQ call sites are VDP and lightgun only (`core/system.c:486,514,661,839,867,1002`, `core/input_hw/lightgun.c:135`); MD `docs/megacd_dev.md:11` | emulator, MD | Cond: inferred from absence in emulators. UNCONFIRMED (hardware) | Whether the gate array can drive Main /IPL | Y | N | Y | N |
| COM-81 [X-02] | CPU state at IP entry | LB | partial | CB `src/main/main.asm:99-102` (all registers zeroed, SR `$2700`); MD `docs/megacd_dev.md:21,29,89` (stack, self-inconsistent, OQ-2) | CB, MD | Cond: conflicting or underspecified | SR, SP and VDP state the original leaves | Y | N | Y | N (LB homebrew sets its own state; LC risk via COM-36) |
| COM-82 [X-08] | Default Main handler side effects games rely on | LC | partial | MD `docs/main_bios.md:224-238,388-416` (RE); CB `src/main/interrupt.asm:21-137` | MD (RE), CB | N: only RE plus one reimplementation | Original handler side effects (flags, counters, IFL2 timing) | Y | N | Y | **Y (LC)**: shares a root with COM-35 |
| COM-83 | 12.5 MHz Sub clock, 384-cycle timer base | LB | Y | G `core/cd_hw/scd.h:60,67`, `core/cd_hw/scd.c:1943`; P `pico/cd/mcd.c:82` (12500000/75); MD `lib/sub/gate_arr.def.h:252` | as above | Y: ESTIMATED | Crystal tolerance (real clocks drift) | Y | N | Y | N |
| COM-84 | Reset-release → first Sub instruction latency | LA | partial | P `pico/cd/memory.c:200-201` (+40 cycles); G immediate (`core/mem68k.c:1059-1062`) | emulators | Cond: ESTIMATED | Real latency (BIOS should poll a flag, not assume a delay) | Y | N | Y | N |
| COM-85 | Polling races | LC | partial | P `pico/cd/memory.c:79-84,264-270`; G `core/mem68k.c:399-400,581-582`, `core/cd_hw/scd.c:732-733` (sync fixes for named games) | emulators | N: emulator workarounds only | Real-hardware timing | Y | N | Y | N (hardware, not BIOS) |
| COM-86 [X-11] | Gate-array forced reset/init at boot | LA | partial | S-HW §4-1 p.56 (excluded); CB performs none (`src/main/main.asm:21-102`) | excluded / CB | Cond: CB shows it is unnecessary **in ClownMDEmu only**; no non-excluded hardware statement | Whether real hardware needs it (OQ-10) | Y | N | **Y** | **Y (LA on real hardware)**: unknown until measured |
| COM-87 | Gfx unit idle at SP entry | LC | partial | G `core/cd_hw/scd.c:1559-1566`, `core/cd_hw/gfx.c:604-735`; MD `lib/sub/gate_arr.def.h:527-617` | emulator, MD | Y: BIOS never writes `$FF8066` (design) | none | Y | Y | Y | N |
| COM-88 | Font/1bpp registers | LC | Y | G `core/cd_hw/scd.c:606-628`; P `pico/cd/memory.c:310-318,357-368`; CB `include/mcd_sub.inc:120-122` | as above | Y: ESTIMATED (G and P encode it differently; equivalence to be checked) | none for the BIOS | Y | Y | Y | N |
| COM-89 | Stamp, rotation and scaling semantics | LC | Y | G `core/cd_hw/gfx.c:302-735`; C `source/bus-sub-m68k.c:1272-1326` (priority TODO at 1306); MD `lib/sub/gate_arr.def.h:527-617` | as above | Cond: hardware feature, not BIOS. ESTIMATED | Edge cases (C does not implement priority) | Y | N | Y | N (not BIOS) |
| API-01 | Sub jump table `$5F00-$5FFF`, 6-byte JMP slots | LB | Y | MD `lib/sub/bios.def.h:92-127`, `lib/sub/memmap.def.h:64-95`. MB `src/sub/call_table.asm:35-59`. CL `source/bus-sub-m68k.c:712,882` (traps at PC `$5F16`/`$5F22`) | MD P-OFF/P-RE (MIT). MB P-UNK (0BSD). CL P-BB (AGPL, cite only) | Cond: 3 public sources agree; origin P-OFF/P-RE; re-derive via E1 | Use of `$5F00-$5F09` | Y | Y (E1) | N (E2 to confirm) | N |
| API-02 | `_SETJMPTBL` module parsing/installation | LB | Y | MD `lib/sub/bios.def.h:68-92`, `lib/sub/sp_header.s:9-25`. MB `src/sub/module.asm:16-78` | MD text is disassembly-style ("it looks like ...") = P-RE. MB P-UNK | Cond: header shape also recoverable from homebrew SP headers (P-USE) | Accepted name strings (MD lists 4); meaning of version/type fields | Y | Y | N | N |
| API-03 | `_WAITVSYNC` waits for INT2 | LB | Y | MD `lib/sub/bios.def.h:94-97`; used `lib/sub/cdrom.s:42`. MB `src/sub/variables.inc:26` | P-OFF + P-USE | Cond: simple, black-box testable | Behaviour without INT2; preserved registers | Y | Y | N | N |
| API-04 | `_BURAM` dispatcher | LB | Y | MD `lib/sub/bram.def.h:11-15`. CL `source/bus-sub-m68k.c:712-881` | P-OFF (MD), P-BB (CL) | Cond | - | Y | Y | N | N |
| API-05 [X-18] | `_CDBOOT` dispatcher | LC | partial | MD `lib/sub/cdboot.def.h:11-15` | P-OFF | Cond: address only | Whether commercial titles call it: not found in the sources examined | Y | partial (no HLE in CL) | Y (E2) | N |
| API-06 [X-04] | `_CDBIOS` dispatcher, `D0.w` code | LB | Y | MD `lib/sub/bios.def.h:123-127`, `lib/sub/sub.macro.s:32-34` (`BIOSCALL` macro). CL `source/bus-sub-m68k.c:64-71,882-888` | P-OFF/P-RE (MD), P-BB (CL) | Cond | Effect of a non-zero high word in `D0` | Y | Y | N | N |
| API-07 [X-12] | USERCALL0-3 from the SP header | LB | Y | MD `lib/sub/bios.def.h:99-121`, `docs/boot.md:17-26`, `lib/sub/sp_header.s:20-25`. MB `src/sub/main.asm:58-69` | MD cites "Sections 4 and 5 of the BIOS Manual" = P-OFF. MB P-UNK | Cond | Terminator rule of the offset list; modules with fewer than 4 entries | Y | Y | N | N |
| API-08 | Sub exception slots `$5F40-$5FFF`, order and defaults | LB | Y | MD `lib/sub/memmap.def.h:64-95`. MB `src/sub/call_table.asm:35-59` | P-OFF/P-RE (MD), P-UNK (MB) | Cond: order agreed by 2 sources; defaults are a design choice | Original default handler behaviour | Y | Y | Y (E6) | N |
| API-09 | Sub hardware vectors point into the slots | LB | partial | MD `docs/megacd_dev.md:9-17` | P-RE | Y: follows by design from API-08 | - | Y | Y | N | N |
| API-10 [X-04] | Register convention, clobbers, carry | LB | Y | MD `@clobber`/`@param` tags, `lib/sub/bios.def.h:143-720`, `lib/sub/bram.def.h:17-187`. CL carry handling `source/bus-sub-m68k.c:146-149,216-223,745-870` | P-OFF/P-RE. MD notes a mismatch between the "documentation" and the disassembly (`bios.def.h:386-388`) | Cond: confirm by E2 register-diff | Exact clobber set for each call; meaning of N/Z/V | Y | partial | Y (E2) | N |
| API-11 | Calls legal from interrupt or USERCALL2 context | LB | N | Not found in the sources examined (MD, CL, MB, M1, E-GPGX-F, E-PICO) | Excl. (S-BIOS §5-3/5-4, TOC pp.33-35) | N | Reentrancy rules | partial | partial | Y | N for LB (homebrew calls from USERCALL1). Robustness risk for LC |
| API-12 | Level-2 handler: BIOS work, `INT2FLAG`, USERCALL2 | LB | partial | MD `lib/sub/bios.def.h:52-55`. MB `src/sub/interrupt.asm` (own design) | P-OFF/P-UNK | Cond | Ordering; `INT2FLAG` value convention | Y | Y | Y (E2) | N |
| API-13 | BIOS handles level 4/5 (CDD/CDC) | LB | partial | MB `src/sub/main.asm:56`. E-GPGX-F `core/cd_hw/cdd.c:1956` ("BIOS hangs otherwise") | P-UNK; emulator comment (cite only) | Cond: the CDD protocol is a memory-map/CDD item (OQ-11) | How CDD status reaches `CDSTAT` | partial | partial | Y | N |
| API-14 [X-12] | Sub boot sequence, USERCALL0/1 loop | LB | partial | MD `docs/boot.md:17-26`. MB `src/sub/main.asm:21-72` | P-OFF (manual §4-5), P-UNK | Cond | USERCALL1 return-code semantics; BIOS work between iterations | Y | Y | Y (E2) | N |
| API-15 [X-14] | Stack and CPU mode at user entry | LB | partial | MD `lib/sub/bios.def.h:57-60`. MB `src/sub/variables.inc:23-24` (stack `$5D80-$5E80`) | P-OFF/P-UNK | Cond | Encoding of `USERMODE`; original stack top | Y | partial | Y (E2) | N |
| API-16 [X-05] | `CDSTAT`/`BOOTSTAT`/`INT2FLAG`/`USERMODE` addresses | LB | Y | MD `lib/sub/bios.def.h:47-66`; used `examples/hello_world/src/sp.s:17-20`. CL uses a different status address and says "Find the address that a real BIOS uses" (`source/bus-sub-m68k.c:153-171`) | P-OFF + P-USE; CL P-BB | Cond | Full `BOOTSTAT` encoding | Y | Y | N | N |
| API-17 | `$0000-$5FFF` reserved, user from `$6000` | LB | Y | MD `docs/boot.md:3`, `docs/megacd_dev.md:123`. MB `src/sub/main.asm:42-50`. CL `source/clownmdemu.c:498,527` | P-OFF/P-UNK/P-BB, consistent | Y: implied by every SP | - | Y | Y | N | N |
| API-18 | Unknown codes return safely | LB | partial | CL `source/bus-sub-m68k.c:326-328,875-880` | P-BB | Y: design choice | What the original does | Y | Y | N | N |
| API-20 | `DRV_INIT` | LB | Y | MD `lib/sub/bios.def.h:215-228`; used `new_project/src/sp.s:40-47`, `examples/hello_world/src/sp.s:17` | P-OFF/P-RE + P-USE | Cond | Completion signalling; auto-play behaviour | Y | partial (CL has no `$10` HLE) | Y (E5) | N |
| API-21 | `DRV_OPEN` | LC | partial | MD `lib/sub/bios.def.h:207-213` | P-OFF | Cond | Status and timing while the tray is open | Y | N | Y | N |
| API-22 | `CDBCHK` | LB | Y | MD `lib/sub/bios.def.h:367-376`. CL `source/bus-sub-m68k.c:146-149` | P-OFF/P-BB | Cond | - | Y | Y | N | N |
| API-23 [X-05] | `CDBSTAT` status structure | LB/LC | partial | MD `lib/sub/bios.def.h:378-390` (pointer only). CL placeholder `source/bus-sub-m68k.c:151-172`. Nibble polling `new_project/src/sp.s:46-47` | P-OFF. CL fields are guesses (P-BB, "placeholder which is enough to get Popful Mail to boot") | Cond for LB (only "upper nibble 0 = idle" is needed). **N for LC**: no field-level non-excluded spec | Every field, status codes, update timing | Y | partial | Y (E2/E5) | **Y (LC)**: games read the fields; CL needed a game-specific placeholder |
| API-24 | `CDBTOCWRITE` | LC | partial | MD `lib/sub/bios.def.h:392-406` (refers to "the BIOS manual") | P-OFF | Cond | Entry count, terminator | Y | N | Y | N |
| API-25 | `CDBTOCREAD` | LC | Y | MD `lib/sub/bios.def.h:408-420`. CL incomplete `source/bus-sub-m68k.c:174-179` | P-OFF/P-BB | Cond | Error path for an invalid track | Y | partial | Y | N |
| API-26 | `CDBPAUSE` | LC | Y | MD `lib/sub/bios.def.h:422-434` | P-OFF | Cond | Default delay; actual drive effect | partial | N | Y. **Never test `$FFFF`**: MD warns it can damage the drive | N |
| API-27 | `MSC_STOP` | LC | Y | MD `lib/sub/bios.def.h:143-149`. CL `source/bus-sub-m68k.c:73-80` (implemented as pause, TODO) | P-OFF/P-BB | Cond | Observable difference between stop and pause | Y | partial | Y | N |
| API-28 | `MSC_PAUSEON/OFF` | LC | Y | MD `lib/sub/bios.def.h:159-165`. CL `source/bus-sub-m68k.c:77-85` | P-OFF/P-BB | Cond | - | Y | Y | N | N |
| API-29 | `MSC_SCANFF/FR/OFF` | LC | partial | MD `lib/sub/bios.def.h:167-189` | P-OFF | Cond | Scan speed and how scanning ends | Y | N | Y | N |
| API-30 [X-17] | `MSC_PLAY/PLAY1/PLAYR` | LC | Y | MD `lib/sub/bios.def.h:244-272`. CL `source/bus-sub-m68k.c:87-101` (all/once/repeat). Contradiction: MD also names `$11/$12` UNKNOWN (`:230-242`, OQ-12) | P-OFF/P-BB | Cond: CL behaviour plus the E1 census resolves OQ-12 without P-OFF | "Play all" across track ends; status during play | Y | Y | Y (audio timing) | N |
| API-31 | `MSC_PLAYT/SEEK/SEEKT/SEEK1` | LC | partial | MD `lib/sub/bios.def.h:274-334` | P-OFF | Cond | Seek accuracy; status after seek | Y | N | Y | N |
| API-32 [X-04] | `ROM_READ/SEEK/READN/READE` | LB/LC | Y | MD `lib/sub/bios.def.h:306-365`; used `lib/sub/cdrom.s:300-316,408-424`. CL `source/bus-sub-m68k.c:103-144` (open TODOs at `:128`, `:140`) | P-OFF/P-RE + P-USE + P-BB | Cond | Count 0; reversed range; interaction with `CDC_START` | Y | Y | Y (timing) | N |
| API-33 | `ROM_PAUSEON/OFF` | LC | partial | MD `lib/sub/bios.def.h:191-205` | P-OFF | Cond | - | Y | N | Y | N |
| API-34 [X-17] | Undocumented/contested codes | LC | partial | MD `lib/sub/bios.def.h:129-142,230-242`. CL default branch `source/bus-sub-m68k.c:326-328` | P-RE (listed as "present in jump table") | N: semantics unknown in all sources examined | Purpose of `$00`, `$01`, `$0B-$0F`, `$1A-$1F` | Y (E1 shows whether anyone calls them) | partial | Y | N unless E1 finds callers |
| API-35 | `FDR_SET/FDR_CHG` | LC | Y | MD `lib/sub/bios.def.h:436-454`. CL `source/bus-sub-m68k.c:181-204` | P-OFF/P-BB | Cond | Volume scale; ramp units | Y | Y | Y (analogue level) | N |
| API-36 | `CDC_START/STARTP/STOP` | LB | Y | MD `lib/sub/bios.def.h:456-484`. CL `source/bus-sub-m68k.c:206-214` | P-OFF/P-BB. `STARTP` has "No official documentation" | Cond (`STARTP`: N) | Semantics of `STARTP` | Y | Y | N | N |
| API-37 [X-04] | `CDC_STAT/CDCREAD/CDC_TRN/CDC_ACK` | LB | Y | MD `lib/sub/bios.def.h:486-539`; used `lib/sub/cdrom.s:315-366`. CL `source/bus-sub-m68k.c:216-324` | P-OFF/P-RE + P-USE + P-BB | Cond: well cross-checked by HLE running homebrew and games | Exact `D0` packing; behaviour with no sector | Y | Y | N | N |
| API-38 | `CDCSETMODE` | LC | partial | MD `lib/sub/bios.def.h:661-704` (clobbers "UNKNOWN") | P-OFF | Cond | Clobbers; effect on later reads | Y | N | Y | N |
| API-39 | Subcode `$8E-$94` | LC | partial | MD `lib/sub/bios.def.h:541-626` | P-OFF | Cond | `0x750` work-area layout; error counters | Y | N | Y (disc with subcode) | N |
| API-40 | `LEDSET` | LB/LC | Y | MD `lib/sub/bios.def.h:628-659`; used `new_project/src/sp.s:108-109` | P-OFF + P-USE | Cond | Code for "return control to BIOS" (MD shows `?`) | partial | N (no LED in emulators) | Y | N |
| API-41 | `WONDERREQ/WONDERCHK` | LC | N | MD `lib/sub/bios.def.h:706-720` (names only) | P-RE | N | Everything | N | N | Y (Wondermega) | N (niche) |
| API-42 | Asynchronous command model | LB | partial | MD `lib/sub/cdboot.def.h:24-31` (16.6 ms tick); polling `new_project/src/sp.s:44-47` | P-OFF + P-USE | Cond for LB; N for LC detail | State-transition table; queued vs immediate commands | Y | partial | Y (E5) | N for LB (it feeds the API-23 LC blocker) |
| API-43 | Error/return codes | LB | partial | Carry semantics from MD tags. CL `source/bus-sub-m68k.c:745-870` | P-OFF/P-BB | Cond | Numeric codes; no-disc paths | Y | partial | Y | N |
| API-44 | CDC pre-seek 2-4 sectors | LC | Y | MD `lib/sub/bios.def.h:462-465` | P-OFF/P-RE | Cond | Range per model | Y | N | Y | N |
| API-45 [X-19] | Timing characteristics | LC | partial | E-GPGX-F `core/cd_hw/cdd.c:630` (data track at least 2 s, "BIOS requirement"), `:1956`. CL `TODO.md:101-102` (sector timing unimplemented) | Emulator comments (non-commercial, cite only) | N: no measured public spec | Latencies, ticks per command, seek times | partial | N | **Y** | **Y (LC)**: timing-sensitive titles cannot be validated without measurement (E5) |
| API-46 | Sector header/mode handling | LB | partial | MD `lib/sub/bios.def.h:497-513`. CL `source/bus-sub-m68k.c:225-293` | P-OFF/P-BB | Cond | Mode-2 form handling | Y | Y | N | N |
| API-50 | `BRMINIT` | LB/LC | Y | MD `lib/sub/bram.def.h:17-35`, wrapper `lib/sub/bram.h:60-104`. CL `source/bus-sub-m68k.c:720-728` | P-OFF/P-BB | Cond | Display strings; "other format" detection | Y | Y | Y (E3) | N |
| API-51 | `BRMSTAT` | LC | Y | MD `lib/sub/bram.def.h:37-47`. CL `source/bus-sub-m68k.c:730-737` (fixed fake values) | P-OFF/P-BB | Cond | - | Y | partial | Y (E3) | N |
| API-52 | `BRMSERCH` | LC | Y | MD `lib/sub/bram.def.h:49-66`. CL `source/bus-sub-m68k.c:739-760` | P-OFF/P-BB | Cond | Meaning of returned `A0` | Y | partial | Y (E3) | N |
| API-53 | `BRMREAD` | LB/LC | Y | MD `lib/sub/bram.def.h:68-86`. CL `source/bus-sub-m68k.c:762-790` | P-OFF/P-BB | Cond | Protect-mode decoding | Y | partial | Y (E3) | N |
| API-54 | `BRMWRITE` | LB/LC | Y | MD `lib/sub/bram.def.h:88-114` (`D1=0` per Tech Bulletin #1). CL `source/bus-sub-m68k.c:792-816` | P-OFF/P-BB | Cond | Overwrite vs. new file; out-of-space handling | Y | partial | Y (E3) | N |
| API-55 | `BRMDEL` | LC | Y | MD `lib/sub/bram.def.h:116-125`. CL `source/bus-sub-m68k.c:818-824` | P-OFF/P-BB | Cond | Compaction | Y | partial | Y | N |
| API-56 | `BRMFORMAT` | LC | Y | MD `lib/sub/bram.def.h:127-137`. CL no-op `source/bus-sub-m68k.c:826-830` | P-OFF | Cond (depends on API-60) | Format image | Y | N | Y (E3) | via API-60 |
| API-57 | `BRMDIR` | LC | Y | MD `lib/sub/bram.def.h:139-165`. CL unimplemented `source/bus-sub-m68k.c:832-836` | P-OFF | Cond | Paging edge cases | Y | N | Y (E3) | N |
| API-58 | `BRMVERIFY` | LC | Y | MD `lib/sub/bram.def.h:167-187` (lists `A0` twice, typo). CL `source/bus-sub-m68k.c:838-873` | P-OFF/P-BB | Cond | Error-number values | Y | partial | Y | N |
| API-59 | BRAM codes `$09/$0A` | LC | N | MD `lib/sub/bram.def.h:189-190` (names only) | P-RE | N | Everything | Y (E1) | N | Y | N unless E1 finds callers |
| API-60 [X-07] | On-media BRAM format and protect encoding | LC | partial | E-GPGX-F `libretro/libretro.c:131-137,1137-1148` and E-PICO `pico/cd/misc.c:11-24`, `pico/cd/mcd.c:62-68`: a 64-byte formatted-trailer template with size fields and an ASCII medium signature. No directory or protect spec found | Emulator data tables (non-commercial, cite only); origin unstated, presumably copied from a formatted real BRAM. Excl. S-BIOS §7 pp.38-45 | **N**: no non-excluded spec of directory entries, allocation or protect encoding | Directory entry format, allocation order, protect encoding, any checksum | Y (E3) | N | **Y** | **Y (LC)**: saves must interoperate with real consoles, RAM carts and `.brm` files |
| API-61 | File-name rules | LC | partial | MD `lib/sub/bram.def.h:64`. CL `source/bus-sub-m68k.c:555-565` (cites "Sega's developer documentation": 0-9, A-Z, `_`) | P-OFF | Cond | Lower case; padding | Y | Y | Y | N |
| API-62 | RAM-cartridge BRAM | LC | partial | MD `lib/main/bramcart.def.h`. E-GPGX-F `libretro/libretro.c:1185-1195` | P-OFF/emulator | Cond | Detection and size encoding | Y | partial | Y (needs a cart) | N |
| API-63 | BRAM display strings, "other format" | LC | N | CL `source/bus-sub-m68k.c:726-727` ("I have no idea") | - | N | Content and purpose | Y | N | Y | N |
| API-65 [X-18] | `_CDBOOT` `$00-$05` | LC | Y | MD `lib/sub/cdboot.def.h:17-93` | P-OFF | Cond | Who uses it | Y | N | Y | N |
| API-66 [X-18] | `_CDBOOT` `$06-$09` | LC | N | MD `lib/sub/cdboot.def.h:95-125` ("No official documentation") | P-RE | N | Everything | Y (E1) | N | Y | N |
| API-70 [X-16] | Boot header: IP to `$FF0000`, SP to `$6000` | LB | Y | CL `source/clownmdemu.c:494-531` (IP/SP offset and length from header words `$18/$1A/$20/$22`; default IP `$200`/`$600`). MD `docs/boot.md:3,13`. MB `src/sub/main.asm:58-60` | P-BB: CL boots commercial discs without a Sega ROM | **Y**: working black-box loader. Field layout is shared with disc format (Area B) | IP size limit; whether IP length > `$600` is honoured (CL does; unverified) | Y | Y | N (E2 optional) | N |
| API-71 [X-06] | Security/region check | LB | partial | [open-questions.md](open-questions.md) OQ-8 | policy | Cond on a legal decision | - | Y | Y | N | **Y (LB policy)**: OQ-8 unresolved |
| API-72 [X-01] | Word RAM mode/owner at hand-off | LB | partial | CL `source/clownmdemu.c:529-531` (2M, given to Sub). MB `src/sub/main.asm:32-38` (Sub BIOS init sets 1M and returns it to Main) | P-BB / P-UNK. **Apparent disagreement** (may be different phases) | Cond | State observed by IP and SP | Y | Y | Y (E2) | N |
| API-73 [X-02] | Main CPU state at IP entry | LB | partial | MD `docs/megacd_dev.md:21,29,89` (self-contradictory, OQ-2); `docs/main_bios.md:56-58` (Tech Bulletin #3: stack `$FFFD00`) | P-OFF/P-RE | Cond | SP, SR, registers | Y | partial | Y | N |
| API-74 | IFL2 raised each Main V-INT | LB | Y | MD `docs/main_bios.md:388-394,688-698,740-742`. MB `src/main/function_table.asm:85` | P-RE/P-UNK; P-USE in homebrew | Cond | Whether the default V-INT raises IFL2 before the IP patches it | Y | Y | N | N |
| API-75 | Comm registers cleared at boot | LB | Y | MB `src/sub/main.asm:22-27`. M1 `src/mode_1/mcd_mode_1.asm:39` | P-UNK, 0BSD | Y | - | Y | Y | N | N |
| API-76 [X-13] | Mode-1 signatures, compressed Sub BIOS | LC | Y | M1 `src/mode_1/mcd_mode_1.asm:115-178`. MB `README.md:17-23`. MD `lib/main/bios.def.h:1387-1402`. E-PICO `pico/cd/memory.c:1220-1223` (MSU-MD checks `"SEGA"` at `$400100`) | P-USE (callers state the contract). The offsets were learned from real ROMs (P-RE/P-OFF, Tech Bulletin #3) | Cond: public interoperability facts. **Trademark question** about embedding `"SEGA"` (OQ-5 family) | Callers need a particular Kosinski encoder for detection (MB README); is the `"WONDER"` variant required? | Y | Y | Y (MSU-MD class on hardware) | N (design constraint) |
| API-77 [X-13] | Mode-1 Sub BIOS self-start with cart SP | LC | Y | M1 `src/mode_1/mcd_mode_1.asm:32-105` | P-USE (0BSD) | Y: caller contract is public | - | Y | Y | Y | N |
| API-80 [X-03] | Main vectors to `$FFFD00` slots, order | LB | Y | MD `lib/main/memmap.def.h:65-99`, `docs/megacd_dev.md:7-17`. MB `src/main/call_table.asm:21-50`. CL `source/mega-cd-boot-rom.c:1-15` (MB build) | P-RE (MD), P-UNK (MB). MD duplicate slot (OQ-12) | Cond: shape agreed by 2 sources; E6 resolves OQ-12 | Slot for illegal instruction vs address error | Y | Y | Y (E6) | N |
| API-81 [X-03] | Slot defaults; patch slot+2 | LB | Y | MD `docs/megacd_dev.md:17,31`, `docs/main_bios.md:61-63` (Tech Bulletin #3, "label value plus 2") | P-OFF/P-RE | Cond | - | Y | Y | N | N |
| API-82 [X-08] | `$280` table: existence, order, entry size | LC | Y | MD `lib/main/bios.def.h:451-1384`, `docs/main_bios.md:30-42`. MB `src/main/function_table.asm:16-102` (73 entries) | **P-RE only** (MD explicit); MB P-UNK. Tech Bulletin #3 names `MAINENT.I`/`ROM_UTIL.DOC` (not found) | **N under current policy** (OQ-7 forbids disassembly-derived tables), although technically fully described | Clean-room re-derivation of order and semantics | Y (E4) | partial | Y (E4) | **Y (LC)**: OQ-7 |
| API-83 [X-08] | `$280` system group | LC | partial | MD `lib/main/bios.def.h:451-481`, `docs/main_bios.md:373-383` (empty). MB `src/main/function_table.asm:21-24` | P-RE/P-UNK; **names disagree** (MD: entry/reset/init/init-SP; MB: soft/hard reset, control panel) | N (OQ-7) | Semantics | Y (E4) | partial | Y | Y (OQ-7) |
| API-84 | V-INT handler/wait/flags | LC | Y | MD `docs/main_bios.md:224-238,388-408`, `lib/main/bios.def.h:93,296-334`. MB `src/main/function_table.asm:25-26` ("not available in clownmdemu") | P-RE | N (OQ-7) | - | Y | Y | Y | Y (OQ-7) |
| API-85 | Input | LC | partial | MD `lib/main/bios.def.h:526-560`. MB `src/main/function_table.asm:28-29,65` | P-RE/P-UNK | N (OQ-7) | Repeat-delay semantics | Y | Y | Y | Y (OQ-7) |
| API-86 | VDP/DMA utilities, default registers, VRAM layout | LC | Y | MD `docs/main_bios.md:240-279,428-547`. MB `src/main/function_table.asm:30-46,99-100`, `src/main/vdp.asm` | P-RE/P-UNK | N (OQ-7) | Region-dependent defaults (MD "TODO: confirm") | Y | Y | Y | Y (OQ-7) |
| API-87 | Palette cache and fades | LC | Y | MD `docs/main_bios.md:287-293,579-595,650-666` | P-RE | N (OQ-7) | - | Y | Y | N | Y (OQ-7) |
| API-88 | Nemesis/Enigma decompression | LC | partial | MD `lib/main/bios.def.h:849-865,1084-1086`. MB `src/main/function_table.asm:49-50,66`, `src/main/decompress.asm` | P-RE. The formats themselves are community-documented (not examined, §5) | Cond: formats are public; entry semantics need OQ-7 | Use of the `$FFF700` buffer | Y | Y | N | Y (OQ-7) |
| API-89 | Sprite-object/entity system | LC | partial | MD `docs/main_bios.md:311-343` (incomplete, "unknown byte") | P-RE | N | Field meanings | Y | Y | N | Y (OQ-7) |
| API-90 | Built-in font and print | LC | Y | MD `docs/main_bios.md:349-357`. MB `src/main/splash.asm:19-29` (homebrew and hacks use the font/logo left in VRAM) | P-RE/P-UNK | Cond: supply **our own** font (as MB does). Tile-index placement (base 32) is an RE fact | Glyph mapping beyond ASCII | Y | Y | N | Y (OQ-7) |
| API-91 | PRNG | LC | partial | MD `docs/main_bios.md:345-347,749-759` (multiply-with-carry; constants not given) | P-RE | N | Exact algorithm (games may depend on the sequence) | Y | Y | N | Y (OQ-7) |
| API-92 [X-08] | Comm sync, Sub-BIOS proxy calls, comm-flag protocol | LC | partial | MD `docs/main_bios.md:359-368,684-742` ("still investigating"). MB stubs 8 such entries as "not available in clownmdemu" (`src/main/function_table.asm:71-83,91`) | P-RE, incomplete even within the RE community | **N**: unknown in all sources examined. Our Sub BIOS would also need the matching responder | Full two-CPU protocol | partial (E4) | N | **Y** | **Y (LC)**: MD says most retail users of `$280` use these (`docs/main_bios.md:363`) |
| API-93 | BCD/time arithmetic | LC | partial | MD `lib/main/bios.def.h:1300-1313,1378`. MB `src/main/function_table.asm:93-94,101-102` | P-RE/P-UNK | N (OQ-7) | Formats | Y | Y | N | Y (OQ-7) |
| API-94 [X-08] | Main work-area layout | LC | Y | MD `lib/main/bios.def.h:44-399`, `docs/main_bios.md:126-171`, `docs/megacd_dev.md:23-25`. MB `src/main/variables.inc` | P-OFF (Tech Bulletin #3 diagram) + P-RE | N (OQ-7) | Variation between revisions ("may vary by revision") | Y | Y | Y | Y (OQ-7) |
| API-95 | Residual VRAM/VDP/palette state at IP entry | LC | partial | MB `src/main/splash.asm:19-29` | P-UNK (observation of the original) | Cond: our own assets in the same places, confirmed by black-box screenshots | What exactly remains | Y | Y | Y | N |
| API-96 | Return to BIOS / control panel | LC | partial | MB `src/main/function_table.asm:21-24`. MD `lib/sub/bios.def.h:647` (LED "return control to BIOS") | P-UNK/P-OFF | Cond | Entry conditions | Y | Y | Y | N |
| API-98 | Model/region variants | LC | partial | MD `docs/main_bios.md:38` (`$280` fixed across models), `lib/main/bios.def.h:1393-1402` (Sub image offset varies). M1 signature list `src/mode_1/mcd_mode_1.asm:149-178` | P-RE/P-USE | Cond | Per-model extra calls (Wondermega, LaserActive) | partial | N | Y | N |
| API-99 | Region-dependent API behaviour | LC | N | MD `docs/main_bios.md:487` ("TODO: confirm that this is different per region") | P-RE | N | Everything | Y | N | Y | N |
| CD-001 | Cooked ISO fixture recognised by emulators | LB | Y | GX `core/cd_hw/cdd.c:584-643` (ISO accepted only if `SEGADISCSYSTEM` at byte 0; otherwise needs sync or CUE); PD `pico/media.c:220-229`, `pico/cd/cdd.c:337-349`; MD `megadev.make:236-241` (ISO = boot area via `mkisofs -G` + ISO 9660) | GX/PD cite only; MD MIT | **Y** (emulator scope): own generator. CONFIRMED (scope: emulator) | Whether IDs other than `SEGADISCSYSTEM` load at all in GX/PD (they do not autodetect them; CUE path untested) | Y (SynDisc) | Y | N | N |
| CD-002 | Raw BIN 2352 + CUE fixture | LB | Y | GX `cdd.c:604-615` (sync autodetect), `cdd.c:796-812` (CUE MODE1/2048, MODE1/2352, MODE2/2352); PD `pico/cd/cd_parse.c:330-336`; EC130 (sector layout) | GX/PD cite only; EC130 public | **Y**. CUE syntax has no free official spec (de-facto CDRWIN format), so define the fixture only from what both emulators parse | Formal CUE grammar (not found in sources examined: GX, PD, MD, EC130) | Y | Y | N | N |
| CD-003 | Mixed-mode CUE, audio pregaps | LC | Y | MD `docs/disc.md:25-45` (track 1 data, 2 s pregap "per the official documentation"); GX `cdd.c:864-910` (PREGAP/INDEX handling); PD `pico/cd/cd_parse.c:366-410` | MD MIT, but the 2 s rule is second-hand from XS; GX/PD cite only | **Cond**: the layout is clear. The "2 s pregap required" rule rests on an excluded doc and is ESTIMATED | Whether the BIOS or drive needs the pregap or it is only a seek-margin recommendation | Y (SynDisc with generated tones) | Y | Partial (seek-overrun audibility) | N |
| CD-004 | Correct sync/header/EDC/ECC for raw sectors | LB | Y | EC130 (sector structure, Mode 1 EDC/ECC); GX `cdd.c:1376-1395` (emulator skips sync+header and does not verify ECC) | EC130 public | **Y** (CONFIRMED: public standard) | None for the generator. Emulators will not catch EDC/ECC bugs | Y (generator unit test vs EC130) | N (emulators do not check) | Y (CD-R read by the stock drive) | N |
| CD-005 | Data track ≥ 150 sectors | LB | partial | GX `cdd.c:630-634` (pads to 150; comment calls it a "BIOS requirement") | GX cite only | **Cond**: an emulator comment only. ESTIMATED. As a fixture rule, just pad | Origin of the requirement (probably drive lead-in / pregap behaviour) | Y | Y (scope: emulator) | Y to confirm | N |
| CD-006 | `.sub` subcode side file | LC | Y | GX `cdd.c:1284-1285` (opens `<name>.sub`), `cdd.c:1738-1775` (96 B/sector, P-W interleaved, raises INT6); EC130 (subchannels) | GX cite only; EC130 public | **Y** for P/Q (EC130). R-W CD+G content format: see CD-106 | CD+G packet format (Red Book / IEC 60908 is paid; not found free) | Y | Y | N | N |
| CD-007 | Physical CD-R the stock drive reads | LB | N | none found | - | **Cond**: burn from the CD-004 image | Whether Model 1/2 drives read CD-R reliably; ATIP or dye limits. Not found in sources examined (GX, PD, CL, MD, EC130) | Y (SynDisc) | N | Y | N |
| CD-008 | Audio-only disc does not hang the BIOS | LA | partial | MD `lib/sub/cdboot.def.h:73-81` (disc types incl. "music"); GX `cdd.c:2100-2190` (TOC reports track type via RS6 bit 3 / RS8 bit 2) | MD MIT (RE caveat); GX cite only | **Y**: classify from the TOC data flag | None for "do not hang" | Y (SynDisc audio-only CUE) | Y | Partial | N |
| CD-009 | Negative fixtures | LB | N (our own design) | - | - | **Y**: our own spec | Expected behaviour of the original BIOS for each case (not needed for our own BIOS) | Y | Y | N | N |
| CD-010 | ISO 9660 in the data track | LB | Y | EC119 (PVD at LBA 16); MD `lib/sub/cdrom.s:217-243` (application code reads the PVD at sector `$10` itself, which implies the BIOS provides no file system) | EC119 public; MD MIT | **Y** | Whether any BIOS service parses ISO 9660 (MD suggests none; S-FMT "File System" pp.8–14 excluded) | Y | Y | N | N |
| CD-011 | LBA↔MSF (LBA 0 = 00:02:00, BCD) | LA | Y | EC130 (2 s offset, MSF in header and Q); GX `cdd.c:1813-1825` (header MSF = LBA+150, BCD), `cdd.c:1945-1948` (CDD command MSF → LBA−150) | EC130 public; GX cite only | **Y** (CONFIRMED: EC130 plus an emulator) | None | Y | Y | N | N |
| CD-020 | System ID recognition and bootability | LB | partial | MD `lib/cd_boot.s:16-27` (quotes I-RHOPE: four IDs; security check only for `SEGABOOTDISC`/`SEGADISCSYSTEM`; the other two "appear" non-bootable); `../rom-layout.md` B-09; XS S-FMT App. 2 pp.18–19 (lead) | MD MIT, but the text is a quote of I-RHOPE (no licence, TLS issue) | **Cond**: `SEGADISCSYSTEM` is safe (emulators require it). The semantics of the other IDs are ESTIMATED only | Exact accepted IDs, padding/case rules, meaning of `SEGADISC`/`SEGADATADISC` | Y (SynDisc per ID) | Partial (emulators ignore the ID beyond detection) | Y for parity with real discs | N for LB (choose `SEGADISCSYSTEM`); see OQ-9 |
| CD-021 | Volume/system fields `$10-$2F` | LC | partial | MD `lib/cd_boot.s:29-40` | MD MIT (RE caveat) | **Cond**: layout known, BIOS use unknown | Whether the BIOS reads them at all | Y | N | Y | N |
| CD-022 [X-16] | IP offset/size → IP load | LB | partial | MD `lib/cd_boot.s:42-56` (IP offset `$800`, size `$800`, plus a quoted "SOJ" note that the original BIOS assumes the IP starts in sector 0), `cfg/ip.ld:5-13` (IP ≤ `$E00`), `docs/boot.md:13-15` | MD MIT; the quotes are second-hand | **Cond**: our BIOS can define "load the IP from `$200` for N bytes per the fields". Exact original semantics are ESTIMATED | Exact interpretation of the offset/size fields in the original BIOS; whether the IP must start at `$200` | Y | Y (for our BIOS) | Y for parity | N for LB / Y for LC parity (see CD-027) |
| CD-023 [X-16] | SP offset/size → SP at `$6000` | LB | Y | MD `lib/cd_boot.s:57-60`, `docs/boot.md:3`; `../rom-layout.md` B-07/B-08 | MD MIT | **Cond** (ESTIMATED; B-07 placement CONFIRMED only via an excluded doc) | Max SP size; whether the BIOS write-protects after loading | Y | Y | Y for parity | N |
| CD-024 | Entry/work-RAM fields `$38/$3C/$48/$4C` | LC | partial | MD `lib/cd_boot.s:55-60` (always written 0) | MD MIT | **N**: semantics unknown | Meaning of non-zero values | Y (SynDisc variants) | N | Y | N |
| CD-025 | Disc header `$100-$1FF` checks | LC | partial | MD `lib/cd_boot.s:67-85` (hardware ID, copyright, names, serial, region `JUE` at `$1F0`); GX `cdd.c:1172-1200` (GX itself keys hard-coded TOCs on the serial at `$180`) | MD MIT; GX cite only | **Cond**: layout known; BIOS checks unknown | Which fields the BIOS validates (e.g. hardware ID string) | Y | N | Y | N |
| CD-026 | Boot-area extent read by the BIOS | LB | partial | MD `lib/cd_boot.s:98-104` (SP at `$1000`, boot area padded to `$8000` = 16 sectors) | MD MIT | **Cond**: our BIOS reads what the fields say. The original extent is ESTIMATED | Number of sectors the original reads; whether the SP can exceed the boot area | Y | Y | Y for parity | N |
| CD-027 | IP size limit / sector-1 quirk | LC | partial | MD `lib/cd_boot.s:42-50`, `docs/boot.md:13-15` | MD MIT (quotes) | **N** for exact parity | Exact rule; whether commercial discs depend on it | Y | N | Y | N |
| CD-028 | SP header format and usercall table | LB | Y | MD `lib/sub/sp_header.s:8-25`, `docs/boot.md:19-26`; `../bios-api.md` A-01/A-02 | MD MIT (RE caveat) | **Cond**: the usable spec is in MD; official §5-3 is excluded | Meaning of the flag/type/next-module fields; module chaining | Y | Y | Y for parity | N for LB (if MD is accepted, #17) |
| CD-029 | Disc-type classification | LC | partial | MD `lib/sub/cdboot.def.h:73-93` | MD MIT (RE caveat) | **Cond**: the codes are known; the classification rules are not | Rules mapping TOC + ID → type 0–7 | Y | N | Y | N |
| CD-030 | HOCK enable, INT4 per CDD frame | LA | Y | GX `core/cd_hw/scd.c:1541-1546` (only bit 2 writable), `scd.c:1943-1965` (75 Hz; INT4 only while bit 2 is set); MD `lib/sub/gate_arr.def.h:433`; `../memory-map.md` level 4 | GX cite only; MD MIT | **Cond**: the emulator model is consistent. Hardware rate is ESTIMATED. A NeoGeo-CD wiki note (<https://wiki.neogeodev.org/index.php/CD_drive_control>, different machine) mentions about 64 Hz rather than 75 for its CDD: an **unresolved conflict** | Real INT4 period and jitter; whether it is drive-timed | Y (Probe) | Y (scope: emulator) | Y | N (LA in emulator) / Y for real-HW LA |
| CD-031 [X-09] | Status frame layout | LA | Y | GX `cdd.c:2026-2078`, `cdd.c:2330-2335`; PD `pico/cd/cdd.c:855-1228` (derived); BE `cdd_mcu.h` (`status_format`, `drive_status` enums, `current_status_nibble`); MD `lib/sub/gate_arr.def.h:440-503` | GX/PD/BE cite only | **Cond**: GX and BE agree on the nibble frame; BE's independence from GX is unproven (only `cdd_mcu.h` enum names read). ESTIMATED (corrected during integration review) | Unused-nibble values on hardware; per-report RS8 flags | Y (Probe log) | Y | Y | N (emulator) |
| CD-032 | Command frame and send trigger | LA | Y | GX `scd.c:1548-1556` (write to `$FF804A` → `cdd_process`); BE `cdd_mcu.h` (`current_cmd_nibble`, `cmd_recv_pending`) | as above | **Cond** (ESTIMATED) | Whether hardware needs all nibbles written in order; word vs byte access | Y (Probe) | Y | Y | N |
| CD-033 | Checksum algorithm and bad-checksum reaction | LA | partial | GX `cdd.c:2330-2335` (status: low nibble of the inverted nibble sum); BE `cdd_mcu.h` (`checksum` fields); GX `cdd.h:63` defines "no valid checksum" status 6 but never uses it | GX/BE cite only | **Cond** for the algorithm. **N** for the drive reaction (GX does not verify command checksums) | Real drive response to a bad command checksum; whether the BIOS must verify the status checksum | Y (Probe sends a bad checksum; harmless) | N | Y | N (LA) / Y for LC robustness |
| CD-034 [X-09] | Status code set | LA | Y | GX `core/cd_hw/cdd.h:56-71`; BE `cdd_mcu.h` (`drive_status`: same order 0–E) | GX/BE cite only | **Cond**: GX and BE agree; BE's independence from GX is unproven. ESTIMATED (corrected during integration review) | When each error status (6/7/8, A, D, E) actually occurs | Y (Probe) | Partial | Y | N |
| CD-035 [X-09] | Command code set | LA | Y | GX `cdd.c:2024-2325` (0,1,2,3,4,6,7,8,9,A,C,D; others "unsupported"); BE `cdd_mcu.h` (`host_cmd`: NOP, STOP, REPORT_REQUEST, READ, SEEK, INVALID, PAUSE, PLAY, FFWD, RWD, TRACK_SKIP, TRACK_CUE, DOOR_CLOSE, DOOR_OPEN) | GX/BE cite only | **Cond**: the codes agree. Naming differs (GX "Play/Resume" = BE "READ/PLAY") | Semantics of `$5`/`$B`; exact difference between `$3` and `$7` | Y (Probe) | Y | Y | N |
| CD-036 | Report sub-codes 0–6 (incl. TOC) | LA | Y | GX `cdd.c:2100-2190` (abs/rel time, track no., total length, first/last, track start with RS6 bit 3 = data track, error info); BE `cdd_mcu.h` (`SF_*`: ABSOLUTE, RELATIVE, TRACK, TOCO, TOCT, TOCN, E); EC130 (Q-channel TOC content) | GX/BE cite only; EC130 public | **Cond** (ESTIMATED; the TOC concept is CONFIRMED by EC130) | Exact nibble placement on hardware for each report; lead-in vs lead-out flags | Y (Probe + SynDisc) | Y | Y | N |
| CD-037 [X-19] | Latency and seek timing | LB | partial | GX `cdd.c:1950-1976` (minimum 2 frames "or the BIOS hangs", +10/step option; linear seek of up to ~120 frames, explicitly "rough approximation"); GX `cdd.c:2028-2031` (games needing ≥ 2–3 "playing" reports) | GX cite only | **N** for hardware (game-tuned emulator constants) | Real command-to-status latency, seek-time curve, spin-up time | Y (Probe timing log) | N | Y | N for LB (a tolerant BIOS can poll) / Y for LC (see CD-107) |
| CD-038 | RS1 = `$F` invalid during seek | LB | Y | GX `cdd.c:2193-2222`, `cdd.c:2041-2052` | GX cite only | **Cond** (emulator; second-hand game evidence in comments) | Hardware confirmation | Y (Probe) | Y | Y | N |
| CD-039 | Power-on drive state and bring-up | LA | partial | GX `cdd.c:216-234` (reset: fader full, latency 0), `cdd.c:2080-2098` and `2276-2295` (stop/close → TOC-read or no-disc); MD `lib/sub/bios.def.h:213-228` (DRVOPEN/DRVINIT exist) | GX cite only; MD MIT | **Cond**: an emulator model only | Real status sequence after power-on (tray state, spin-up, automatic TOC read?) | Y (Probe cold boot) | N | Y | N (emulator) / Y real-HW LA |
| CD-040 | HOCK/CDCK nibble link pacing | LA | N | BE `cdd_mcu.h` (`cdd_hock_enabled/disabled`, cycle fields); gendev forum thread on HOCK/CDCK (<https://gendev.spritesmind.net/forum/viewtopic.php?p=21203>): not read in detail | BE cite only; forum (no licence) | **N**: not specified in non-excluded sources | Whether the gate array buffers the whole frame (pure register model) or software must time accesses | Y (Probe) | N | Y | N (all emulators use the register model) |
| CD-041 | `$FF8036` status bits | LC | partial | GX `cdd.c:1833-1930` (sets `$FF8036` high byte to 0/1 for audio playing) | GX cite only | **Cond** | Bit meanings and read behaviour on hardware | Y (Probe) | Partial | Y | N |
| CD-042 | Track jump `$A` | LC | partial | GX `cdd.c:2261-2274` (comment: parameter meaning unknown, refers to a Sony DSP datasheet and US patent 5,222,054) | GX cite only | **N** | Parameter semantics | Y (Probe) | N | Y | N |
| CD-043 | Codes `$5`/`$B`/`$E`/`$F` | LC | partial | BE `cdd_mcu.h` (`CMD_INVALID`=5, `CMD_TRACK_CUE`=B); GX `cdd.c:2318-2325` | BE/GX cite only | **N** | Behaviour | Y (Probe) | N | Y | N |
| CD-050 | Motorised tray open/close | LC | Y | GX `cdd.c:2276-2316` (`$C` close → TOC/no-disc; `$D` open → status 5); MD `lib/sub/bios.def.h:213`, `lib/sub/cdboot.def.h:33-57` | GX cite only; MD MIT | **Cond** | Tray-moving status duration; behaviour on top-loaders | Y (Probe, Model 1) | Partial | Y | N |
| CD-051 | Top-loader lid detection | LC | N | not found in sources examined (GX, PD, CL, BE, MD) | - | **N** | How a lid-open is reported (status code? timing?) | Y (Probe, Model 2) | N | Y | N |
| CD-052 | Insertion → TOC read | LA | partial | GX `cdd.c:2276-2295` (close → status 9 "TOC" when loaded) | GX cite only | **Cond** | Whether the drive reads the TOC on its own or needs a command | Y (Probe) | Y (scope: emulator) | Y | N |
| CD-053 | No-disc detection | LA | Y | GX `cdd.h:68` (status B), `cdd.c:2083`; BE `cdd_mcu.h` (`DS_NO_DISC`) | GX/BE cite only | **Cond** (GX and BE agree; BE's independence from GX is unproven) (corrected during integration review) | Time until no-disc is reported | Y (emulator with no disc; Probe) | Y | Y | N |
| CD-054 | Disc change while running | LC | N | not found in sources examined | - | **N** | Status sequence and required re-init | Y (Probe) | Partial | Y | N |
| CD-055 | Pause→standby timer | LC | partial | MD `lib/sub/bios.def.h:424-434` (CDBPAUSE sets the spin-down delay) | MD MIT (RE caveat) | **Cond**: the API exists; units unknown | Units and default; whether the drive or the BIOS implements it | Y | N | Y | N |
| CD-056 | Lead-out / end status | LC | partial | GX `cdd.c:1800-1804` (status C at end of disc); BE `DS_DISC_LEADOUT` | GX/BE cite only | **Cond** | Real behaviour at lead-out (auto-stop? loop?) | Y (SynDisc + Probe) | Y | Y | N |
| CD-057 | LEDs and LED modes | LC | partial | MD `lib/sub/gate_arr.def.h:29-44` (LEDR/LEDG at `$FF8000`), `lib/sub/bios.def.h:630-659` (LEDSET modes 0–7) | MD MIT | **Cond** | Blink patterns per mode | Y (Probe, visual) | N | Y | N |
| CD-060 [X-10] | CDC identity and register access | LB | Y | GX `core/cd_hw/cdc.c:3` ("LC8951x compatible"), `cdc.c:585-750` (writes), `cdc.c:760-870` (reads), `scd.c:1412-1434`; MD `lib/sub/gate_arr.def.h:163-205`; LCDM (whole document) | GX cite only; MD MIT; LCDM provenance unverified | **Cond**: the vendor design manual (if cleared) plus emulators give a full register-level spec | Clearance of LCDM; gate-array specifics (address auto-increment, which bits of `$FF8004`) are emulator-only | Y (Probe) | Y | Y | N |
| CD-061 | CDC reset and init | LB | Y | GX `cdc.c:743-750` (RESET reg `$F`), `cdc.c:75-90`; LCDM | as above | **Cond** | Required init order and values for this board (clock, buffer size config) | Y (Probe) | Y | Y | N |
| CD-062 | Decoder enable / mode | LB | Y | GX `cdc.c:56-64` (DECEN, AUTORQ, WRRQ, MODRQ, FORMRQ, SHDREN), `cdc.c:686-733`; MD `lib/sub/bios.def.h:663-704` (BIOS mode 0/1/2) | GX cite only; MD MIT | **Cond** | Error-correction modes and their effect on STAT flags | Y | Y | Y | N |
| CD-063 | Buffer write, WA/PT, 16 KiB ring | LB | Y | GX `cdc.h:61` (16 KiB plus overrun slack), `cdc.c:520-580` | GX cite only; LCDM | **Cond** | Buffer size on each model (16 KiB is ESTIMATED) | Y (Probe) | Y | Y | N |
| CD-064 | HEAD0-3 header check | LB | Y | GX `cdc.c:792-815`, `cdd.c:1813-1825`; EC130 | GX cite only; EC130 public | **Y** (header content is CONFIRMED by EC130; register access is Cond) | None for Mode 1 | Y | Y | N | N |
| CD-065 | STAT0-3 flags | LB | partial | GX `cdc.c:840-870` (STAT1 always 0; STAT3 VALST; comment that its handling is "not 100% correct but BIOS do not seem to care") | GX cite only; LCDM | **Cond** (LCDM) / emulator incomplete | Real error flags under bad reads; emulators never produce errors | Partial (needs damaged media) | N | Y | N (LB) |
| CD-066 | DECI → INT5 and acknowledge | LB | Y | GX `cdc.c:487-517`, `cdc.c:764-775`, `cdc.c:862-869`; `../memory-map.md` level 5 | GX cite only | **Cond** | Exact clear condition on hardware | Y (Probe) | Y | Y | N |
| CD-067 | DBC/DAC/DTRG/DTACK transfer | LB | Y | GX `cdc.c:631-676`, `cdc.c:255-325`; LCDM | GX cite only | **Cond** | DBC off-by-one and DBCH upper-bit behaviour (GX comment `cdc.c:283`) | Y (Probe) | Y | Y | N |
| CD-068 | Sub host read via `$FF8008` | LB | Y | GX `cdc.c:261-325` (DD=3; DSR set per word; EDT at end), `scd.c:1436-1441` (a write also reads, "verified on real hardware" via Krikzz's tool, second-hand); MD `lib/sub/gate_arr.def.h:643-653`, `lib/sub/cdrom.s:339-390` | GX cite only; MD MIT | **Cond** | First-hand hardware confirmation | Y (Probe) | Y | Y | N |
| CD-069 | Main host read via `$A12008` | LC | partial | GX `cdc.c:261` (DD=2); `../memory-map.md` `$A12004/$A12008`; MD `docs/cdrom.md:59` ("Main CPU read … not well understood") | GX cite only; MD MIT | **Cond** (emulator only) | Handshake between Main and Sub for this path | Y (Probe) | Y | Y | N |
| CD-070 | DMA → PRG-RAM | LB | Y | GX `cdc.c:332-345` (halts while Main holds PRG-RAM), `scd.c:121-135` (address = `$FF800A` × 8) | GX cite only | **Cond** | Hardware confirmation of the unit and halt behaviour; MR `docs/mcd logs/dma_prgram*.PNG` (not opened) may cover it | Y (Probe) | Y | Y | N |
| CD-071 | DMA → Word RAM (2M/1M) | LC | Y | GX `cdc.c:348-372`, `gfx.c:44-130` (× 8 units; bank select) | GX cite only | **Cond** | As CD-070; MR `dma_wordram*.PNG` (not opened) | Y (Probe) | Y | Y | N |
| CD-072 | DMA → PCM RAM | LC | Y | GX `cdc.c:326-330`, `pcm.c:398-407` (× 4 units) | GX cite only | **Cond** | As above; MR `dma_pcm*.PNG` | Y (Probe) | Y | Y | N |
| CD-073 | `$FF8004` write resets DMA addr/dest | LB | Y | GX `scd.c:1412-1428` (comments: "verified on real hardware, cf. Krikzz's mcd-verificator") | GX cite only; second-hand HW claim | **Cond** | First-hand confirmation | Y (Probe) | Y | Y | N |
| CD-074 | Transfer throughput/timing | LC | partial | GX `cdc.c:69-73` (≥ 16 SCD clocks/byte, citing MR "mcd logs"; stalls not modelled) | GX cite only; MR lead | **N** (hardware timing unconfirmed) | Real DMA rate under contention | Y (Probe) | N | Y | N |
| CD-075 | LC89513K variant | LC | partial | GX `cdc.c:79-90` (5-bit register address on CDX / WM2 types); LC89513K datasheet lead: <https://bitsavers.mirrorservice.org/components/sanyo/_dataSheets/LC89513K.pdf> (not read) | GX cite only; datasheet not read | **Cond** | Which retail models use which chip; software-visible differences | Y (Probe per model) | N | Y | N |
| CD-076 | Mode 2 / XA sub-header | LC | partial | GX `cdc.c:545-570`; EC130 (Mode 2) | GX cite only; EC130 public | **Cond** | Which titles use Mode 2; whether the BIOS must support it | Y (SynDisc Mode 2) | Y | N | N |
| CD-077 | Ring overrun behaviour | LC | partial | GX `cdc.c:573-577` | GX cite only | **N** (hardware) | Overwrite vs stall semantics | Y (Probe) | N | Y | N |
| CD-080 [X-04] | Data-read services | LB | partial | MD `lib/sub/bios.def.h:314-365`, `:458-539` (codes and notes); `lib/sub/cdrom.s:289-390` (call sequence: CDCSTOP → ROMREADN → poll CDCSTAT → CDCREAD → CDCTRN or DMA → CDCACK); CL `source/bus-sub-m68k.c:64-330` (HLE; the author notes its calls are not accurate, `:66`) | MD MIT but **codes appear to derive from XS S-BIOS or RE** (#17, OQ-7); CL AGPL cite only | **Cond**: implementable to MegaDev's usage only. Input/output registers, error codes and edge cases (0 sectors, negative counts: open TODOs at CL `bus-sub-m68k.c:128,140`) are not specified | Official ABI is excluded; no clean-room spec | Y (own SP calling our BIOS) | Y | N for our BIOS | **Y** (LB): homebrew built with MegaDev depends on these codes, which have no cleared source. Needs a #17/OQ-7 decision |
| CD-081 [X-05] | CDBSTAT / `$5E80` status block | LB | partial | MD `lib/sub/bios.def.h:62-66`; CL `source/bus-sub-m68k.c:151-171` (placeholder layout "enough to boot one game"; real address unknown) | as CD-080 | **N** | Field layout and update timing | Y | N | Y (clean-room observation) | **Y** (LC; LB only if homebrew polls it) |
| CD-082 | CDBCHK/TOCREAD/TOCWRITE | LC | partial | MD `lib/sub/bios.def.h:376-420`; CL `bus-sub-m68k.c:146-176` | as CD-080 | **Cond** (outputs only partly described) | Exact outputs | Y | N | Y | N |
| CD-083 | CD-DA (MSC*) services | LC | partial | MD `lib/sub/bios.def.h:149-334` (incl. OQ-12 duplicates `$11`/`$12`); CL `bus-sub-m68k.c:73-101` | as CD-080 | **Cond**: semantics only as MD comments | Repeat/loop flags, end-of-track behaviour, return codes | Y (SynDisc mixed mode) | N | Y | **Y** (LC: no cleared spec) |
| CD-084 | DRVINIT / DRVOPEN | LB | partial | MD `lib/sub/bios.def.h:213-228` | as CD-080 | **Cond** | Parameter table format for DRVINIT | Y | N | Y | N (LB can boot without a game calling it) |
| CD-085 | FDRSET / FDRCHG | LC | partial | MD `lib/sub/bios.h:518-552` (volume `$0000-$0400`, rate values) | as CD-080 | **Cond** | Rate units, master vs system volume | Y | N | Y | N |
| CD-086 | SCD* subcode services | LC | partial | MD `lib/sub/bios.def.h:543-626` | as CD-080 | **Cond** | Buffer formats | Y | N | Y | N |
| CD-087 | LEDSET | LC | partial | MD `lib/sub/bios.def.h:630-659` | as CD-080 | **Cond** | Patterns | Y | N | Y | N |
| CD-088 | CDCSETMODE, CDCSTARTP, `$00/$01`, WONDER* | LC | partial | MD `lib/sub/bios.def.h:131-141`, `:471-474`, `:686-720` ("needs research") | as CD-080 | **N** | Everything except CDCSETMODE | N without observation | N | Y | N |
| CD-089 [X-18] | `_CDBOOT` services | LC | partial | MD `lib/sub/cdboot.def.h:15-125` (calls 6–9 "no official documentation") | as CD-080 | **N** | Semantics of CBTIPDISC…CBTSPSTAT; which titles call them | Y | N | Y | **Y** (LC: titles that re-boot from disc) |
| CD-090 | Carry-flag busy convention; async drive work | LB | partial | MD `lib/sub/cdboot.def.h:38-68` (CC/CS), `docs/cdrom.md:3` (work pumped from INT2); CL `bus-sub-m68k.c:148,219-221`; **CL caveat**: CL intercepts execution at `$5F22` (`bus-sub-m68k.c:882-888`) and implements no CDD registers `$FF8034-$FF804B` (no handlers in `:941-1053`), and CL's CDC is high level (`source/cdc.c:44-75`) | MD MIT; CL AGPL | **Cond** | Which calls are synchronous | Y | Y (GX/PD only; **CL cannot test our CD driver** and would hijack our `$5F22` entry) | N | N |
| CD-091 [X-17] | Function-code conflicts | LC | Y (conflict) | `../open-questions.md` OQ-12; MD `lib/sub/bios.def.h:235-262` | MD MIT | **N** | Authoritative code list (only in excluded S-BIOS §2-2) | N | N | Y (observation) | **Y** (LC; part of the CD-080 blocker) |
| CD-100 | CD-DA path under BIOS control | LC | partial | GX `cdd.c:1476-1700` (CD-DA mixing through the fader) | GX cite only | **Cond** | Analogue path; mute timing | Y (SynDisc tones + Probe) | Y | Y | N |
| CD-101 | Fader `$FF8034` format and model variants | LC | partial | GX `scd.c:1501-1538` (default LC7883-type: 12-bit value in bits 4–15; Wondermega/M2 variants differ); MD `lib/sub/gate_arr.def.h:426` | GX cite only | **Cond** (emulator; LC7883 datasheet not located) | Real attenuation curve per model; unused bits | Y (Probe + audio capture) | N | Y | N |
| CD-102 | Fader ramp semantics | LC | partial | GX `cdd.c:1559`, `:1622`, `:1677` (one step per sample, "cf. LC7883 datasheet"); MD `lib/sub/bios.h:540-552` | GX/MD | **Cond** | Is ramping done by hardware or by the BIOS? | Y (Probe + capture) | N | Y | N |
| CD-103 | Mute/pre-emphasis flags | LC | partial | GX `cdd.c:2049` (RS8 bit 0 mute, bit 1 pre-emphasis, bit 2 track type) | GX cite only; EC130 (Q control field) | **Cond** | Whether de-emphasis is automatic | Y | N | Y | N |
| CD-104 | Subcode buffer, `$FF8068`, INT6 | LC | Y | GX `cdd.c:1738-1775`; MD `lib/sub/gate_arr.def.h:620-638`; `../memory-map.md` level 6 | GX cite only; MD MIT | **Cond** | Buffer image region `$FF8180` semantics; timing vs sector | Y (SynDisc `.sub`) | Y | Y | N |
| CD-105 | Q-channel use | LC | Y | EC130 (subchannel Q) | public | **Y** (format CONFIRMED) | None | Y | Y | N | N |
| CD-106 | CD+G decode for the player | LC | N | Red Book / IEC 60908 (paid, not examined) | - | **N** from free sources | CD+G packet/instruction format | Y (SynDisc after a spec) | Y | N | N (optional feature) |
| CD-107 [X-19] | Seek-to-play latency accuracy | LC | partial | GX `cdd.c:1961-1976` (tuned against a game's real-hardware recording; comment), `cdd.c:1952-1957` | GX cite only | **N** | Real seek and spin timings | Y (Probe) | N | Y | **Y** (LC: games desync without it; no source) |
| CD-110 | Sub BIOS init (vectors, INT handlers, CDD, CDC) | LA | partial | `../rom-layout.md` B-05/B-07; `../memory-map.md` §4; MD `lib/sub/memmap.def.h:64-95` | as cited there | **Cond** (our own design; the needed hardware facts are in CD-030/060) | None beyond CD-030/060 | Y | Y | Y for real-HW LA | N |
| CD-111 | Wait for drive/disc with timeout | LA | partial | GX `cdd.c:1950-1957` (minimum latency) | GX cite only | **Cond** | Real worst-case spin-up/TOC time for choosing timeouts | Y | Y | Y | N |
| CD-112 | TOC read, track 1 is data | LA | Y | CD-036 sources; EC130 (Q control: data track flag) | as CD-036 | **Cond** | As CD-036 | Y | Y | Y | N |
| CD-113 | Read boot sectors with header verify | LB | Y | CD-032/064/068 sources; MD `lib/sub/cdrom.s:289-390` | as cited | **Cond** | Pre-seek margin (MD notes the BIOS pre-seeks 2–4 sectors: `lib/sub/bios.def.h:458-467`) | Y | Y | Y | N |
| CD-114 | Validate system ID | LB | partial | CD-020 | as CD-020 | **Cond** | As CD-020 | Y | Y | Y | N |
| CD-115 | Deliver the IP to `$FF0000` | LB | Y | MD `docs/boot.md:3`, `cfg/ip.ld:5-13`; `../rom-layout.md` B-08 | MD MIT | **Y** for our own mechanism (e.g. via Word RAM, B-03/W-02) | None for LB | Y | Y | N | N |
| CD-116 [X-12] | SP at `$6000`, usercall0/1/2 | LB | Y | MD `docs/boot.md:19-26`, `lib/sub/sp_header.s`; `../bios-api.md` A-01/A-02 | MD MIT | **Cond** | Call order and re-entry (e.g. does usercall1 loop?), INT2 timing | Y | Y | Y for parity | N (LB) |
| CD-117 [X-01] [X-02] | CPU and hardware state at IP/SP entry | LB/LC | N | not found in sources examined (MD `docs/megacd_dev.md` stack notes are self-contradictory: OQ-2) | - | **N** | SR, SSP, VDP regs, Word RAM owner, interrupt enables, Z80 state at entry | Y (emulator only; not observable on HW without running Sega code) | Partial | Y | **Y** (LC) |
| CD-118 | Main↔Sub boot handshake | LA | partial | `../rom-layout.md` B-02; `../memory-map.md` comm registers | as cited | **Y** (internal to our BIOS) | None | Y | Y | N | N |
| CD-119 | Audio CD → player or message | LC | partial | MD `lib/sub/cdboot.def.h:73-81` | MD MIT | **Y** (any UI of our own) | None (the UI is ours) | Y | Y | N | N |
| CD-120 [X-13] | Mode 1 with CD services | LC | partial | `../rom-layout.md` B-02 (S-BIOS §4-1, excluded) | XS | **N** | How a cartridge obtains the CD BIOS in Mode 1 | Y (Probe) | Partial | Y | N (other area overlap) |
| CD-121 | Boot-time budget | LC | N | not found in sources examined | - | **N** | Any software or attract-mode timing dependency | Y | N | Y | N |
| CD-122 | Reset during boot | LC | N | not found in sources examined | - | **Cond** (our own design) | Soft-reset semantics expected by games | Y | Y | Y | N |
| CD-130 [X-06] | Region check | LC | partial | `../rom-layout.md` R-30/R-31; `../open-questions.md` OQ-8 | I-RHOPE (no licence, TLS issue) | **N** (policy and legal) | Legal decision; region-code semantics | Y (SynDisc per region byte) | Y | N | **Y** (legal/policy, OQ-8) |
| CD-131 [X-06] | Commercial security block calls into the boot ROM | LC | partial (excluded content) | MD `docs/boot.md:13` (IP must contain the security code); MD `lib/security.c` (**excluded; not analysed**: on first-line inspection it appears to contain Main-CPU code that calls a fixed low boot-ROM address; address deliberately not recorded); I-RHOPE ("On the Genesis Side", see R-31) | Sega-authored code inside an MIT repo; I-RHOPE | **N** | What the boot ROM must provide at the called address(es), and what the block expects back (logo display, verification), with no access to the Sega code | Only by clean-room observation | N | Y | **Y** (LC: every commercial disc; legal + no independent spec) |
| CD-132 [X-06] | Boot own discs without Sega code | LB | Y (policy) | `../bios-api.md` §4; `../provenance.md` rules 1–3 | project policy | **Y** | Fixture IP layout without a security block (MD always prepends it: `megadev.make:213-219`, so **MegaDev's default build cannot be used for fixtures**) | Y | Y | N | N |
| CD-133 [X-06] | `$1F0` string vs byte `$20B` | LC | partial | MD `lib/cd_boot.s:84-85`; GX `core/loadrom.c` R-30; PD `pico/media.c:239-245` | MD MIT; GX/PD cite only | **Cond** | Which one the BIOS uses (`$20B` lies inside the IP security block) | Y | Y | Y | N |
| CD-134 | No Sega logo; independent splash | LC | Y (policy) | `../bios-api.md` §4 | project policy | **Y** | Legal review of trademark-lockout interplay (OQ-8) | Y | Y | N | N |
| CD-140 | Read-error retry/reporting | LB | partial | MD `docs/cdrom.md:65-73` (application-level result codes); GX `cdc.c:840-870` (no error emulation) | MD MIT | **Cond** (our own policy) | Real error flag behaviour; BIOS error-return codes for compatibility | Partial (needs damaged CD-R) | N | Y | N |
| CD-141 | Drive error statuses and the "latest error" report | LC | partial | GX `cdd.c:2172-2181` (always "no error"); BE `DS_SUM_ERROR`/`DS_CMD_ERROR`/`DS_FUNC_ERROR` | GX/BE cite only | **N** | Error-code payloads | Y (Probe with bad commands) | N | Y | N |
| CD-142 | Drive silent → timeout | LA | N | not found in sources examined | - | **Y** (our own watchdog design) | None | Y (emulator with HOCK never acked; hard to force) | Partial | N | N |
| CD-143 | Tray open or disc removed mid-read | LC | N | not found in sources examined | - | **N** | Status sequence | Y (Probe) | N | Y | N |
| CD-144 | Foreign data disc → message | LA | partial | CD-020 | as CD-020 | **Y** (our own rule) | None | Y (SynDisc without an ID) | Y | N | N |
| CD-145 | Skipped/out-of-order sector detection | LC | partial | GX `cdd.c:1813-1825`; EC130 header | GX cite only; public | **Y** (compare HEAD MSF to the expected value) | None | Y | Partial (emulators never skip) | Y | N |
| PRV-01 | The maintainer decides whether paraphrased citation of CONFIDENTIAL-marked manuals is allowed; until then they are excluded | LA | partial (issue open) | Issue #17; PR #16 `docs/specifications/README.md:3-5`; `open-questions.md` OQ-19 | L-01..L-07: CONFIDENTIAL / PROPERTY OF SEGA. LEGAL-REVIEW. | N: a decision, not a source | Maintainer/legal decision text; what to do with PR #16 citations if rejected | N | N | N | **Y**: PR #16 cannot merge. Many items stay ESTIMATED because the only official cross-check is excluded. |
| PRV-02 [X-04] | A documented clean-room basis on which the Sub BIOS entry points (`$5F16`/`$5F1C`/`$5F22` etc.), function codes and register conventions may be implemented | LB | partial | `megadev/lib/sub/bios.def.h` (PR #16 bios-api.md §1); `megadev/docs/main_bios.md:12` (Sub calls documented in the official manual); `clown/source/bus-sub-m68k.c:712` (`$5F16` trap), `:882-884` (`$5F22` trap) | MegaDev is MIT, but its Sub-side data is derived from L-02 (confidential). clown is AGPL; its HLE knowledge comes by an unknown method. LEGAL-REVIEW: are interface facts (addresses, codes) usable? | Cond: only if the maintainer accepts interface facts from MegaDev, or after black-box confirmation (EXP-04) | Provenance-clean list of entries, codes, argument registers, return conventions | Y (EXP-04 conformance suite on our BIOS) | Y for our own BIOS. Expected values need the original as reference. | Y for authoritative expected values (or a user-supplied BIOS in a local emulator, PRV-26) | **Y**: homebrew SPs call these entries directly. No provenance-clean source exists. |
| PRV-03 [X-08] | A documented clean-room basis for the Main-side `$280` library and its work RAM | LC | partial (RE only) | `megadev/docs/main_bios.md:12,30-32,104,212,220`; PR #16 bios-api.md A-11/A-12, OQ-7 | Derived from reverse engineering of Sega ROMs; MegaDev invites reading the disassembly. Tech Bulletin #3 (L-06) is quoted. Policy rule 1 / OQ-7. LEGAL-REVIEW. | **N**: not found in the sources examined (L-01..L-22) except RE-derived MegaDev material; the official doc (`ROM_UTIL.DOC`, L-07) was not found (corrected during integration review) | Entry list, order, semantics, work-RAM layout | Partly: black-box observation of retail games' calls (EXP-09) under a clean-room protocol | Y for observation if a user-supplied BIOS is used locally (LEGAL-REVIEW) | Y for ground truth | **Y** for LC: Japanese titles named in `megadev/docs/main_bios.md:32` call it. |
| PRV-04 [X-03] | Main exception/interrupt jump table at `$FFFD00` (6-byte JMP slots; V-INT slot that software patches) | LB | partial | `megadev/lib/main/memmap.def.h:19,68-99` (via PR #16 A-10); Tech Bulletin #3 quote `megadev/docs/main_bios.md:56-63`; `clown/source/mega-cd-boot-rom.c:1-24` (vector words point into `$FFFD00-$FFFDA2`) | MegaDev MIT, partly RE plus a confidential quote; clown AGPL (data observed only, not copied) | Cond: three sources agree on the table's existence and base, but the per-slot assignment rests on MegaDev (OQ-12 duplicate slot) | Authoritative slot-to-vector map; the duplicate `$FFFD80` | Y (a probe IP patches each slot and triggers the exception) | Y for consistency | Y to confirm | N for LB if limited to the V-INT/H-INT slots MegaDev homebrew uses; Y for full LC |
| PRV-05 [X-06] | What the original BIOS checks on a disc (bytes compared, when, failure behaviour), so that a policy can be chosen | LC | partial (single weak source) | I-RHOPE fetched HTML lines 54, 58 (compares `200h-783h` with a copy in the BIOS; the check runs only for `SEGABOOTDISC`/`SEGADISCSYSTEM`); `megadev/new_project/README.md:21` (security code size 1,412 B US/EU, 342 B JP); PR #16 OQ-8 | I-RHOPE: no licence, TLS-invalid; MegaDev MIT (sizes are facts). The security code is Sega's. LEGAL-REVIEW (lockout and interoperability). | Cond: an independent BIOS **need not** replicate the check; only the **policy** needs a legal decision | Whether the check covers JP, and its exact range per region/model; legal stance | Partly (EXP-05 negative tests on our own discs) | N (emulators skip it: `clown/source/clownmdemu.c:502,511` region code commented out) | Y | **Y** for LC: no policy without legal review (OQ-8) |
| PRV-06 [X-06] | How disc region interacts with console region (header region field, rejection behaviour) | LC | partial | `clown/source/clownmdemu.c:502,511` (region read commented out, emulator-scoped); `megadev/megadev.make:50-63`, `megadev/lib/cd_boot.s:85` (header region string); I-RHOPE | Emulator/SDK only | Cond: the header field format is known; the hardware reaction is not | Original BIOS reaction to a region mismatch, per model | Y (EXP-05 with region-byte variants) | N | Y | N for LB (we choose the policy); N for LC unless a game is found that depends on regional rejection |
| PRV-07 [X-06] | Retail security code (it runs from `$FF0000` and returns to `$FF0584` on US discs) works on our BIOS: the VDP state, font and interrupts it relies on | LC | partial | I-RHOPE line 60 (logo display, return address, font left in VRAM); `megadev/docs/boot.md:13-15` | The code belongs to Sega; observation only | **N**: dependencies are undocumented in non-excluded sources | Which BIOS-set state the security code reads (VDP regs, vectors, Sub status) | Partly: run a user-owned disc's IP under our BIOS in a local emulator and trace it (EXP-09, LEGAL-REVIEW) | Y (local, not CI) | Y to confirm | **Y** for LC: every retail disc runs this code first |
| PRV-08 | No Sega security-block bytes in the repo, fixtures, CI caches or releases, including MegaDev-built IPs | LB | Y (policy exists) | `docs/provenance.md:5`; `megadev/lib/security.c:1-9,15-274`; `megadev/megadev.make:213-218` | Sega code inside an MIT repo; MIT does not license it. LEGAL-REVIEW. | Y: a project rule plus a detector (e.g. reject any fixture whose IP begins with a known security-block hash, without storing the bytes) | A hash list that does not store the bytes (needs a lawful way to compute it) | Y | Y | N | N, but a high risk if missed: MegaDev examples embed the block by default |
| PRV-09 | Our test discs boot under our BIOS without Sega code, and can be compared under the original BIOS lawfully | LB | partial | `megadev/megadev.make:213-218` (security linked by default); I-RHOPE lines 75, 79 (`base.img` approach, **rejected**) | Comparison under the original BIOS requires the security block on the disc, i.e. Sega code in a local build | Y for our side (our BIOS defines the policy). Comparison: Cond (LEGAL-REVIEW) | A lawful way to produce "comparison" discs, or a Mode-1 route (EXP-04b) | Y | Y | Y for comparison | N for LB on our BIOS; Y for the reference comparison |
| PRV-10 [X-16] | Boot-sector header layout: system ID at sector 0, IP offset/size fields, SP offset/size | LB | Y (several non-excluded sources) | I-RHOPE lines 52-58; `megadev/lib/cd_boot.s:30,52-60` (disc ID and IP/SP offset/size fields; the earlier `:85,95` pointed at the region string, corrected during integration review); `clown/source/clownmdemu.c:498-511` (word offsets `0x18/0x1A/0x20/0x22`, emulator-scoped); `gpgx/core/cd_hw/cdd.c:1181-1182` (first-track type check) | MIT / no licence / AGPL / non-commercial; facts only | Cond: cross-checked across three lineages, but no hardware measurement (corrected during integration review: was "Y (Cond: …)") | Behaviour for non-default IP sizes on hardware (`megadev/docs/boot.md:15` says untested) | Y | Y | Y for non-default layouts only | N |
| PRV-11 | Accepted system IDs (`SEGADISCSYSTEM`, `SEGABOOTDISC`, `SEGADISC`, `SEGADATADISC`) and their semantics | LB | partial | I-RHOPE lines 52-55 ("not exactly sure what the difference is"); PR #16 OQ-9; official S-FMT excluded | I-RHOPE only, uncertain | Cond: `SEGADISCSYSTEM` boots in every source; the others are unclear | Semantics of the other three IDs | Y (EXP-05 ID variants) | Y, emulator-scoped | Y for truth | N for LB (use `SEGADISCSYSTEM`); open for LC |
| PRV-12 [X-04] | Sub-BIOS function codes (`MSC_*`, `ROM_*`, `CDB*`, `BRM*` …) from a source independent of S-BIOS | LB | partial | `megadev/lib/sub/bios.def.h` (duplicates `:235,242` vs `:252,262`, OQ-12); `clown/source/bus-sub-m68k.c:73-327` (codes `0x02`…`0x8D` handled), `:720-838` (BRM codes `0x00`-`0x08`); `clown/TODO.md:104` (BuRAM calls incomplete) | MegaDev derived from L-02; clown AGPL, method unknown | Cond: two non-confidential listings exist, but **neither is provenance-independent** | Codes clown leaves unimplemented (`bus-sub-m68k.c:327` logs unrecognised calls); argument and return semantics | Y (EXP-04) | Y against clown's HLE; against GPGX/Pico only with a Sega BIOS | Y for truth | Y for LB (part of PRV-02) |
| PRV-13 [X-07] | Internal BRAM on-media format and `_BURAM` behaviour, so that our BIOS reads saves the original wrote and vice versa | LC | partial | `clown/source/bus-sub-m68k.c:712-840` (HLE `_BURAM`); `megadev/lib/sub/bram.def.h`, `bram.h:60-145` | AGPL / MIT derived from L-02 | Cond | Directory/format layout written by the original BRAM manager | Y (EXP-08: read raw BRAM written by the original; data only) | Partly | Y | N (games format BRAM through our BIOS); Y only for save interoperability |
| PRV-14 | Gate-array register map (`$A12000-$A1202F` Main side, `$FF8000+` Sub side) | LA | partial | PR #16 memory-map.md (GPGX/Pico/MegaDev citations); `clown/source/bus-main-m68k.c:511-516` (H-INT override at `$72`) | Emulators non-commercial/AGPL; MegaDev MIT; official excluded | Cond: three code lineages for the main registers; bit-level details are emulator-scoped | Power-on values, cropped bits (OQ-13, OQ-14) | Y (EXP-01) | Y, emulator-scoped | Y | N for LA (emulator scope is enough to boot); Y for hardware claims |
| PRV-15 [X-09] | CDD command/status protocol (packet format, checksum, timing, command set) | LB | partial | `gpgx/core/cd_hw/cdd.c`; `pico/pico/cd/cdd.c:5` (**copyright Eke-Eke / GPGX**); clown: **no CDD model** (HLE only, `clown/TODO.md:52-69`); ares `ares/md/mcd/cdd.cpp` (not inspected) | Non-commercial; official (S-HW §3-6) excluded | **N** today: one code lineage (GPGX ≈ Pico), no independent document, no measurement | Every protocol detail, cross-checked by a second lineage or by hardware | Y (EXP-02 on hardware) | **N**: one lineage cannot validate itself (ares could add a second one; unverified) | **Y** | **Y**: our Sub BIOS must drive the CDD to read any disc (LB) |
| PRV-16 [X-10] | CDC (LC8951-class) register protocol and DMA to Word RAM / PRG-RAM | LB | partial | `gpgx/core/cd_hw/cdc.c`; `pico/pico/cd/cdc.c:5` (GPGX lineage); `clown/source/cdc.c` (separate lineage per `clown/README.md:79-83`); chip datasheet **not found in the sources examined** (L-01..L-22) | as above | Cond: two lineages (GPGX, clown) | Vendor datasheet; hardware timing | Y (EXP-02) | Y (two lineages) | Y for timing | N for LB if emulator agreement is accepted; Y for a hardware release |
| PRV-17 | 68000 reset, vector fetch, exception frames, interrupt levels | LA | Y | L-08 (NXP MC68000UM, SHA-256 above) | Vendor manual; cite and paraphrase only | Y | none in this area | Y | Y | N | N (note the UA-dependent 404: record the hash, not the file) |
| PRV-18 | Emulators used as test hosts can load our BIOS image | LA | Y | `gpgx/core/loadrom.c:409-415` (`CD_BIOS_US/EU/JP`); `picodrive/platform/common/emu.c:172-181` (`find_bios` by filename); clown: built-in only (`clown/source/bus-main-m68k.c:19-20,519`) | Tools used externally, not vendored | Y | clown needs a patch (AGPL) to host an external BIOS | Y | Y | N | N |
| PRV-19 [X-09] | "Two emulators agree" counts only if they are independent implementations | LA | Y (evidence found here) | `pico/pico/cd/cdd.c:5`, `cdc.c:5`, `gfx.c:5`, `cdd.h:5` vs GPGX; PR #16 OQ-11 plans a GPGX/Pico diff | n/a | Y: a rule change in the test plan | Lineage of the ares/jgenesis/MiSTer CD code | Y | Y | N | N, but **OQ-11's GPGX-vs-Pico diff is not independent verification**; fix this before relying on it |
| PRV-20 | Ledger of what each source permits | LA | Y (this file) | sections 1.2-1.3; licence files cited there | — | Y | Legal confirmation of the compatibility reading (LEGAL-REVIEW) | n/a | n/a | n/a | N |
| PRV-21 | Every source pinned and integrity-checked | LA | partial | sections 1.1-1.2 | — | Y | Scans have no publisher hash; I-RHOPE TLS invalid; NXP UA-dependent | n/a | n/a | n/a | N |
| PRV-22 | Hardware measurements exist for every hardware-scope CONFIRMED claim | LA | **N** | PR #16 README:30 ("no measured results of our own") | — | N: requires measurement | All of it | Y (EXP-01..03) | N | **Y** | Y for release claims; N for emulator-stage development |
| PRV-23 | Mode-1 probe cartridge (our code on a flash cart, stock Mega-CD) reads power-on registers, mirrors and the H-INT override | LA | Y (design in PR #16 OQ-1, 4, 13, 14, 17) | PR #16 `open-questions.md:18-30`; Mode-1 mapping `gpgx/core/cd_hw/scd.c:1590-1604` (emulator-scoped) | Own code only | Y (design) | Flash cart and hardware access | Y | Partly (the same probe runs in emulators as a differential) | **Y** | N |
| PRV-24 | Run our Sub BIOS on real hardware: Main code in a Mode-1 cart holds the Sub CPU in reset, writes our Sub BIOS into PRG-RAM, releases reset | LB | partial | Sub address 0 maps to PRG-RAM: `gpgx/core/cd_hw/scd.c:1690` (emulator-scoped); PRG-RAM write window via `$A12002/3` (PR #16 memory-map.md, OQ-14) | Own code only | Cond: the mechanism is ESTIMATED from emulator code; bank/write-protect bits are cropped in the scan (OQ-14) | Hardware confirmation that the Sub CPU fetches its reset vectors from PRG-RAM; WP/BK bits | Y | Y (emulator first) | **Y** | N at design stage, but it is the key enabler for LB hardware tests |
| PRV-25 | Validate our Main-side BIOS in Mode 2 on hardware without risky modification | LA | partial | Boot-ROM chip replacement = hardware modification (**out of scope**, damage risk); FPGA host L-19 (not inspected); Mode-1 relocation (EXP-03) covers most logic | GPL FPGA core (external tool only) | Cond | Whether the MiSTer core accepts an arbitrary BIOS image (not verified) | Y (FPGA) | n/a | Y or FPGA | N for development; Y for a "runs on real Mode-2 hardware" claim |
| PRV-26 | Legal basis for observing the original BIOS (owned console), using a user-supplied BIOS dump in a local emulator, and running user-owned retail discs for black-box traces | LC | N | `docs/provenance.md:7` (rule 3 allows observation, with binaries kept outside the repo and CI) | LEGAL-REVIEW (jurisdiction-specific) | N: a legal question | Written guidance on which observations are permitted | n/a | n/a | n/a | **Y** for LC: compatibility evidence for retail games depends on it |
| PRV-27 [X-15] | Handle TMSS: write `"SEGA"` to `$A14000` on TMSS consoles | LA | partial | PR #16 OQ-6; a Mega-CD-specific statement was not found in the sources examined | Trademark-based lockout question. LEGAL-REVIEW. | Cond | Whether the Mega-CD Mode-2 path triggers TMSS at all | Y (EXP-01 on TMSS and non-TMSS units) | Y, emulator-scoped | Y | N for emulators; Y for a hardware boot on TMSS units until resolved |
| PRV-28 | The BIOS boot screen, CD player and BRAM manager use no Sega logo, fonts, audio or text | LA | Y (policy) | `docs/provenance.md:3,5`; PR #16 bios-api.md §4 | — | Y (own design) | none | Y | Y | N | N |
| PRV-29 | Variants per model/region (Model 1/2, CDX, Wondermega, LaserActive, Multi-Mega) and what differs | LC | partial | `megadev/docs/main_bios.md:38` (`$280` table "at the same offset" across the listed models, RE-derived); PR #16 OQ-16 | RE-derived | N: not found in the sources examined (L-01..L-22) except RE-derived statements (corrected during integration review) | Model list with BIOS revisions and behaviour differences | Partly (PCB photos for capacity, OQ-16) | N | Y, per model | N for a single target model; Y for broad LC claims |
| PRV-30 | Official corporate page for the model list | LC | N (inaccessible) | L-09 (HTTP 403, Cloudflare) | Corporate terms (unread) | N | Page content | n/a | n/a | n/a | N (a human checks it in a browser) |
| PRV-31 | Evidence that a non-Sega boot ROM / HLE BIOS boots Mode-2 discs (feasibility lead) | LB | Y (emulator-scoped) | `clown/source/clownmdemu.c:494-531` (reads sector 0, loads the IP to Word RAM and then Main RAM, the SP to PRG-RAM `$6000`, gives Word RAM to the Sub CPU; no region/security check); `clown/source/bus-main-m68k.c:19-20` (built-in boot ROM) | AGPL; read only. Boot-ROM blob provenance unverifiable (no source in the repo). | Y as a lead only (emulator-scoped; CONFIRMED for that emulator) | How far the HLE approach diverges from hardware | n/a | Y | N | N |
| PRV-32 | Emulator comments like "This is what Sega's BIOS does" are leads, never specs | LC | Y | `clown/source/clownmdemu.c:506,523`; `clown/source/cdda.c:6`; `clown/source/bus-sub-m68k.c:128,140,153` (open questions about official BIOS behaviour) | AGPL; method unknown (possibly disassembly or observation) | Y (as a process rule) | The method behind each claim | Y (EXP-04 turns each claim into a test) | Y | Y | N |
| PRV-33 | CD-DA fader and PCM behaviour the BIOS exposes (e.g. 12-bit fader volume) | LC | partial | `clown/source/cdda.c:6` (upper 4 bits discarded, attributed to Sega's BIOS); `gpgx/core/cd_hw/cdd.c:2-3` (file is "CD drive processor & CD-DA fader"); RF5C164 datasheet **not found in the sources examined** | AGPL / non-commercial | Cond | Vendor datasheet; hardware fader curve | Y | Y | Y for accuracy | N |
| PRV-34 | Is a spec team allowed to read a reference-BIOS disassembly? Rule 1 forbids committing it; rule 3 allows observation | LC | N | `docs/provenance.md:5,7` | LEGAL-REVIEW | N: a policy question | Explicit policy text | n/a | n/a | n/a | Y for clean-room option CR-A (section 6) |
| PRV-35 | Patent, trademark and product-name review before distribution | LA | N | `docs/provenance.md:9-10` | LEGAL-REVIEW | N | Review result | n/a | n/a | n/a | N for development; Y for release |
| PRV-36 | Official SDK artefacts known only by reference | LC | N (not found) | `megadev/docs/main_bios.md:50-71` (Tech Bulletin #3, `MAINENT.I`, `ROM_UTIL.DOC`); `:87-100` (32X `MAINCPU.INC`); PR #16 bios-api.md:7 (`cabios.i`) | Confidential-marked by reference; existence only | N | n/a (not to be adopted) | n/a | n/a | n/a | N (recorded as leads for EXP-04/09) |
| PRV-37 | Own disc-image fixtures (ISO / BIN+CUE) and CD-R readability on real units | LB | partial | `gpgx/core/cd_hw/cdd.c:510-525,810-820` (accepted image formats, emulator-scoped); CD-R readability on real Mega-CD units **not found in the sources examined** | Own fixtures only | Y for emulators | Hardware CD-R compatibility per model | Y | Y | Y for disc tests | N |
<!-- END GENERATED: matrix -->

## 8. Changes made during integration review

The independent review of PR #21 found over-claims and absence wording that the brief forbids. Each correction below was made in the area file, with "corrected during integration review" noted on the row or line, and flows into §7 through the generator. No blocker was removed, and no Implementable rating was raised.

| # | File | Item / location | Change |
| --- | --- | --- | --- |
| C-01 | rom-cpu-memmap.md | ROM-41, reference cell | PicoDrive `memory.c:186-187`: the "verified" SRES=0 ⇒ SBRQ=1 rule is commented out, so PicoDrive does not apply it (cf. COM-05). The cell no longer cites it as support. |
| C-02 | rom-cpu-memmap.md | ROM-45, provenance cell | "Both SDKs say … official BIOS manual" → only MegaDev says so; MCDBOOT states no origin. |
| C-03 | rom-cpu-memmap.md | ROM-45, Implementable cell | The same correction in the rationale. |
| C-04 | rom-cpu-memmap.md | §3 LB note | "both SDKs trace back to the excluded official manual" → MegaDev does; MCDBOOT states no origin. |
| C-05 | comm-wordram-irq.md | COM-09, missing-information cell | "emulators: no" → GX and PicoDrive: no; clownmdemu `source/bus-main-m68k.c:972` blocks Main writes below WP×512 (cf. ROM-43). |
| C-06 | bios-api.md | §3 summary, LC blockers | "unknown everywhere" → "not found in the sources examined: MD, CL, MB, M1, E-GPGX-F, E-PICO". |
| C-07 | cd-boot.md | Short answer, LA | "BlastEm independently" → BlastEm's `cdd_mcu.h` agrees with GX; its independence is unproven. |
| C-08 | cd-boot.md | §0 source register, BE row | "independent of GX" → independence from GX unproven (only enum names read). |
| C-09 | cd-boot.md | CD-031, Implementable cell | "two independent emulator lineages agree" → GX and BE agree; BE's independence is unproven. |
| C-10 | cd-boot.md | CD-034, Implementable cell | "two lineages agree" → GX and BE agree; independence unproven. |
| C-11 | cd-boot.md | CD-053, Implementable cell | Same correction as C-10. |
| C-12 | provenance-experiments.md | PRV-03, Implementable cell | "no public non-RE source; the official doc is unknown" → not found in the sources examined (L-01..L-22) except RE-derived MegaDev; the official doc was not found. |
| C-13 | provenance-experiments.md | PRV-29, Implementable cell | "no public non-RE per-model list" → not found in the sources examined except RE-derived statements. |
| C-14 | provenance-experiments.md | §4 top blocker 5 | "known only from reverse engineering" → not found in the sources examined except reverse-engineered material. |
| C-15 | provenance-experiments.md | §5.1, PRV-03 row | "Known only from RE" → not found in the sources examined (L-01..L-22) except RE-derived material. |
| C-16 | provenance-experiments.md | §5.1, PRV-29 row | "Only RE-derived statements exist" → not found in the sources examined except RE-derived statements. |
| C-17 | provenance-experiments.md | PRV-10, Implementable cell | "Y (Cond: …)" → **Cond**, because the parenthesis already stated the condition. This lowers the rating; it does not raise it. |
| C-18 | provenance-experiments.md | PRV-10, reference cell | `megadev/lib/cd_boot.s:85,95` (region string) → `:30,52-60` (disc ID and IP/SP offset/size fields), checked at `7a7246c`. |
| C-19 | provenance-experiments.md | §3 intro | States that `gpgx/…` line numbers refer to upstream `49c5847`, not the fork (e.g. `cdd.c:1181` upstream = `:1168` fork). |

Changes to this document and the tool:

- The headline was redefined by adding rules 5 and 6 (§4). The previous headline is kept as the lenient secondary view.
- Rule 4 now treats inherited blockers ("via API-60") as blocking, which affects API-56.
- The X-groups (§3) are now data that the script reads. The provenance hand-check overrides (H-01…H-05) are a table in §4.
- Verdict B was split into B1 (own ABI) and B2 (MegaDev-class); B2 is 現時点では困難. Verdicts A and C were reworded against the new headline, and the absence wording in §1 and §2 was rephrased.
- §1 gained G-17 (CD-033), and API-56 was added to G-10.
- §3 entries X-09, X-20, X-21 and S-2, and the §6 source table, were updated for C-01, C-05, C-07…C-11 and C-19.
