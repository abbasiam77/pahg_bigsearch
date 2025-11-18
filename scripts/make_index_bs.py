#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from urllib.parse import urlsplit, urlunsplit, quote

def enc(u: str) -> str:
    p = urlsplit(u)
    return urlunsplit((p.scheme, p.netloc, quote(p.path, safe="/%._-~"), p.query, p.fragment))

def j(d: dict) -> str:
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

def main():
    with open("catalog.json", "r", encoding="utf-8") as f:
        cat = json.load(f)

    db = cat["db"]
    families = cat.get("families", [])

    lines = []
    # DB line
    lines.append("DB\t" + j(db))

    # ENTRY lines
    for fam in families:
        fam_entry = {
            "id": fam["familySymbol"],
            "type": "family",
            "title": fam["familyTitle"],
            "url": enc(fam["familyUrl"]),
            "dbId": db["id"],
            "updatedAt": db["updatedAt"],
            "description": fam.get("familyDescription", ""),
            "basicInfo": "",
            "species": db.get("species", []),
            "attrs": {"familyId": fam["familyId"], "symbol": fam["familySymbol"]},
        }
        lines.append("ENTRY\t" + j(fam_entry))

        for m in fam.get("members", []):
            gene_entry = {
                "id": m["geneSymbol"],
                "type": "gene",
                "title": m["geneSymbol"],
                "url": enc(m["url"]),
                "dbId": db["id"],
                "updatedAt": db["updatedAt"],
                "description": f"{m['geneSymbol']} — {fam['familySymbol']} family member.",
                "basicInfo": "",
                "species": db.get("species", []),
                "attrs": {"memberId": m["memberId"], "family": fam["familySymbol"]},
            }
            lines.append("ENTRY\t" + j(gene_entry))

    with open("index.bs", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"OK: wrote index.bs ({len(lines)} lines)")

if __name__ == "__main__":
    main()
