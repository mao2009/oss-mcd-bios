"""Structural ROM validator (Python stdlib only).

Usage: python3 -I tools/rom/validate.py ROM [--config tools/rom/rom-config.json]
                                             [--invariants docs/specifications/invariants.json]

Checks are plain dicts: {"id": str, "kind": str, "status": str, ...params}.
Only checks with status "CONFIRMED" are enforced; anything else is reported as SKIP.
Numeric params may be ints or strings such as "0x1FE".

Built-in checks are toolchain/CPU-level facts only (file readable, size matches the
build config, 68000 initial SSP/PC readable as big-endian longwords and even).
Mega-CD ROM-layout facts come only from the invariants file, if it exists.

Supported kinds:
  size_equals   size
  min_size      size
  u32_be_even   offset
  u32_be_equals offset, value
  u16_be_equals offset, value
  bytes_equal   offset, hex
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CONFIG = os.path.join(ROOT, "tools", "rom", "rom-config.json")
DEFAULT_INVARIANTS = os.path.join(ROOT, "docs", "specifications", "invariants.json")


def _num(v):
    return int(v, 0) if isinstance(v, str) else int(v)


def _read(rom, offset, n):
    if offset < 0 or offset + n > len(rom):
        raise ValueError(f"offset {offset:#x}+{n} outside {len(rom)}-byte image")
    return rom[offset:offset + n]


def _u(rom, check, n):
    return int.from_bytes(_read(rom, _num(check["offset"]), n), "big")


KINDS = {
    "size_equals": lambda rom, c: (len(rom) == _num(c["size"]), f"size {len(rom)}, expected {_num(c['size'])}"),
    "min_size": lambda rom, c: (len(rom) >= _num(c["size"]), f"size {len(rom)}, minimum {_num(c['size'])}"),
    "u32_be_even": lambda rom, c: (_u(rom, c, 4) % 2 == 0, f"value {_u(rom, c, 4):#010x}"),
    "u32_be_equals": lambda rom, c: (_u(rom, c, 4) == _num(c["value"]), f"value {_u(rom, c, 4):#010x}, expected {_num(c['value']):#010x}"),
    "u16_be_equals": lambda rom, c: (_u(rom, c, 2) == _num(c["value"]), f"value {_u(rom, c, 2):#06x}, expected {_num(c['value']):#06x}"),
    "bytes_equal": lambda rom, c: (
        _read(rom, _num(c["offset"]), len(bytes.fromhex(c["hex"]))) == bytes.fromhex(c["hex"]),
        f"expected {c['hex']}"),
}


def builtin_checks(config):
    return [
        {"id": "build-config-size", "kind": "size_equals", "size": config["rom_size"], "status": "CONFIRMED",
         "note": "matches the build config; the config value itself is " + config.get("rom_size_status", "UNVERIFIED")},
        {"id": "m68k-initial-ssp-readable-even", "kind": "u32_be_even", "offset": 0, "status": "CONFIRMED"},
        {"id": "m68k-initial-pc-readable-even", "kind": "u32_be_even", "offset": 4, "status": "CONFIRMED"},
    ]


def load_invariants(path):
    """Return the check list from an invariants file, or [] if it does not exist."""
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["invariants"] if isinstance(data, dict) else data


def run_checks(rom, checks):
    """Return a list of (result, id, detail) with result in PASS/FAIL/SKIP."""
    results = []
    for c in checks:
        cid = c.get("id", "<no id>")
        if c.get("status") != "CONFIRMED":
            results.append(("SKIP", cid, f"status {c.get('status')!r} is not CONFIRMED"))
            continue
        kind = KINDS.get(c.get("kind"))
        if kind is None:  # fail closed: a confirmed requirement we cannot check is not a pass
            results.append(("FAIL", cid, f"unsupported kind {c.get('kind')!r}"))
            continue
        try:
            ok, detail = kind(rom, c)
        except (KeyError, ValueError, TypeError) as e:
            ok, detail = False, f"{type(e).__name__}: {e}"
        results.append(("PASS" if ok else "FAIL", cid, detail))
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
    extra = load_invariants(a.invariants)
    print(f"invariants file: {a.invariants if extra else 'none (built-in checks only)'}")
    results = run_checks(rom, builtin_checks(config) + extra)
    for r, cid, detail in results:
        print(f"{r:5} {cid}: {detail}")
    failed = sum(r == "FAIL" for r, _, _ in results)
    print(f"{len(results)} checks, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
