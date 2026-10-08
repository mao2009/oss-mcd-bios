#!/usr/bin/env python3
"""Source architecture rules checker (Python stdlib only).

Usage: python -I -B tools/arch/arch_check.py [--root DIR] [--rules FILE]

Exit codes: 0 = no violation detected, 1 = violation(s), 2 = rules or git
could not be read/validated (fail closed).

This is a textual check of include/incbin directives and build-script path
references; it does not understand macros, assembler search paths or
computed paths. See docs/architecture-rules.md.
"""
import argparse
import fnmatch
import posixpath
import re
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath

DEFAULT_RULES = "arch/rules.toml"
# Optional label, optional dot, directive, then the (optionally quoted) path.
INCLUDE_RE = re.compile(
    r"""^[ \t]*(?:[A-Za-z_.@][\w.@]*:?[ \t]+)?\.?(?:include|incbin|binclude)[ \t]+["'<]?([^"'>\s;,]+)""",
    re.IGNORECASE | re.MULTILINE,
)
RELATIVE_RE = re.compile(r"(?<![\w./-])((?:\.\./)+[\w./-]+)")
MAKE_VAR_RE = re.compile(r"^(?:override\s+|export\s+)?([A-Za-z_][\w.]*)\s*(\?=|::=|:=|\+=|=)\s*(.*)$")
MAKE_REF_RE = re.compile(r"\$[({]([A-Za-z_][\w.]*)[)}]")
AUTO_VAR_RE = re.compile(r"\$[@<^?*+|]")
LD_INPUT_RE = re.compile(r"\b(?:INPUT|GROUP|INCLUDE|STARTUP)\b\s*\(?([^)\n]*)")
TOKEN_SPLIT_RE = re.compile(r"[\s\"'=,;()]+")


class RulesError(Exception):
    """Rules or repository state cannot be evaluated: fail closed."""


def load_rules(path):
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise RulesError(f"cannot read rules {path}: {e}") from e
    try:
        if data["version"] != 1:
            raise RulesError(f"unsupported rules version {data['version']!r}")
        layers, allow, rom, scan = data["layers"], data["allow"], data["rom"], data["scan"]
        rules = {
            "layers": layers,
            "allow": allow,
            "rom_layers": rom["layers"],
            "unassigned": rom["unassigned_deny"],
            "forbidden": [re.compile(p, re.IGNORECASE) for p in rom["forbidden_patterns"]],
            "assembly": scan["assembly"],
            "build": scan["build_scripts"],
            "rom_makefiles": data["rom_build"]["makefiles"],
            "rom_targets": data["rom_build"]["targets"],
            "rom_tools": data["rom_build"]["tools"],
        }
    except (KeyError, TypeError) as e:
        raise RulesError(f"rules {path} are missing or malformed: {e}") from e
    except re.error as e:
        raise RulesError(f"invalid forbidden pattern: {e}") from e
    for name, pats in layers.items():
        if not isinstance(pats, list) or not all(isinstance(p, str) and "*" in p for p in pats):
            raise RulesError(f"layer {name!r} must be a list of glob strings")
    for key in ("rom_makefiles", "rom_targets", "rom_tools"):
        if not isinstance(rules[key], list) or not all(isinstance(p, str) and p for p in rules[key]):
            raise RulesError(f"[rom_build] {key} must be a list of non-empty strings")
    if set(allow) != set(layers):
        raise RulesError("[allow] must have exactly one entry per layer")
    referenced = {d for deps in allow.values() for d in deps} | set(rules["rom_layers"])
    if not referenced <= set(layers):
        raise RulesError(f"unknown layers referenced: {sorted(referenced - set(layers))}")
    return rules


def tracked_files(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise RulesError(f"git ls-files failed: {e}") from e
    return [p for p in out.stdout.decode("utf-8", "surrogateescape").split("\0") if p]


def matches(path, pats):
    return any(fnmatch.fnmatchcase(path, p) for p in pats)


def layer_of(path, layers):
    for name, pats in layers.items():
        if matches(path, pats):
            return name
    return None


def escapes(path):
    return path == ".." or path.startswith(("../", "/"))


def parse_makefile(text):
    """Minimal make model: {name: value} variables and a list of
    (targets, prerequisites, recipe lines, source line) rules (unexpanded)."""
    text = re.sub(r"\\\r?\n", " ", text)
    variables, rules, current = {}, [], None
    for line in text.splitlines():
        if line.startswith("\t"):
            if current is not None:
                current[2].append(line.strip())
            continue
        line = line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        m = MAKE_VAR_RE.match(line)
        if m:
            name, op, value = m.groups()
            if op == "+=":
                variables[name] = variables.get(name, "") + " " + value
            elif not (op == "?=" and name in variables):
                variables[name] = value
            current = None
            continue
        targets, sep, prereqs = line.partition(":")
        if not sep or targets.strip().startswith(".") or MAKE_VAR_RE.match(prereqs.lstrip(":").strip()):
            current = None
            continue
        current = (targets, prereqs.lstrip(":").replace("|", " "), [], line)
        rules.append(current)
    return variables, rules


def make_expand(text, variables):
    for _ in range(20):
        new = MAKE_REF_RE.sub(lambda m: variables.get(m.group(1), ""), text)
        if new == text:
            break
        text = new
    return AUTO_VAR_RE.sub(" ", text.replace("$$", ""))


def path_tokens(text):
    for tok in TOKEN_SPLIT_RE.split(text):
        tok = re.sub(r"^-[ITL]", "", tok)
        if tok and not tok.startswith("-"):
            yield tok


def check_rom_build(root, rules, files, known, dirs):
    """Walk the dependency closure of the configured ROM targets. Every tracked
    file or directory reached must be in a ROM layer or an approved build-tool
    path, and must not name an emulator."""
    layers, rom, tools = rules["layers"], set(rules["rom_layers"]), rules["rom_tools"]
    violations = []

    def text_of(path):
        try:
            return (root / path).read_bytes().decode("utf-8", "replace")
        except OSError as e:
            raise RulesError(f"cannot read tracked file {path}: {e}") from e

    def forbidden(where, text):
        for pat in rules["forbidden"]:
            m = pat.search(text)
            if m:
                violations.append(f"{where}: emulator-specific reference {m.group(0)!r} in ROM build input")

    # The repository's pinned toolchain Makefile derives the executable prefix
    # with this one literal $(shell) expression. Never execute shell commands
    # during a static analysis. Resolve only this exact syntax by reading the
    # tracked, approved lock file; arbitrary make functions stay fail-closed.
    locked_target_expr = "$(shell sed -n 's/^target=//p' tools/build/toolchain.lock | tr -d '\\r')"

    def expand_locked_target(text):
        if locked_target_expr not in text:
            return text
        path = "tools/build/toolchain.lock"
        if path not in files or not matches(path, tools):
            violations.append(f"{path}: compiler target expression requires an approved tracked lock file")
            return text
        targets = [line.removeprefix("target=") for line in text_of(path).splitlines() if line.startswith("target=")]
        if len(targets) != 1 or not re.fullmatch(r"[a-z][a-z0-9-]*", targets[0]):
            violations.append(f"{path}: expected one valid pinned compiler target")
            return text
        return text.replace(locked_target_expr, targets[0])

    for mf in rules["rom_makefiles"]:
        if mf not in files:
            continue  # no build entry point yet
        mdir = posixpath.dirname(mf)
        mtext = text_of(mf)
        if re.search(r"^\s*-?s?include\s", mtext, re.MULTILINE):
            violations.append(f"{mf}: makefile include directives are not analyzed (fail closed)")
        variables, mrules = parse_makefile(mtext)
        explicit, patterns = {}, []
        for targets, prereqs, recipe, line in mrules:
            entry = (make_expand(prereqs, variables).split(), recipe, line)
            for t in make_expand(targets, variables).split():
                (patterns.append((t, entry)) if "%" in t else explicit.setdefault(t, []).append(entry))

        def rule_entries(node):
            if node in explicit:
                return explicit[node]
            for pat, (pre, recipe, line) in patterns:
                head, _, tail = pat.partition("%")
                if node.startswith(head) and node.endswith(tail) and len(node) >= len(head) + len(tail):
                    stem = node[len(head):len(node) - len(tail)]
                    return [([p.replace("%", stem) for p in pre], recipe, line)]
            return []

        def classify(where, path, is_dir):
            probe = path + "/" if is_dir else path
            layer = layer_of(probe, layers)
            if layer not in rom and not matches(probe, tools):
                violations.append(f"{where}: ROM build depends on {path} ({layer or 'unlayered'})")
                return False
            return True

        missing = [t for t in rules["rom_targets"] if not rule_entries(t)]
        if missing:
            violations.append(f"{mf}: ROM target(s) {missing} not defined (cannot verify ROM inputs)")
        seen, queue = set(), list(rules["rom_targets"])
        while queue:
            node = queue.pop()
            if node in seen:
                continue
            seen.add(node)
            path = posixpath.normpath(posixpath.join(mdir, node))
            if path in files and not escapes(path):
                if classify(f"{mf}: {node}", path, False) and layer_of(path, layers) not in rom:
                    text = text_of(path)
                    forbidden(path, text)
                    if fnmatch.fnmatchcase(posixpath.basename(path), "*.ld*"):
                        for arg in LD_INPUT_RE.findall(text):
                            queue.extend(path_tokens(arg))
                continue
            entries = rule_entries(node)
            if not entries:
                violations.append(f"{mf}: ROM prerequisite {node!r} is neither a tracked file nor a target")
                continue
            for pre, recipe, line in entries:
                queue.extend(pre)
                raw = "\n".join([line, *recipe])
                body = expand_locked_target(make_expand(raw, variables))
                forbidden(f"{mf}: rule {line.strip()!r}", raw + "\n" + body)
                if "$(" in body or "${" in body:
                    violations.append(f"{mf}: rule {line.strip()!r} uses make functions the checker cannot analyze")
                for tok in path_tokens(expand_locked_target(make_expand("\n".join(recipe), variables))):
                    p = posixpath.normpath(posixpath.join(mdir, tok))
                    if p in files or p in dirs:
                        classify(f"{mf}: recipe of {line.strip()!r}", p, p in dirs)
    return violations


def references(path, text, rules, known):
    """Yield (raw reference, repo-relative target).

    Assembly: tried relative to the repository root first (GNU as searches the
    current directory, i.e. where the top-level make runs), then relative to
    the including file. -I search directories are NOT consulted.
    Build scripts: tried relative to the script's directory, then the root."""
    name = posixpath.basename(path)
    here = posixpath.dirname(path)
    if matches(name, rules["assembly"]):
        for raw in dict.fromkeys(INCLUDE_RE.findall(text)):
            cands = [posixpath.normpath(raw), posixpath.normpath(posixpath.join(here, raw))]
            inside = [c for c in cands if not escapes(c)]
            yield raw, next((c for c in cands if c in known), (inside or cands)[0])
        return
    elif matches(name, rules["build"]):
        roots = {p.split("*", 1)[0] for pats in rules["layers"].values() for p in pats}
        root_re = "|".join(re.escape(r) for r in sorted(roots) if r)
        raws = RELATIVE_RE.findall(text)
        if root_re:
            raws += re.findall(rf"(?<![\w./-])((?:{root_re})[\w./-]*)", text)
    else:
        return
    for raw in dict.fromkeys(raws):
        cands = [posixpath.normpath(posixpath.join(here, raw))]
        if not raw.startswith("."):
            cands.append(posixpath.normpath(raw))
        yield raw, next((c for c in cands if c in known), cands[0])


def check(root, rules_path):
    root = Path(root)
    rules = load_rules(rules_path)
    files = tracked_files(root)
    dirs = {str(p) for f in files for p in PurePosixPath(f).parents} - {"."}
    known = set(files) | dirs  # build scripts may reference directories (e.g. -I src/hw)
    layers, rom = rules["layers"], set(rules["rom_layers"])
    violations = []

    for path in files:
        src = layer_of(path, layers)
        if src is None:
            if matches(path, rules["unassigned"]):
                violations.append(f"{path}: not assigned to any layer (default deny)")
            continue
        try:
            text = (root / path).read_bytes().decode("utf-8", "replace")
        except OSError as e:
            raise RulesError(f"cannot read tracked file {path}: {e}") from e

        if src in rom:
            for pat in rules["forbidden"]:
                m = pat.search(text)
                if m:
                    line = text.count("\n", 0, m.start()) + 1
                    violations.append(f"{path}:{line}: emulator-specific reference {m.group(0)!r} in ROM layer")

        for raw, target in references(path, text, rules, known):
            if escapes(target):
                violations.append(f"{path}: reference {raw!r} escapes the repository")
            elif target not in known:
                violations.append(f"{path}: reference {raw!r} does not resolve to a tracked file")
            else:
                dst = layer_of(target + "/" if target in dirs else target, layers)
                if dst == src:
                    continue
                if dst is None:
                    if src in rom:
                        violations.append(f"{path}: ROM layer '{src}' depends on unlayered {target}")
                elif dst not in rules["allow"][src]:
                    violations.append(f"{path}: forbidden dependency {src} -> {dst} ({target})")
    return violations + check_rom_build(root, rules, set(files), known, dirs)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--rules", default=None)
    args = ap.parse_args(argv)
    rules = args.rules or str(Path(args.root) / DEFAULT_RULES)
    try:
        violations = check(args.root, rules)
    except RulesError as e:
        print(f"ARCH RULES ERROR (fail closed): {e}", file=sys.stderr)
        return 2
    for v in violations:
        print(f"VIOLATION: {v}", file=sys.stderr)
    if violations:
        print(f"architecture check FAILED: {len(violations)} violation(s)", file=sys.stderr)
        return 1
    print("architecture check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
