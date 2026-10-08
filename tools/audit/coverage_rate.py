"""Spec-coverage matrix: build, verify and rate (stdlib only).

The consolidated table in docs/specifications/coverage-matrix.md is a verbatim
copy of the rows in docs/specifications/coverage/*.md. Two mechanical edits are
made: relative link targets are rebased one directory up, and cross-area flags
("[X-nn]") are appended to the ID cell.

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

# Cross-area overlaps/disagreements; explained in coverage-matrix.md section 3.
FLAGS = {
    "X-01": "ROM-65 COM-52 COM-63 API-72 CD-117",
    "X-02": "ROM-68 ROM-70 COM-81 API-73 CD-117",
    "X-03": "ROM-26 ROM-27 COM-79 API-80 API-81 PRV-04",
    "X-04": "API-06 API-10 API-32 API-37 CD-080 PRV-02 PRV-12",
    "X-05": "API-16 API-23 CD-081",
    "X-06": "ROM-101 API-71 CD-130 CD-131 CD-132 CD-133 PRV-05 PRV-06 PRV-07",
    "X-07": "ROM-90 API-60 PRV-13",
    "X-08": "ROM-11 ROM-71 COM-35 COM-82 API-82 API-83 API-92 API-94 PRV-03",
    "X-09": "CD-031 CD-034 CD-035 PRV-15 PRV-19",
    "X-10": "CD-060 PRV-16",
    "X-11": "ROM-44 COM-86",
    "X-12": "ROM-49 COM-32 COM-33 API-07 API-14 CD-116",
    "X-13": "ROM-10 COM-58 API-76 API-77 CD-120",
    "X-14": "ROM-47 API-15",
    "X-15": "ROM-31 PRV-27",
    "X-16": "CD-022 CD-023 API-70 PRV-10",
    "X-17": "API-30 API-34 CD-091",
    "X-18": "API-05 API-65 API-66 CD-089",
    "X-19": "API-45 CD-037 CD-107",
    "X-20": "ROM-43 ROM-63 COM-09",
    "X-21": "ROM-41 COM-05",
    "X-22": "ROM-40 COM-04",
}
CONFLICT = re.compile(r"unconfirmed|conflict|disagree|contradict", re.I)
# Provenance cell says the knowledge derives from the excluded manuals or from RE.
TAINT = re.compile(r"P-OFF|P-RE|\bRE\b|RE-derived|reverse.engineer|disassembl|"
                   r"official BIOS manual|derived from L-0|derive from XS", re.I)


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_rows(text):
    """12-column rows whose first cell is an item ID (optionally flagged)."""
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


def item_id(row):
    return row[0].split()[0]


def area_rows():
    flags = {}
    for tag, ids in FLAGS.items():
        for i in ids.split():
            flags.setdefault(i, []).append(tag)
    out = []
    for prefix, _, name in AREAS:
        rows = table_rows((SPEC / "coverage" / name).read_text(encoding="utf-8"))
        for r in rows:
            if not r[0].startswith(prefix + "-"):
                raise ValueError(f"{name}: unexpected ID {r[0]}")
            r = [c.replace("](../", "](") for c in r]
            r[0] = " ".join([r[0]] + [f"[{t}]" for t in flags.get(r[0], [])])
            out.append(r)
    ids = [item_id(r) for r in out]
    missing = {i for v in FLAGS.values() for i in v.split()} - set(ids)
    if len(ids) != len(set(ids)) or missing:
        raise ValueError(f"duplicate IDs or unknown flagged IDs: {missing}")
    return out


def head(cell):
    """Leading Y / Cond / N / Partial token of a cell, ignoring bold."""
    m = re.match(r"(Y|Cond|N|partial)(?![\w/])", cell.replace("*", "").strip(), re.I)
    return m.group(1).capitalize() if m else ""


def level(row):
    return re.match(r"L[ABC]", row[2]).group(0)  # "LB/LC" counts at LB


def defined(row):
    """Verifiable spec defined from non-excluded sources (matrix section 4)."""
    material, impl, own_test, blocker = head(row[3]), head(row[6]), head(row[8]), head(row[11])
    if impl not in ("Y", "Cond"):
        return False
    if any(CONFLICT.search(row[i]) for i in (3, 4, 5, 6)):
        return False
    if (impl == "Cond" or material != "Y") and own_test != "Y":
        return False
    if impl == "Cond" and blocker == "Y":
        return False
    return True


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


def rates(rows):
    """{scope: {level: (defined, untainted, Y-only, enumerated)}}, levels cumulative."""
    prov = provenance(rows)
    scopes = {"All areas": rows}
    for prefix, label, _ in AREAS:
        scopes[label] = [r for r in rows if item_id(r).startswith(prefix + "-")]
    out = {}
    for scope, rs in scopes.items():
        out[scope] = {}
        for n, lv in enumerate(LEVELS):
            sel = [r for r in rs if level(r) in LEVELS[: n + 1]]
            d = [r for r in sel if defined(r)]
            out[scope][lv] = (len(d), sum(not TAINT.search(prov[item_id(r)]) for r in d),
                              sum(head(r[6]) == "Y" for r in d), len(sel))
    return out


def pct(a, b):
    return f"{a}/{b} = {100 * a / b:.1f}%" if b else f"{a}/0: not computable"


def render_rates(rows):
    lines = []
    for k, title in ((0, "Headline: defined"), (1, "Defined and provenance cell not "
                     "manual/RE-derived"), (2, "Defined and Implementable = Y")):
        lines += [f"**{title}**", "",
                  "| Scope | LA (LA items) | LB (LA+LB items) | LC (all items) |",
                  "| --- | --- | --- | --- |"]
        for scope, by in rates(rows).items():
            lines.append(f"| {scope} | " + " | ".join(pct(by[lv][k], by[lv][3]) for lv in LEVELS) + " |")
        lines.append("")
    own = {lv: sum(level(r) == lv for r in rows) for lv in LEVELS}
    excluded = [item_id(r) for r in rows if head(r[6]) in ("Y", "Cond") and not defined(r)]
    lines += [f"Items enumerated by minimum level: LA {own['LA']}, LB {own['LB']}, "
              f"LC {own['LC']}, total {len(rows)}.",
              "",
              f"Items marked Y or Cond by their area file but NOT counted as defined "
              f"by the rule ({len(excluded)}): " + ", ".join(excluded) + "."]
    return "\n".join(lines)


def render_matrix(rows):
    sep = "| " + " | ".join(["---"] * 12) + " |"
    return "\n".join([HEADER, sep] + ["| " + " | ".join(r) + " |" for r in rows])


def regenerate(text, rows):
    for name, body in (("matrix", render_matrix(rows)), ("rates", render_rates(rows))):
        pat = re.compile(rf"(<!-- BEGIN GENERATED: {name} -->\n).*?(<!-- END GENERATED: {name} -->)", re.S)
        if not pat.search(text):
            raise ValueError(f"marker for {name} missing")
        text = pat.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)
    return text


def main(argv):
    rows = area_rows()
    if "--write" in argv or "--check" in argv:
        text = MATRIX.read_text(encoding="utf-8")
        new = regenerate(text, rows)
        if "--check" in argv:
            ok = new == text
            print("matrix up to date" if ok else "matrix STALE: run --write")
            return 0 if ok else 1
        MATRIX.write_text(new, encoding="utf-8", newline="\n")
    print(render_rates(table_rows(MATRIX.read_text(encoding="utf-8")) if MATRIX.exists() else rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
