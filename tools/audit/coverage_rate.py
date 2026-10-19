"""Spec-coverage matrix: build, verify and rate (stdlib only).

The consolidated table in docs/specifications/coverage-matrix.md is a verbatim
copy of the rows in docs/specifications/coverage/*.md. Two mechanical edits are
made: relative link targets are rebased one directory up, and cross-area group
tags ("[X-nn]") are appended to the ID cell. Group membership is read from the
"Cross-area overlaps and disagreements" table (Tag | Topic | Items | ...) in the
matrix itself, so that table is the single data source for the groups.

  python tools/audit/coverage_rate.py           print the rate tables
  python tools/audit/coverage_rate.py --write   regenerate both generated blocks
  python tools/audit/coverage_rate.py --check   exit 1 if the matrix is stale
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "specifications"
MATRIX = SPEC / "coverage-matrix.md"
AREAS = [  # (prefix, area label, file)
    ("ROM", "A rom-cpu-memmap", "rom-cpu-memmap.md"),
    ("COM", "B comm-wordram-irq", "comm-wordram-irq.md"),
    ("API", "C bios-api", "bios-api.md"),
    ("CD", "D cd-boot", "cd-boot.md"),
    ("PRV", "E provenance-experiments", "provenance-experiments.md"),
]
HEADER = ("| ID | Required behavior | Level | Existing material (Y/N/partial) | "
          "Exact reference URL + location | Provenance & usage terms | "
          "Implementable from public material only? (Y/Cond/N + why) | "
          "Specific missing information | Coverable by own test? | "
          "Verifiable in emulator only? | Real hardware needed? | "
          "Blocker? (Y/N + why) |")
LEVELS = ("LA", "LB", "LC")
CONFLICT = re.compile(r"unconfirmed|conflict|disagree|contradict", re.I)
# Provenance cell ("as above"/"as <ID>" expanded) records origin in the excluded
# manuals, in RE, or in an undeclared-origin source. Hand-checked: see matrix §4.
TAINT = re.compile(r"P-OFF|P-RE|P-UNK|\bRE\b|RE-derived|reverse.engineer|disassembl|"
                   r"official BIOS manual|derived from L-0|derive from XS|"
                   r"second-hand from XS|quotes official", re.I)
# Implementable cell says the item rests on excluded material.
IMPL_TAINT = re.compile(r"only via an excluded|rests on an excluded|"
                        r"origin is the excluded|attributes them to the excluded", re.I)


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_rows(text):
    """12-column rows whose first cell is an item ID (optionally tagged)."""
    rows, width, prev = [], 0, []
    for line in text.splitlines():
        if not line.startswith("| "):
            width = 0
            continue
        cells = split_row(line)
        if set(cells) == {"---"}:
            width = len(prev)  # width of the table this row belongs to
        elif width == 12 and re.fullmatch(r"[A-Z]+-\d+( \[X-\d+\])*", cells[0]):
            if len(cells) != 12:
                raise ValueError(f"{cells[0]}: {len(cells)} columns, expected 12")
            rows.append(cells)
        prev = cells
    return rows


def groups(text):
    """{tag: [IDs]} from rows "| X-nn | topic | ID, ID, ... | ... |"."""
    out = {}
    for line in text.splitlines():
        if re.match(r"\| X-\d+ \|", line):
            cells = split_row(line)
            out[cells[0]] = re.findall(r"[A-Z]+-\d+", cells[2])
    return out


def overrides(text):
    """IDs hand-checked as provenance-clean despite a TAINT hit: "| H-nn | ID | why |"."""
    return set(re.findall(r"^\s*\| H-\d+ \| ([A-Z]+-\d+) \|", text, re.M))


def item_id(row):
    return row[0].split()[0]


def area_rows(group_map):
    tags = {}
    for tag, ids in group_map.items():
        for i in ids:
            tags.setdefault(i, []).append(tag)
    out = []
    for prefix, _, name in AREAS:
        for r in table_rows((SPEC / "coverage" / name).read_text(encoding="utf-8")):
            if not r[0].startswith(prefix + "-"):
                raise ValueError(f"{name}: unexpected ID {r[0]}")
            r = [c.replace("](../", "](") for c in r]
            r[0] = " ".join([r[0]] + [f"[{t}]" for t in tags.get(r[0], [])])
            out.append(r)
    ids = [item_id(r) for r in out]
    unknown = {i for v in group_map.values() for i in v} - set(ids)
    if len(ids) != len(set(ids)) or unknown:
        raise ValueError(f"duplicate IDs or unknown grouped IDs: {unknown}")
    return out


def head(cell):
    """Leading Y / Cond / N / Partial token of a cell, ignoring bold."""
    m = re.match(r"(Y|Cond|N|partial)(?![\w/])", cell.replace("*", "").strip(), re.I)
    return m.group(1).capitalize() if m else ""


def level(row):
    return re.match(r"L[ABC]", row[2]).group(0)  # "LB/LC" counts at LB


def blocking(row):
    """Blocker cell starts with Y, or inherits a blocker ("via API-60")."""
    return head(row[11]) == "Y" or row[11].strip().startswith("via ")


def defined(row):
    """Rules 1-4 of matrix §4: defined by any cited non-excluded source."""
    material, impl, own_test = head(row[3]), head(row[6]), head(row[8])
    if impl not in ("Y", "Cond"):
        return False
    if any(CONFLICT.search(row[i]) for i in (3, 4, 5, 6)):
        return False
    if (impl == "Cond" or material != "Y") and own_test != "Y":
        return False
    return not (impl == "Cond" and blocking(row))


def provenance(rows):
    """Provenance cells with "as above" / "as <ID>" references expanded."""
    out, prev = {}, ""
    for r in rows:
        cell = r[5]
        m = re.match(r"as (above|[A-Z]+-\d+)", cell)
        if m:
            cell = (prev if m.group(1) == "above" else out.get(m.group(1), "")) + " " + cell
        out[item_id(r)] = prev = cell
    return out


def classify(rows, group_map, clean_ids=frozenset()):
    """{ID: dict(defined, clean, undisputed, y)} for every row."""
    prov = provenance(rows)
    base = {item_id(r): defined(r) for r in rows}
    out = {}
    for r in rows:
        i = item_id(r)
        members = [j for g in group_map.values() if i in g for j in g]
        out[i] = {"defined": base[i],
                  "clean": i in clean_ids or not (TAINT.search(prov[i]) or IMPL_TAINT.search(r[6])),
                  "undisputed": all(base[j] for j in members),
                  "y": head(r[6]) == "Y"}
    return out


VIEWS = [  # (title, predicate over a classify() entry)
    ("Headline: defined, provenance-clean and undisputed",
     lambda k: k["defined"] and k["clean"] and k["undisputed"]),
    ("Secondary: defined and provenance-clean (cross-area disputes ignored)",
     lambda k: k["defined"] and k["clean"]),
    ("Secondary: defined and undisputed (manual/RE-derived sources allowed)",
     lambda k: k["defined"] and k["undisputed"]),
    ("Secondary: defined by any cited source, including manual/RE-derived (lenient)",
     lambda k: k["defined"]),
    ("Secondary: headline items whose Implementable cell is Y",
     lambda k: k["defined"] and k["clean"] and k["undisputed"] and k["y"]),
]


def rates(rows, group_map, clean_ids=frozenset()):
    """{view: {scope: {level: (count, enumerated)}}}, levels cumulative."""
    cls = classify(rows, group_map, clean_ids)
    scopes = {"All areas": rows}
    for prefix, label, _ in AREAS:
        scopes[label] = [r for r in rows if item_id(r).startswith(prefix + "-")]
    out = {}
    for title, pred in VIEWS:
        out[title] = {}
        for scope, rs in scopes.items():
            out[title][scope] = {}
            for n, lv in enumerate(LEVELS):
                sel = [r for r in rs if level(r) in LEVELS[: n + 1]]
                out[title][scope][lv] = (sum(pred(cls[item_id(r)]) for r in sel), len(sel))
    return out


def pct(a, b):
    return f"{a}/{b} = {100 * a / b:.1f}%" if b else f"{a}/0: not computable"


def render_rates(rows, group_map, clean_ids=frozenset()):
    lines = []
    for title, by in rates(rows, group_map, clean_ids).items():
        lines += [f"**{title}**", "",
                  "| Scope | LA (LA items) | LB (LA+LB items) | LC (all items) |",
                  "| --- | --- | --- | --- |"]
        for scope, lv in by.items():
            lines.append(f"| {scope} | " + " | ".join(pct(*lv[x]) for x in LEVELS) + " |")
        lines.append("")
    cls = classify(rows, group_map, clean_ids)
    own = {lv: sum(level(r) == lv for r in rows) for lv in LEVELS}

    def ids(pred):
        found = [item_id(r) for r in rows if pred(cls[item_id(r)], r)]
        return f"({len(found)}): " + (", ".join(found) or "none") + "."

    lines += [f"Items enumerated by minimum level: LA {own['LA']}, LB {own['LB']}, "
              f"LC {own['LC']}, total {len(rows)}.", "",
              "Demoted by provenance (defined, but manual/RE/undeclared-origin) "
              + ids(lambda k, r: k["defined"] and not k["clean"]), "",
              "Demoted by cross-area dispute (defined, but another row of its X-group "
              "is not) " + ids(lambda k, r: k["defined"] and not k["undisputed"]), "",
              "Marked Y or Cond by the area file but not defined by rules 1-4 "
              + ids(lambda k, r: head(r[6]) in ("Y", "Cond") and not k["defined"])]
    return "\n".join(lines)


def render_matrix(rows):
    sep = "| " + " | ".join(["---"] * 12) + " |"
    return "\n".join([HEADER, sep] + ["| " + " | ".join(r) + " |" for r in rows])


def regenerate(text, rows, group_map):
    clean_ids = overrides(text)
    for name, body in (("matrix", render_matrix(rows)), ("rates", render_rates(rows, group_map, clean_ids))):
        pat = re.compile(rf"(<!-- BEGIN GENERATED: {name} -->\n).*?(<!-- END GENERATED: {name} -->)", re.S)
        if not pat.search(text):
            raise ValueError(f"marker for {name} missing")
        text = pat.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)
    return text


def main(argv):
    text = MATRIX.read_text(encoding="utf-8")
    group_map = groups(text)
    rows = area_rows(group_map)
    if "--write" in argv or "--check" in argv:
        new = regenerate(text, rows, group_map)
        if "--check" in argv:
            ok = new == text
            print("matrix up to date" if ok else "matrix STALE: run --write")
            return 0 if ok else 1
        MATRIX.write_text(new, encoding="utf-8", newline="\n")
    print(render_rates(rows, group_map, overrides(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
