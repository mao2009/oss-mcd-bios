#!/usr/bin/env python3
"""Environment doctor: report missing or incorrect toolchain/emulator versions.

Python stdlib only; run as ``python -I tools/doctor/doctor.py [--require build,emu] [--json]``.

Pin files (owned by the build/emulator work, read only here), one tool per file:
  build -> tools/build/toolchain.lock (+ any other tools/build/*.lock)
  emu   -> tools/emu/gpgx.lock (primary target; other tools/emu/*.lock = secondary emulators)
Shared format: plain ``key=value`` lines, ``#`` comments. Keys used here:
  name         display name (default: file stem)
  version      expected installed version, compared EXACTLY to a version token in the output
  command      executable on PATH, or a repo-relative/absolute path (contains '/')
  version_cmd  command printing the version (default: "<command> --version")
  sha256 / commit / url / repo   source pins; verified by the fetch/build scripts, reported only.
Statuses (every row carries a reason; SKIP is never success):
  PASS  installed tool's version equals the pin
  FAIL  pin present but unreadable; installed version differs; version command fails;
        or tool/pin absent for a group named in --require
  SKIP  pin absent; tool not installed (group not required); or pin has no command/version,
        so the installed version is not checkable here
Exit code 1 if any row FAILs.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GROUPS = {"build": ("tools/build", "toolchain.lock", "issue #2"),
          "emu": ("tools/emu", "gpgx.lock", "issue #5")}
MIN_PYTHON = (3, 11)
_KEY = re.compile(r"^[a-z0-9_]+$")
_VERSION_TOKEN = re.compile(r"\d+(?:\.\d+)+[\w.+-]*")


def result(group, name, status, reason):
    return {"group": group, "name": name, "status": status, "reason": reason}


def load_pin(path: Path) -> dict:
    """Parse key=value lines; raise ValueError on anything malformed."""
    pin = {}
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not _KEY.match(key):
            raise ValueError(f"line {n}: expected key=value")
        if key in pin:
            raise ValueError(f"line {n}: duplicate key {key!r}")
        pin[key] = value.strip()
    if not pin:
        raise ValueError("no key=value entries")
    return pin


def check_pin(root: Path, group: str, stem: str, pin: dict, required: bool) -> dict:
    name = pin.get("name") or stem
    source = next((f"{k} {pin[k][:12]}" for k in ("version", "commit", "sha256") if pin.get(k)), "no version")
    command = pin.get("command")
    if not command:
        return result(group, name, "SKIP", f"pin ({source}) has no command key; installed version not checkable here")
    exe = str(root / command) if "/" in command else shutil.which(command)
    if not exe or not Path(exe).is_file():
        return result(group, name, "FAIL" if required else "SKIP",
                      f"{command} not installed (pinned {source})" + ("" if required else f"; optional, use --require {group}"))
    expected = pin.get("version")
    if not expected:
        return result(group, name, "SKIP", f"{command} installed but pin has no version key; version not checkable")
    args = shlex.split(pin.get("version_cmd") or f"{shlex.quote(command)} --version")
    if args and args[0] == command:
        args[0] = exe
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=20, errors="replace", cwd=root)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return result(group, name, "FAIL", f"version command failed: {exc.__class__.__name__}")
    lines = [l for l in (proc.stdout + proc.stderr).splitlines() if l.strip()]
    first = lines[0].strip() if lines else "<no output>"
    if proc.returncode != 0 or expected not in _VERSION_TOKEN.findall(first):
        return result(group, name, "FAIL", f"{command}: expected version {expected!r}, got {first!r} (exit {proc.returncode})")
    return result(group, name, "PASS", f"{command} version {expected} matches pin")


def diagnose(root: Path = ROOT, required=(), python_version=sys.version_info[:3]) -> list[dict]:
    py = ".".join(map(str, python_version))
    out = [result("host", "python", "PASS" if tuple(python_version) >= MIN_PYTHON else "FAIL",
                  f"Python {py} (need >= {'.'.join(map(str, MIN_PYTHON))})")]
    for group, (rel, primary, issue) in GROUPS.items():
        req = group in required
        if not (root / rel / primary).is_file():
            out.append(result(group, Path(primary).stem, "FAIL" if req else "SKIP", f"{rel}/{primary} absent ({issue})"))
        for pin_path in sorted((root / rel).glob("*.lock")):
            try:
                pin = load_pin(pin_path)
            except (OSError, UnicodeDecodeError, ValueError) as exc:
                out.append(result(group, pin_path.stem, "FAIL", f"{rel}/{pin_path.name} unreadable: {exc}"))
                continue
            out.append(check_pin(root, group, pin_path.stem, pin, req))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--require", default="", help="comma-separated groups whose absence is FAIL: build,emu")
    p.add_argument("--json", action="store_true")
    p.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    required = {g for g in a.require.split(",") if g}
    unknown = required - set(GROUPS)
    if unknown:
        p.error(f"unknown group(s): {', '.join(sorted(unknown))}")
    results = diagnose(a.root, required)
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(f"{r['status']:<7} {r['group']}/{r['name']}: {r['reason']}")
        counts = {s: sum(r["status"] == s for r in results) for s in ("PASS", "FAIL", "SKIP")}
        print(f"\nPASS {counts['PASS']}  FAIL {counts['FAIL']}  SKIP {counts['SKIP']} (SKIP is not success)")
    return 1 if any(r["status"] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
