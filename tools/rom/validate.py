"""Structural ROM validator (Python stdlib only).

Usage: python3 -I -B tools/rom/validate.py ROM [--config tools/rom/rom-config.json]
                                                [--invariants docs/specifications/invariants.json]

Implements the invariants schema (schema_version 2) owned by
docs/specifications/test-invariants.md (Issue #1):

- The file is rejected (exit 1, no checks run) if it is malformed: unsupported
  schema_version, missing/invalid fields, duplicate ids, unknown check type, missing check
  parameters, a bytes_not_in value of the wrong length, or an entry that breaks the
  enforceability rule (enforceable true only for CONFIRMED+hardware or PROJECT-RULE).
- enforceable true: PASS or FAIL; a FAIL fails the build.
- enforceable false: reported as SKIP with status/scope and the advisory outcome. Never PASS.
- A read past the end of the image fails the check.

Built-in checks are toolchain/CPU-level only: ROM size equals the build config's rom_size
(build consistency, the value itself is UNVERIFIED) and the 68000 initial SSP/PC longwords
are readable and even. Mega-CD layout facts come only from the invariants file, if present.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CONFIG = os.path.join(ROOT, "tools", "rom", "rom-config.json")
DEFAULT_INVARIANTS = os.path.join(ROOT, "docs", "specifications", "invariants.json")
SCHEMA_VERSIONS = {2}
STATUSES = {"CONFIRMED", "ESTIMATED", "UNCONFIRMED", "PROJECT-RULE"}


class OutOfRange(Exception):
    pass


def _read(rom, offset, n):
    if offset < 0 or offset + n > len(rom):
        raise OutOfRange(f"offset {offset:#x}+{n} outside {len(rom)}-byte image")
    return rom[offset:offset + n]


def _u32(rom, c, offset=None):
    v = int.from_bytes(_read(rom, c["offset"] if offset is None else offset, 4), "big")
    return v & c.get("mask", 0xFFFFFFFF)


def _in_ranges(v, ranges):
    return any(lo <= v <= hi for lo, hi in ranges)


def _offsets(c):
    exclude = set(c.get("exclude", []))
    return [o for o in range(c["start"], c["end"] + 1, c["step"]) if o not in exclude]


def _each(rom, c, pred):
    bad = [f"{o:#x}={_u32(rom, c, o):#x}" for o in _offsets(c) if not pred(_u32(rom, c, o))]
    return not bad, "bad: " + ", ".join(bad) if bad else f"{len(_offsets(c))} values ok"


def _u16(rom, c):
    return int.from_bytes(_read(rom, c["offset"], 2), "big")


def _at(rom, offset, s):
    return _read(rom, offset, len(s)) == s.encode("ascii")


# type -> (required params, check returning (ok, detail))
CHECKS = {
    "size_equals": (("bytes",), lambda rom, c: (len(rom) == c["bytes"], f"size {len(rom)}, expected {c['bytes']}")),
    "u32_even": (("offset",), lambda rom, c: (_u32(rom, c) % 2 == 0, f"value {_u32(rom, c):#x}")),
    "u32_range": (("offset", "min", "max"), lambda rom, c: (
        c["min"] <= _u32(rom, c) <= c["max"], f"value {_u32(rom, c):#x}, range {c['min']:#x}..{c['max']:#x}")),
    "u32_in_ranges": (("offset", "ranges"), lambda rom, c: (_in_ranges(_u32(rom, c), c["ranges"]), f"value {_u32(rom, c):#x}")),
    "u32_even_each": (("start", "end", "step"), lambda rom, c: _each(rom, c, lambda v: v % 2 == 0)),
    "u32_each_in_ranges": (("start", "end", "step", "ranges"),
                           lambda rom, c: _each(rom, c, lambda v: _in_ranges(v, c["ranges"]))),
    "u16_in": (("offset", "values"), lambda rom, c: (_u16(rom, c) in c["values"], f"value {_u16(rom, c):#06x}")),
    "bytes_equal": (("offset", "ascii"), lambda rom, c: (_at(rom, c["offset"], c["ascii"]), f"looking for {c['ascii']!r}")),
    "bytes_equal_any": (("offsets", "ascii"), lambda rom, c: (
        any(_at(rom, o, c["ascii"]) for o in c["offsets"]), f"looking for {c['ascii']!r}")),
    "bytes_not_in": (("offset", "length", "ascii_values"), lambda rom, c: (
        not any(_at(rom, c["offset"], s) for s in c["ascii_values"]), f"found {_read(rom, c['offset'], c['length'])!r}")),
}


def schema_errors(doc):
    """Return a list of reasons the invariants document is malformed (empty = valid)."""
    if not isinstance(doc, dict) or doc.get("schema_version") not in SCHEMA_VERSIONS:
        return [f"unsupported schema_version {doc.get('schema_version') if isinstance(doc, dict) else None!r}"
                f" (implemented: {sorted(SCHEMA_VERSIONS)})"]
    if not isinstance(doc.get("invariants"), list):
        return ["'invariants' must be an array"]
    errors, seen = [], set()
    for n, inv in enumerate(doc["invariants"]):
        if not isinstance(inv, dict):
            errors.append(f"invariants[{n}]: not an object")
            continue
        iid = inv.get("id")
        where = f"invariants[{n}] ({iid})"
        if not isinstance(iid, str) or not re.fullmatch(r"INV-[0-9]{3}", iid):
            errors.append(f"{where}: bad id")
        elif iid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(iid)
        for field in ("description", "status", "enforceable", "scope", "source", "check"):
            if field not in inv:
                errors.append(f"{where}: missing {field}")
        status, scope, enforceable = inv.get("status"), inv.get("scope"), inv.get("enforceable")
        if status not in STATUSES:
            errors.append(f"{where}: bad status {status!r}")
        if not isinstance(scope, str) or not re.fullmatch(r"hardware|software-compat|project|emulator:[a-z0-9-]+", scope):
            errors.append(f"{where}: bad scope {scope!r}")
        if not isinstance(enforceable, bool):
            errors.append(f"{where}: enforceable must be a boolean")
        elif enforceable and not ((status == "CONFIRMED" and scope == "hardware") or status == "PROJECT-RULE"):
            errors.append(f"{where}: enforceable requires CONFIRMED+hardware or PROJECT-RULE (got {status}, {scope})")
        check = inv.get("check")
        spec = CHECKS.get(check.get("type")) if isinstance(check, dict) else None
        if spec is None:
            errors.append(f"{where}: unknown check type {check.get('type') if isinstance(check, dict) else check!r}")
            continue
        missing = [p for p in spec[0] if p not in check]
        if missing:
            errors.append(f"{where}: check missing {', '.join(missing)}")
        elif check["type"] == "bytes_not_in" and any(len(s) != check["length"] for s in check["ascii_values"]):
            errors.append(f"{where}: bytes_not_in value not exactly {check['length']} bytes")
    return errors


def builtin_invariants(config):
    def inv(id_, check):
        return {"id": id_, "status": "PROJECT-RULE", "enforceable": True, "scope": "project", "check": check}
    return [
        inv("BUILD-size-matches-config", {"type": "size_equals", "bytes": config["rom_size"]}),
        inv("M68K-initial-ssp-even", {"type": "u32_even", "offset": 0}),
        inv("M68K-initial-pc-even", {"type": "u32_even", "offset": 4}),
    ]


def evaluate(rom, inv):
    check = inv["check"]
    try:
        return CHECKS[check["type"]][1](rom, check)
    except OutOfRange as e:
        return False, str(e)


def run_checks(rom, invariants):
    """Return a list of (result, id, detail); result is PASS/FAIL (enforced) or SKIP (advisory).

    invariants must already be schema-valid (see schema_errors)."""
    results = []
    for inv in invariants:
        ok, detail = evaluate(rom, inv)
        tag = f"[{inv['status']}, {inv['scope']}, enforceable={str(inv['enforceable']).lower()}]"
        if inv["enforceable"]:
            results.append(("PASS" if ok else "FAIL", inv["id"], f"{tag} {detail}"))
        else:
            results.append(("SKIP", inv["id"], f"{tag} advisory {'ok' if ok else 'WARNING mismatch'}: {detail}"))
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("rom")
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--invariants", default=DEFAULT_INVARIANTS)
    a = p.parse_args(argv)
    with open(a.config) as f:
        config = json.load(f)
    try:
        with open(a.rom, "rb") as f:
            rom = f.read()
    except OSError as e:
        print(f"FAIL  rom-file-readable: {e}")
        return 1
    extra = []
    if os.path.exists(a.invariants):
        try:
            with open(a.invariants, encoding="utf-8") as f:
                doc = json.load(f)
        except ValueError as e:
            doc, errors = None, [f"invalid JSON: {e}"]
        else:
            errors = schema_errors(doc)
        if errors:
            print(f"FAIL  invariants file {a.invariants} is malformed:")
            for e in errors:
                print(f"      {e}")
            return 1
        extra = doc["invariants"]
    print(f"invariants file: {a.invariants if extra else 'none (built-in checks only)'}")
    results = run_checks(rom, builtin_invariants(config) + extra)
    for r, iid, detail in results:
        print(f"{r:5} {iid}: {detail}")
    failed = sum(r == "FAIL" for r, _, _ in results)
    skipped = sum(r == "SKIP" for r, _, _ in results)
    print(f"{len(results)} checks, {failed} failed, {skipped} skipped (not enforced)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
