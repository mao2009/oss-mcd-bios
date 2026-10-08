#!/usr/bin/env python3
"""Default-deny build-input / provenance gate (Python stdlib only).

Usage: python -I -B tools/policy/policy_check.py [--root DIR] [--policy FILE]

Exit codes: 0 = no violation detected, 1 = violation(s), 2 = policy or git
could not be read/validated (fail closed).

This is a heuristic gate. Passing it does NOT prove that the repository is
free of proprietary or unauthorized material; see docs/policy-review.md.
"""
import argparse
import fnmatch
import subprocess
import sys
import tomllib
from pathlib import Path

DEFAULT_POLICY = "policy/allowlist.toml"
ROM_SIGNATURES = (  # (offset, bytes, description)
    (0x100, b"SEGA", "Mega Drive ROM header"),
    (0x0, b"SEGADISCSYSTEM", "Mega-CD disc/boot header"),
    (0x10, b"SEGADISCSYSTEM", "Mega-CD raw-sector header"),
)


class PolicyError(Exception):
    """Policy or repository state cannot be evaluated: fail closed."""


def load_policy(path):
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise PolicyError(f"cannot read policy {path}: {e}") from e
    try:
        if data["version"] != 1:
            raise PolicyError(f"unsupported policy version {data['version']!r}")
        locations = data["locations"]
        inputs = data["inputs"]["categories"]
        denied = [e.lower() for e in data["content"]["denied_extensions"]]
        max_bytes = data["content"]["max_file_bytes"]
    except (KeyError, TypeError) as e:
        raise PolicyError(f"policy {path} is missing or malformed: {e}") from e
    if "artifact" not in locations:
        raise PolicyError("policy must define an 'artifact' location")
    for name, pats in locations.items():
        if not isinstance(pats, list) or not all(isinstance(p, str) and p for p in pats):
            raise PolicyError(f"location {name!r} must be a list of non-empty strings")
    unknown = [c for c in inputs if c not in locations]
    if unknown:
        raise PolicyError(f"inputs reference unknown locations: {unknown}")
    if not isinstance(max_bytes, int) or max_bytes <= 0:
        raise PolicyError("content.max_file_bytes must be a positive integer")
    return {"locations": locations, "inputs": inputs, "denied": denied, "max_bytes": max_bytes}


def git(root, *args):
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise PolicyError(f"git {' '.join(args)} failed: {e}") from e
    return [p for p in out.stdout.decode("utf-8", "surrogateescape").split("\0") if p]


def category(path, locations):
    for name, pats in locations.items():
        if any(fnmatch.fnmatchcase(path, p) for p in pats):
            return name
    return None


def content_problem(data, max_bytes):
    if len(data) > max_bytes:
        return f"file larger than {max_bytes} bytes"
    if b"\0" in data:
        why = "NUL byte"
    else:
        try:
            data.decode("utf-8")
            return None
        except UnicodeDecodeError:
            why = "not valid UTF-8"
    for off, sig, desc in ROM_SIGNATURES:
        if data[off:off + len(sig)] == sig:
            return f"ROM-like content ({desc} at 0x{off:X})"
    return f"binary content ({why})"


def check(root, policy_path):
    root = Path(root)
    policy = load_policy(policy_path)
    locs = policy["locations"]
    violations = []

    staged = git(root, "ls-files", "-s", "-z")
    tracked = {e.split("\t", 1)[1] for e in staged}
    try:
        policy_rel = Path(policy_path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        policy_rel = None
    if policy_rel not in tracked:
        raise PolicyError(f"policy {policy_path} must be a tracked file inside the repository")
    for entry in staged:
        meta, path = entry.split("\t", 1)
        mode = meta.split()[0]
        cat = category(path, locs)
        if mode in ("120000", "160000"):
            violations.append(f"{path}: symlinks/submodules are not allowed")
            continue
        if cat is None:
            violations.append(f"{path}: not in any allowed location (default deny)")
            continue
        if cat == "artifact":
            violations.append(f"{path}: build artifacts must not be tracked")
            continue
        if Path(path).suffix.lower() in policy["denied"]:
            violations.append(f"{path}: denied extension {Path(path).suffix}")
            continue
        try:
            data = (root / path).read_bytes()
        except OSError as e:
            raise PolicyError(f"cannot read tracked file {path}: {e}") from e
        problem = content_problem(data, policy["max_bytes"])
        if problem:
            violations.append(f"{path}: {problem}")

    for path in git(root, "ls-files", "--others", "-z"):  # includes ignored files
        if category(path, locs) in policy["inputs"]:
            violations.append(f"{path}: untracked/ignored file in a build-input location")

    for path in git(root, "diff", "--name-only", "-z", "HEAD"):
        if category(path, locs) in policy["inputs"] or path == policy_rel:
            violations.append(f"{path}: uncommitted modification to a build input or policy")
    return violations


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--policy", default=None)
    args = ap.parse_args(argv)
    policy = args.policy or str(Path(args.root) / DEFAULT_POLICY)
    try:
        violations = check(args.root, policy)
    except PolicyError as e:
        print(f"POLICY ERROR (fail closed): {e}", file=sys.stderr)
        return 2
    for v in violations:
        print(f"VIOLATION: {v}", file=sys.stderr)
    if violations:
        print(f"policy check FAILED: {len(violations)} violation(s)", file=sys.stderr)
        return 1
    print("policy check passed (heuristic only; not proof of provenance)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
