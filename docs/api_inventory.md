# Mega-CD BIOS API inventory — provenance-first working ledger

**State: INCOMPLETE / UNVERIFIED.** No verified individual service count, ABI compatibility, bootable BIOS, or game compatibility is claimed.

This project inventories public *program-facing* BIOS services separately from dispatchers, callbacks, hardware registers, and internal routines. Source descriptions are not automatically permission to reuse code or copyrighted documentation.

## Source policy

1. **Preferred discovery source:** [Megadev](https://github.com/drojaazu/megadev), a publicly available Mega-CD C/68k framework whose repository declares an MIT license. Audit the exact revision, file headers, origin, and third-party notices before reusing any particular code or text. The repository license is not proof that every fact or contribution has uncontested provenance.
2. **Supporting tools:** [SGDK](https://github.com/Stephane-D/SGDK) (its library/tools declare MIT, but it primarily targets Mega Drive rather than being a complete Mega-CD BIOS API reference), and permissively licensed original test programs / independently authored hardware observations.
3. **Behavioral cross-check only, not code donor:** [Genesis Plus GX](https://github.com/ekeeke/Genesis-Plus-GX) (core carries non-commercial restrictions and other components have separate notices). Never copy its implementation into this MIT BIOS without a distinct legal review.
4. **Restricted provenance / quarantine:** archives of Sega documents marked CONFIDENTIAL, proprietary ROM dumps/disassembly and undocumented leaked material. Do **not** use these as the sole basis of confirmed ABI contracts, do not transplant code, and do not commit copies or transcription. Legacy entries based only on archived manuals remain unverified until independently established from appropriate sources.
5. Verify licenses per **file and revision**. Record exact path, commit, license, origin, evidence type, and confidence. Do not interpret public GitHub availability as consent for unrestricted reuse. Legal questions require qualified review before binary distribution.

## Machine-readable ledger

[api_inventory.csv](api_inventory.csv) contains *legacy candidates*, not verified API services. Entries sourced only from a non-official archive have been marked `source_review_required` and deliberately contain no authoritative call selector, address or ABI. Callback/dispatcher rows are **excluded** from the service-count denominator.

Field meanings:

- `kind`: service / dispatcher / callback.
- `inventory_status`: `source_review_required`, `candidate`, `confirmed`, `disputed`.
- `implementation_status`: not_implemented / partial / implemented.
- `abi_status`: unverified / synthetic_tested / emulator_verified / reference_verified / hardware_verified.

No meaningful coverage fraction exists until the individual-service inventory is reconciled with independently attributable primary evidence.

## Coverage work queue (not a claim of completeness)

| Area | State | Evidence required |
|---|---|---|
| BIOS dispatch/call convention | NOT VERIFIED | Megadev file+revision and independent minimal caller |
| CD drive / CDD controls | NOT ENUMERATED | public implementation or observed tests |
| CD-DA playback | NOT ENUMERATED | caller contract and behavior observations |
| CD-ROM / CDC reads and transfers | NOT ENUMERATED | precise service ABI + return/error tests |
| Subcode and fader | NOT ENUMERATED | independent API references |
| LED or ancillary services | NOT ENUMERATED | publicly attributable caller references |
| Backup RAM services | NOT ENUMERATED | external callers and persistence tests |
| Regional and firmware version differences | NOT VERIFIED | version-specific repeatable tests |

These are investigation categories only. They are not derived from a claimed exhaustive proprietary manual count.

## Gates to promote a candidate to CONFIRMED

1. Locate an independently published, legally suitable caller, header, or original test; document revision, exact file, license and scope. Where provenance is uncertain, retain candidate status.
2. Separate an API service from a dispatcher or callback; capture exact entry mechanism and selectors **only with evidence**.
3. Independently exercise the contract in a bounded emulator test (document versions and hashes); record inputs, outputs, error behavior and CPU context.
4. Cross-check with a second independent source or reference behavior where legally appropriate. Distinguish documented, implementation-tested, original-BIOS-ABI-verified and physical-hardware-verified.
5. Record regional/firmware differences; freeze denominators only after explicit coverage review.

## Historical provenance note

The original ledger used an unofficial online mirror of a purported Sega development manual, some versions marked CONFIDENTIAL, for its category taxonomy and six placeholder symbols. Those assertions are **not** treated as confirmed. References to that mirror were removed from current operational inventory, without rewriting Git history. This file documents that provenance limitation transparently.

This is engineering provenance hygiene, **not a legal opinion or guarantee**.
