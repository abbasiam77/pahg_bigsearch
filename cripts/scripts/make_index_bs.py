#!/usr/bin/env python3
# scripts/make_index_bs.py
import json, sys, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "catalog.json"
OUT = ROOT / "index.bs"

def enc(s: str) -> str:
    return html.escape(str(s), quote=True)

def main():
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    fams = cat.get("families", [])
    lines = []
    # DB line
    db = {
        "name": "PAHG",
        "url": "https://www.pahgncb.com/",
        "version": "1.0"
    }
    lines.append("DB\t" + json.dumps(db, separators=(",",":")))
    # Families
    for fam in fams:
        f_entry = {
            "type": "family",
            "id": fam["familySymbol"],
            "title": fam["familyTitle"],
            "url": fam["familyUrl"],
            "attrs": {"familyId": fam["familyId"], "symbol": fam["familySymbol"]},
        }
        lines.append("ENTRY\t" + json.dumps(f_entry, separators=(",",":")))
        # Members
        for m in fam.get("members", []):
            g_entry = {
                "type": "gene",
                "id": m["geneSymbol"],
                "title": m["geneSymbol"],
                "url": m["url"],
                "attrs": {"familySymbol": fam["familySymbol"], "memberId": m["memberId"]},
            }
            lines.append("ENTRY\t" + json.dumps(g_entry, separators=(",",":")))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: wrote {OUT.name} ({len(lines)} lines)")

if __name__ == "__main__":
    main()
