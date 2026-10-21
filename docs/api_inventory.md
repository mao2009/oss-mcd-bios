# Mega-CD BIOS API inventory (working ledger)

**Status: INCOMPLETE — category coverage is mapped, individual service enumeration is not yet complete.**

This ledger tracks **public program-facing Mega-CD/Sega CD BIOS interfaces**, not all internal ROM subroutines or memory-mapped device registers. Do not infer compatibility from a listed entry.

## Primary inventory

Machine-readable seed: [api_inventory.csv](api_inventory.csv).

The seed deliberately records only directly identified shared entry points and callbacks. **It is not a complete list of individual BIOS calls.** Blank fields mean *unknown*, not zero, and no API-count denominator is asserted.

### Inventory scope / enumeration checklist

| Category | Reference | Individual services enumerated | ABI verified | Implementation |
|---|---|---|---|---|
| D — Drive mechanism | BIOS Manual §3-D, p.12 | No | No | Not implemented |
| M — CD-DA music | §3-M, pp.13–17 | No | No | Not implemented |
| R — CD-ROM data | §3-R, pp.18–19 | No | No | Not implemented |
| B — BIOS other functions | §3-B, pp.20–22 | No | No | Not implemented |
| F — Fader | §3-F, p.23 | No | No | Not implemented |
| C — CDC decoder | §3-C, pp.24–25 | No | No | Not implemented |
| S — Subcode | §3-S, pp.26–28 | No | No | Not implemented |
| L — LED | §3-L, p.29 | No | No | Not implemented |
| Backup RAM calls | §7, pp.38–45 | No | No | Not implemented |
| Common jump table and callbacks | §5, pp.33–35 | Entry points seeded only | No | Not implemented |

The _cdbios and _buram symbols are dispatch interfaces, not a claim that their subordinate functions have been inventoried. The four _usercall callbacks are **not BIOS services**, and must be excluded from the service-count denominator.

## Completion gates

1. Enumerate every item in the **BIOS Call List** (§2-2, pp.7–8) as its own row. Record its original name and selector, with page-level citations. Do not fabricate unknown selectors or addresses.
2. Reconcile each against the descriptions in §3, backup RAM in §7, and jump table contracts in §5; check alternate naming, aliases, and duplicates. Track region/version scope explicitly.
3. Cross-check additional first-hand, legally appropriate information (licensed open-source implementations and independently produced behavior tests). The Sega manual is a *behavioral reference*, not permission to copy proprietary code/assets.
4. For each row, verify exact call convention, registers, flags, blocking semantics, errors, and CPU context, where applicable.
5. Only when service enumeration is reconciled, freeze a per-version denominator. Report independently: documented / implemented / emulator-tested / reference-ABI-verified / hardware-tested.

## Field semantics

- `kind`: `service`, `dispatcher`, or `callback`. Only `service` contributes to the service-implementation ratio.
- `inventory_status`: `documented_symbol`, `candidate`, `confirmed`, or `disputed`.
- `implementation_status`: `not_implemented`, `partial`, or `implemented`.
- `abi_status`: `unverified`, `synthetic_tested`, `emulator_verified`, `reference_verified`, or `hardware_verified`.
- Avoid conflating test success with verified compatibility.

## References

- [Mega-CD BIOS Manual table of contents](https://www.megadrive.org/elbarto/megacd/Official%20Sega%20CD%20Manual/segacd_toc.html), especially §2-2 (pp.7–8), §3, §5 and §7.
- [Technical Bulletins](https://segaretro.org/images/2/2e/Sega-CD_Technical_Bulletins.pdf): validate compatibility variations and call conventions as separate evidence.
- [Project roadmap](roadmap.md): M3 BIOS compatibility is future work.

**No proprietary source code, disassembly, extracted ROM data, or copyright-protected assets are included in this ledger.**
