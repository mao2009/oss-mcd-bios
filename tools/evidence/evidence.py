#!/usr/bin/env python3
"""Machine-readable compatibility evidence: synthetic fixture, collector,
validator, aggregator and docs/compatibility.md matrix generator.

Python stdlib only; run as ``python -I tools/evidence/evidence.py <command>``.
Record format: tools/evidence/result.schema.json (validate() mirrors it).

Aggregation rules (fail closed):
- Only an explicit, valid PASS record makes a cell PASS. SKIP, BLOCKED,
  UNTESTED and invalid records are never success; invalid records count as FAIL.
- Stages are independent: a rom-built PASS never implies any runtime stage.
- A runtime PASS needs observed state and a pinned emulator sha (validate()).
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import platform
import re
import socket
import struct
import sys
from pathlib import Path

SCHEMA_VERSION = 1
STATUSES = ("PASS", "FAIL", "SKIP", "BLOCKED")
CHECKPOINTS = (
    "rom-built", "bios-loaded", "startup", "disc-detected",
    "homebrew-boot", "game-boot", "playable", "completion-tested",
)
REQUIRED = ("schema_version", "status", "checkpoint", "rom_sha256", "rom_commit",
            "emulator", "environment", "observed", "log_excerpt", "reason")
LOG_MAX_CHARS = 4096
LOG_MAX_LINES = 40
BEGIN_MARK = "<!-- BEGIN GENERATED: compat-matrix (tools/evidence/evidence.py matrix; do not edit by hand) -->"
END_MARK = "<!-- END GENERATED: compat-matrix -->"
DEFAULT_RECORDS = Path(__file__).resolve().parent / "records"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GITSHA = re.compile(r"^[0-9a-f]{7,40}$")
_EMU_SHA = re.compile(r"^[0-9a-f]{7,64}$")
_EMU_ID = re.compile(r"^[a-z0-9][a-z0-9:._-]*$")


# --- synthetic fixture -------------------------------------------------------

FIXTURE_SIZE = 0x20000  # 128 KiB
FIXTURE_MARKER = b"OSS-MCD-BIOS SYNTHETIC FIXTURE v1"


def synthetic_rom() -> bytes:
    """Deterministic, proprietary-free m68k image for testing the tooling.

    Original content only: a vector table (SSP, reset PC, every other vector to
    a trap loop), an ASCII marker at 0x100 and two tiny code stubs. It is NOT a
    claim about the verified Mega-CD BIOS layout (issue #1).
    """
    rom = bytearray(FIXTURE_SIZE)
    struct.pack_into(">II", rom, 0, 0x00FFFD00, 0x00000200)  # SSP, reset PC
    for vector in range(2, 64):
        struct.pack_into(">I", rom, vector * 4, 0x00000208)
    rom[0x100:0x100 + len(FIXTURE_MARKER)] = FIXTURE_MARKER
    rom[0x200:0x206] = bytes.fromhex("46FC2700" "60FE")  # move.w #$2700,sr; bra.s *
    rom[0x208:0x20A] = bytes.fromhex("60FE")              # exception: bra.s *
    return bytes(rom)


# --- sanitizer ---------------------------------------------------------------

_AUTH_HEADER = re.compile(r"(?i)\b((?:proxy-)?authorization)\s*[:=].*")
_BEARER = re.compile(r"(?i)\b(bearer|basic)\s+\S+")
_URL_CREDS = re.compile(r"\b([a-z][a-z0-9+.-]*://)[^\s/@]+@")
# Well-known token shapes: GitHub, GitLab, Slack, AWS access key ids.
_TOKEN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_\w{16,}|glpat-[\w-]{16,}|xox[abprs]-[\w-]{10,}|AKIA[0-9A-Z]{16})\b")
_SECRET = re.compile(r"(?i)\b(\w*(?:token|password|passwd|secret|api[_-]?key))(\s*[:=]\s*)\S+")
_WIN_PATH = re.compile(r"\b[A-Za-z]:[\\/][^\s'\"]*|\\\\[\w.$-]+\\[^\s'\"]*")
# Any absolute POSIX path with 2+ components (/__w, /srv, /workspace, /home ...), or ~/...; /dev/* is kept.
_POSIX_PATH = re.compile(r"(?<![\w.:/~-])(?:/(?!dev/)[\w.@+-]+/[^\s'\"]*|~/[^\s'\"]*)")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def sanitize(text: str) -> str:
    """Return a minimal log tail without secrets, paths, user or host names."""
    text = _CONTROL.sub("", text.replace("\r\n", "\n"))
    text = _AUTH_HEADER.sub(r"\1: <redacted>", text)
    text = _BEARER.sub(r"\1 <redacted>", text)
    text = _URL_CREDS.sub(r"\1<redacted>@", text)
    text = _TOKEN.sub("<redacted>", text)
    text = _SECRET.sub(r"\1\2<redacted>", text)
    text = _WIN_PATH.sub("<path>", text)
    text = _POSIX_PATH.sub("<path>", text)
    for value, label in ((_safe(getpass.getuser), "<user>"), (_safe(socket.gethostname), "<host>")):
        if value and len(value) >= 3:
            text = re.sub(re.escape(value), label, text, flags=re.IGNORECASE)
    lines = text.strip("\n").split("\n")[-LOG_MAX_LINES:]
    return "\n".join(lines)[-LOG_MAX_CHARS:]


def _safe(fn) -> str:
    try:
        return fn()
    except Exception:  # getuser() raises without a user database
        return ""


# --- record construction and validation -------------------------------------

def make_record(status, checkpoint, *, rom_sha256=None, rom_commit=None, emulator_id="none",
                emulator_version=None, emulator_sha=None, environment=None, observed=None,
                log="", reason=None) -> dict:
    env = {"os": platform.system().lower() or "unknown", "arch": platform.machine().lower() or "unknown",
           "python": platform.python_version()}
    env.update(environment or {})
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "checkpoint": checkpoint,
        "rom_sha256": rom_sha256,
        "rom_commit": rom_commit,
        "emulator": {"id": emulator_id, "version": emulator_version, "sha": emulator_sha},
        "environment": env,
        "observed": observed or {},
        "log_excerpt": sanitize(log),
        "reason": reason,
    }


def validate(record) -> list[str]:
    """Return rule violations (empty list = valid). Mirrors result.schema.json."""
    if not isinstance(record, dict):
        return ["record is not an object"]
    errors = [f"missing field: {k}" for k in REQUIRED if k not in record]
    errors += [f"unknown field: {k}" for k in record if k not in REQUIRED]
    if errors:
        return errors
    status, checkpoint, emu = record["status"], record["checkpoint"], record["emulator"]
    if record["schema_version"] != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if status not in STATUSES:
        errors.append(f"status must be one of {STATUSES}")
    if checkpoint not in CHECKPOINTS:
        errors.append(f"checkpoint must be one of {CHECKPOINTS}")
    if not _nullable_match(record["rom_sha256"], _SHA256):
        errors.append("rom_sha256 must be 64 lowercase hex chars or null")
    if not _nullable_match(record["rom_commit"], _GITSHA):
        errors.append("rom_commit must be a 7-40 char lowercase git sha or null")
    if not isinstance(emu, dict) or set(emu) != {"id", "version", "sha"}:
        errors.append("emulator must have exactly id, version, sha")
        emu = {"id": None, "version": None, "sha": None}
    if not (isinstance(emu["id"], str) and _EMU_ID.match(emu["id"])):
        errors.append("emulator.id must match ^[a-z0-9][a-z0-9:._-]*$")
    if emu["version"] is not None and not isinstance(emu["version"], str):
        errors.append("emulator.version must be a string or null")
    if not _nullable_match(emu["sha"], _EMU_SHA):
        errors.append("emulator.sha must be 7-64 lowercase hex chars or null")
    env = record["environment"]
    if not (isinstance(env, dict) and {"os", "arch"} <= set(env) and all(isinstance(v, str) for v in env.values())):
        errors.append("environment must be an object of strings with os and arch")
    if not isinstance(record["observed"], dict):
        errors.append("observed must be an object")
    if not isinstance(record["log_excerpt"], str) or len(record["log_excerpt"]) > LOG_MAX_CHARS:
        errors.append(f"log_excerpt must be a string of at most {LOG_MAX_CHARS} chars")
    reason = record["reason"]
    if reason is not None and not isinstance(reason, str):
        errors.append("reason must be a string or null")
    if errors:
        return errors
    # Semantic rules (schema allOf).
    if status != "PASS" and not reason:
        errors.append(f"{status} requires a non-empty reason")
    if status == "PASS" and record["rom_sha256"] is None:
        errors.append("PASS requires rom_sha256")
    if checkpoint == "rom-built" and emu["id"] != "none":
        errors.append("rom-built records must use emulator.id 'none'")
    if checkpoint != "rom-built" and emu["id"] == "none":
        errors.append("runtime checkpoints need an emulator or hardware:<model> id (build-only is not a boot)")
    if status == "PASS" and checkpoint != "rom-built":
        if not record["observed"]:
            errors.append("runtime PASS requires observed state")
        if not emu["id"].startswith("hardware:") and emu["sha"] is None:
            errors.append("runtime PASS on an emulator requires a pinned emulator.sha")
    return errors


def _nullable_match(value, pattern) -> bool:
    return value is None or (isinstance(value, str) and bool(pattern.match(value)))


# --- aggregation and matrix --------------------------------------------------

_PRECEDENCE = ("FAIL", "PASS", "BLOCKED", "SKIP")  # first present wins; none -> UNTESTED


def load_records(paths) -> list[tuple[str, object]]:
    """Return (label, parsed-or-None) for every *.json under the given paths."""
    out = []
    for p in map(Path, paths):
        files = sorted(p.rglob("*.json")) if p.is_dir() else [p] if p.exists() else []
        for f in files:
            try:
                out.append((f.name, json.loads(f.read_text(encoding="utf-8"))))
            except (OSError, ValueError):
                out.append((f.name, None))
    return out


def aggregate(records) -> dict:
    """records: iterable of (label, record). Returns a deterministic summary."""
    seen: dict[tuple[str, str], set[str]] = {}
    invalid = []
    for label, rec in records:
        errors = validate(rec) if rec is not None else ["unreadable JSON"]
        if errors:
            invalid.append({"record": label, "errors": errors})
            # Fail closed: attribute to its cell when identifiable, else to rom-built/none.
            cp = rec.get("checkpoint") if isinstance(rec, dict) else None
            emu = rec.get("emulator") if isinstance(rec, dict) else None
            emu_id = emu.get("id") if isinstance(emu, dict) else None
            key = (cp if cp in CHECKPOINTS else "rom-built", emu_id if isinstance(emu_id, str) else "none")
            seen.setdefault(key, set()).add("FAIL")
            continue
        seen.setdefault((rec["checkpoint"], rec["emulator"]["id"]), set()).add(rec["status"])
    emulators = sorted({emu for _, emu in seen}, key=lambda e: (e != "none", e))  # build column first
    cells = {cp: {emu: next((s for s in _PRECEDENCE if s in seen.get((cp, emu), ())), "UNTESTED")
                  for emu in emulators} for cp in CHECKPOINTS}
    counts = {s: 0 for s in (*_PRECEDENCE, "UNTESTED")}
    for row in cells.values():
        for status in row.values():
            counts[status] += 1
    return {"emulators": emulators, "cells": cells, "counts": counts,
            "success_cells": counts["PASS"], "invalid": invalid}


def render_matrix(summary: dict) -> str:
    emus = summary["emulators"]
    if not emus:  # no records at all (invalid records still create a FAIL cell)
        return ("_No evidence records yet: every stage is UNTESTED (no record); nothing is claimed as supported._\n\n"
                "Only PASS is success; SKIP, BLOCKED and UNTESTED are not.")
    head = "| Stage | " + " | ".join("build (no emulator)" if e == "none" else e for e in emus) + " |"
    sep = "| --- |" + " --- |" * len(emus)
    rows = [f"| {cp} | " + " | ".join(summary["cells"][cp][e] for e in emus) + " |" for cp in CHECKPOINTS]
    body = "\n".join([head, sep, *rows])
    c = summary["counts"]
    note = (f"Cells: PASS {c['PASS']}, FAIL {c['FAIL']}, BLOCKED {c['BLOCKED']}, SKIP {c['SKIP']}, "
            f"UNTESTED {c['UNTESTED']}; invalid records {len(summary['invalid'])}. "
            "Only PASS is success; SKIP, BLOCKED and UNTESTED are not.")
    return f"{body}\n\n{note}"


def update_doc(text: str, matrix: str) -> str:
    """Replace only the marked generated section; refuse if markers are missing."""
    start, end = text.find(BEGIN_MARK), text.find(END_MARK)
    if start < 0 or end < start or text.count(BEGIN_MARK) != 1 or text.count(END_MARK) != 1:
        raise ValueError("generated-section markers missing or duplicated")
    return text[:start + len(BEGIN_MARK)] + "\n" + matrix + "\n" + text[end:]


# --- CLI ---------------------------------------------------------------------

def _cmd_fixture(a):
    data = synthetic_rom()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_bytes(data)
    print(hashlib.sha256(data).hexdigest())
    return 0


def _cmd_collect(a):
    rom_sha = a.rom_sha256 or (hashlib.sha256(Path(a.rom).read_bytes()).hexdigest() if a.rom else None)
    observed = json.loads(Path(a.observed[1:]).read_text(encoding="utf-8") if a.observed.startswith("@") else a.observed)
    env = dict(kv.split("=", 1) for kv in a.env)
    log = Path(a.log).read_text(encoding="utf-8", errors="replace") if a.log else ""
    rec = make_record(a.status, a.checkpoint, rom_sha256=rom_sha, rom_commit=a.rom_commit,
                      emulator_id=a.emulator_id, emulator_version=a.emulator_version,
                      emulator_sha=a.emulator_sha, environment=env, observed=observed, log=log, reason=a.reason)
    errors = validate(rec)
    if errors:
        print("invalid record, not written:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 2
    text = json.dumps(rec, indent=2, sort_keys=True) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_validate(a):
    missing = [p for p in a.paths if not Path(p).exists()]
    records = load_records(a.paths)
    for p in missing:
        print(f"BAD {p}: path does not exist")
    if not records:
        print("BAD no *.json records found (zero validated records is not success)")
        return 1
    bad = len(missing)
    for label, rec in records:
        errors = validate(rec) if rec is not None else ["unreadable JSON"]
        if not errors and a.emulator_prefix and not rec["emulator"]["id"].startswith(a.emulator_prefix):
            errors = [f"emulator.id must start with {a.emulator_prefix!r}"]
        print(f"{'OK ' if not errors else 'BAD'} {label}" + "".join(f"\n    {e}" for e in errors))
        bad += bool(errors)
    return 1 if bad else 0


def _cmd_aggregate(a):
    summary = aggregate(load_records(a.paths))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if a.fail_on_fail and summary["counts"]["FAIL"] else 0


def _cmd_matrix(a):
    matrix = render_matrix(aggregate(load_records(a.paths or [DEFAULT_RECORDS])))
    if not a.doc:
        print(matrix)
        return 0
    doc = Path(a.doc)
    old = doc.read_text(encoding="utf-8")
    new = update_doc(old, matrix)
    if a.check:
        if new != old:
            print(f"{doc} generated section is stale; run: python -I tools/evidence/evidence.py matrix --doc {doc}",
                  file=sys.stderr)
            return 1
        return 0
    doc.write_text(new, encoding="utf-8", newline="\n")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fixture", help="write the synthetic m68k fixture; prints its sha256")
    f.add_argument("--out", required=True)
    c = sub.add_parser("collect", help="build, validate and write one evidence record")
    c.add_argument("--status", required=True, choices=STATUSES)
    c.add_argument("--checkpoint", required=True, choices=CHECKPOINTS)
    rom = c.add_mutually_exclusive_group()
    rom.add_argument("--rom", help="ROM image path (sha256 computed; path not recorded)")
    rom.add_argument("--rom-sha256")
    c.add_argument("--rom-commit")
    c.add_argument("--emulator-id", default="none")
    c.add_argument("--emulator-version")
    c.add_argument("--emulator-sha")
    c.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    c.add_argument("--observed", default="{}", help="JSON object or @file")
    c.add_argument("--log", help="log file; only a sanitized tail is kept")
    c.add_argument("--reason")
    c.add_argument("--out")
    v = sub.add_parser("validate", help="validate record files/directories")
    v.add_argument("paths", nargs="+")
    v.add_argument("--emulator-prefix", help="also require emulator.id to start with this (e.g. hardware:)")
    g = sub.add_parser("aggregate", help="print the JSON summary")
    g.add_argument("paths", nargs="+")
    g.add_argument("--fail-on-fail", action="store_true")
    m = sub.add_parser("matrix", help="render the matrix or update a doc's generated section")
    m.add_argument("paths", nargs="*", help=f"record files/dirs (default: {DEFAULT_RECORDS.name}/ next to this script)")
    m.add_argument("--doc")
    m.add_argument("--check", action="store_true", help="exit 1 if --doc is stale")
    a = p.parse_args(argv)
    return {"fixture": _cmd_fixture, "collect": _cmd_collect, "validate": _cmd_validate,
            "aggregate": _cmd_aggregate, "matrix": _cmd_matrix}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
