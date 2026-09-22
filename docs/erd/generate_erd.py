#!/usr/bin/env python3
"""Render supabase/erd_schema.sql as a classic crow's-foot ERD (PNG + SVG).

Reads the DBML produced by `sql2dbml` (docs/erd/squadup.dbml) and emits a Graphviz
graph with orthogonal edge routing. Enum types are left out on purpose: they are
value lists, not entities, and drawing them as boxes buries the real relationships.

    python3 docs/erd/generate_erd.py
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DBML = ROOT / "docs/erd/squadup.dbml"
OUT = ROOT / "docs/erd"

HEADER_BG = "#d9d9d9"
BORDER = "#333333"
LINE = "#555555"
KEY_COLOR = "#b03030"
TYPE_COLOR = "#777777"


def parse(text):
    """-> (tables, refs, enums). Tables map name -> list of (column, type, marks)."""
    enums = set(re.findall(r'^Enum "([^"]+)" \{', text, re.M))

    # Foreign keys first, so columns can be marked as they're read.
    refs = []
    for line in text.split("\n"):
        if not line.startswith("Ref"):
            continue
        m = re.search(
            r'"([^"]+)"\."([^"]+)"\s*(\??)(<>|[<>-])(\??)\s*"([^"]+)"\."([^"]+)"', line
        )
        if not m:
            continue
        lt, lc, lopt, op, ropt, rt, rc = m.groups()
        # sql2dbml always writes parent <op> child for a foreign key.
        refs.append({"parent": lt, "child": rt, "child_col": rc, "optional": bool(ropt)})

    fks = {}
    for r in refs:
        fks.setdefault(r["child"], set()).add(r["child_col"])

    tables = {}
    for name, body in re.findall(r'^Table "([^"]+)" \{\n(.*?)^\}', text, re.S | re.M):
        # A composite primary key isn't an inline [pk]; sql2dbml emits it as an
        # index instead, e.g. `(user_id, post_id) [pk]`.
        composite = set()
        idx = re.search(r"Indexes \{\n(.*?)\n  \}", body, re.S)
        if idx:
            for cols in re.findall(r"\(([^)]+)\)\s*\[pk\]", idx.group(1)):
                composite.update(c.strip() for c in cols.split(","))

        # A single-column unique constraint turns a one-to-many into a one-to-one.
        uniques = set()
        if idx:
            for m in re.finditer(r"^\s*(\w+) \[[^\]]*unique", idx.group(1), re.M):
                uniques.add(m.group(1))

        cols = []
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith(("Indexes", "Checks", "}", "(")) or not line:
                continue
            m = re.match(r'"([^"]+)" ([^\[]+)(?:\[(.*)\])?', line)
            if not m:
                continue
            col, typ, attrs = m.group(1), m.group(2).strip(), m.group(3) or ""
            marks = set()
            if "pk" in attrs or col in composite:
                marks.add("pk")
                marks.add("nn")  # a pk is never nullable; DBML just doesn't say so
            if "not null" in attrs:
                marks.add("nn")
            if col in fks.get(name, ()):
                marks.add("fk")
            if "unique" in attrs or col in uniques:
                marks.add("uq")
            cols.append((col, typ, marks))
        tables[name] = cols

    # Cardinality is read off the child's FK column: a NOT NULL FK means the child
    # must have a parent (1), a nullable one means it may not (0..1); a UNIQUE FK
    # caps the parent's side at one child instead of many.
    for r in refs:
        marks = next(
            (m for c, _, m in tables.get(r["child"], ()) if c == r["child_col"]), set()
        )
        r["one_side"] = "1" if "nn" in marks else "0..1"
        r["many_side"] = "0..1" if "uq" in marks else "0..N"

    return tables, refs, enums


def node(name, cols):
    rows = [
        f'<TR><TD COLSPAN="3" BGCOLOR="{HEADER_BG}" ALIGN="CENTER">'
        f"<B>{name}</B></TD></TR>"
    ]
    for col, typ, marks in cols:
        key = ",".join(k for k in ("PK", "FK") if k.lower() in marks)
        label = f"<B>{col}</B>" if "pk" in marks else col
        null = "" if "nn" in marks else " ?"
        rows.append(
            f'<TR>'
            # Graphviz HTML rejects an empty <B></B>, so a plain column gets a space.
            f'<TD PORT="{col}" ALIGN="LEFT">'
            + (
                f'<FONT POINT-SIZE="8" COLOR="{KEY_COLOR}"><B>{key}</B></FONT>'
                if key else " "
            )
            + "</TD>"
            f'<TD ALIGN="LEFT">{label}</TD>'
            f'<TD ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="{TYPE_COLOR}">'
            f"{typ}{null}</FONT></TD>"
            f"</TR>"
        )
    table = (
        f'<TABLE BORDER="1" COLOR="{BORDER}" CELLBORDER="0" CELLSPACING="0" '
        f'CELLPADDING="2" BGCOLOR="white">' + "".join(rows) + "</TABLE>"
    )
    return f'  "{name}" [label=<{table}>];'


def card(text):
    """An edge label on a white plate, so the line doesn't run through the digits."""
    return (
        f'<<TABLE BORDER="0" CELLBORDER="0" CELLPADDING="1" BGCOLOR="white">'
        f'<TR><TD><FONT COLOR="{KEY_COLOR}" POINT-SIZE="9">{text}</FONT></TD></TR>'
        f"</TABLE>>"
    )


def build(tables, refs, rankdir="LR"):
    out = [
        "digraph squadup {",
        f"  rankdir={rankdir};",
        "  splines=ortho;",       # the straight, right-angled lines
        "  nodesep=0.4;",
        "  ranksep=0.8;",
        "  esep=0.2;",
        '  bgcolor="white";',
        '  graph [fontname="Helvetica"];',
        '  node [shape=plaintext, fontname="Helvetica", fontsize=10];',
        f'  edge [color="{LINE}", penwidth=1.0, fontname="Helvetica", '
        f'fontsize=9, fontcolor="{KEY_COLOR}", labeldistance=1.6, labelangle=0];',
        "",
    ]
    for name, cols in tables.items():
        out.append(node(name, cols))
    out.append("")
    for r in refs:
        # Plain lines with numeric cardinality at each end: crow's-foot glyphs sit
        # crooked on orthogonal edges, where every endpoint is axis-aligned.
        out.append(
            f'  "{r["parent"]}" -> "{r["child"]}" [dir=none, '
            f'taillabel={card(r["one_side"])}, headlabel={card(r["many_side"])}];'
        )
    out.append("}")
    return "\n".join(out)


def main():
    tables, refs, enums = parse(DBML.read_text())
    dot = build(tables, refs)
    (OUT / "squadup-erd.dot").write_text(dot)
    for fmt, extra in (("png", ["-Gdpi=110"]), ("svg", [])):
        subprocess.run(
            ["dot", f"-T{fmt}", *extra, "-o", str(OUT / f"squadup-erd.{fmt}")],
            input=dot, text=True, check=True,
        )
    pks = sum(1 for c in tables.values() for _, _, m in c if "pk" in m)
    fk = sum(len(v) for v in [{c for c, _, m in cols if "fk" in m} for cols in tables.values()])
    print(f"{len(tables)} tables, {len(refs)} relationships, {pks} pk cols, {fk} fk cols, "
          f"{len(enums)} enums (not drawn)")


if __name__ == "__main__":
    sys.exit(main())
