#!/usr/bin/env python3
# scripts/build_catalog.py
import json, time, re, sys
from pathlib import Path
from typing import List, Dict

CAT_PATH = Path(__file__).resolve().parents[1] / "catalog.json"

URL_RX = re.compile(r"^https://www\.pahgncb\.com/genomedb/public/searchmember\?mid=\d+$")

def now() -> int:
    return int(time.time())

def mem(mid:int, gene:str) -> Dict:
    return {
        "memberId": str(mid),
        "geneSymbol": gene,
        "url": f"https://www.pahgncb.com/genomedb/public/searchmember?mid={mid}",
    }

# ===================== EDITABLE INPUT ZONE =====================
# Option A: inline batches (easy for quick adds)
NEW_FAMS: List[Dict] = [
    # Example:
    # {
    #   "familySymbol": "KLF",
    #   "familyTitle": "KLF transcription factors (KLF)",
    #   "members": [mem(710,"KLF1"), mem(711,"KLF2")]
    # },
]

# Option B: load from external JSON/CSV in data/batches (optional).
# See README for CSV format and how to call via CLI.
# ===============================================================

def load_catalog() -> Dict:
    if CAT_PATH.exists():
        return json.loads(CAT_PATH.read_text(encoding="utf-8"))
    return {"families": []}

def save_catalog(cat: Dict) -> None:
    # keep a dated backup then write
    bak = CAT_PATH.with_suffix(f".bak.{int(time.time())}.json")
    if CAT_PATH.exists():
        bak.write_text(CAT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    CAT_PATH.write_text(json.dumps(cat, indent=2), encoding="utf-8")
    print(f"catalog.json updated. Backup: {bak.name if bak.exists() else '(none)'}")

def sanitize_member(m: Dict) -> Dict:
    if not URL_RX.match(m.get("url","")):
        m["url"] = f"https://www.pahgncb.com/genomedb/public/searchmember?mid={m.get('memberId','')}"
    return m

def next_family_id(families: List[Dict]) -> int:
    mx = 0
    for f in families:
        try:
            mx = max(mx, int(f.get("familyId") or 0))
        except: pass
    return mx + 1

def integrate(cat: Dict, new_fams: List[Dict]) -> Dict:
    families = cat.setdefault("families", [])
    by_sym = {f["familySymbol"]: f for f in families if "familySymbol" in f}

    added_fams = 0
    updated_fams = 0
    added_genes = 0

    fid = next_family_id(families)
    for nf in new_fams:
        sym = nf["familySymbol"].strip()
        title = nf["familyTitle"].strip()
        mems = [sanitize_member(m) for m in nf.get("members", [])]

        if sym in by_sym:
            fam = by_sym[sym]
            have = {m["geneSymbol"] for m in fam.get("members", [])}
            new_only = [m for m in mems if m["geneSymbol"] not in have]
            if new_only:
                fam["members"].extend(new_only)
                added_genes += len(new_only)
                updated_fams += 1
            # ensure required metadata
            fam.setdefault("familyTitle", title)
            fam.setdefault("familyUrl", f"https://www.pahgncb.com/genomedb/public/search?fs={sym}")
            fam.setdefault("createdAt", now())
            fam["updatedAt"] = now()
        else:
            fam = {
                "familyId": fid,
                "familySymbol": sym,
                "familyTitle": title,
                "familyUrl": f"https://www.pahgncb.com/genomedb/public/search?fs={sym}",
                "createdAt": now(),
                "updatedAt": now(),
                "members": []
            }
            # de-dupe *within family only*
            seen = set()
            for m in mems:
                g = m["geneSymbol"]
                if g in seen: continue
                seen.add(g)
                fam["members"].append(m)
            families.append(fam)
            by_sym[sym] = fam
            added_fams += 1
            added_genes += len(fam["members"])
            fid += 1

    print(f"New families added: {added_fams}")
    print(f"Existing families updated: {updated_fams}")
    print(f"New genes added (within-family unique): {added_genes}")
    return cat

def main():
    cat = load_catalog()
    # Optionally: load external batches by CLI (e.g. JSON file path)
    # Minimal: if a path was provided, it should be a JSON with NEW_FAMS-like structure.
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.suffix.lower() == ".json":
            batch = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(batch, dict) and "families" in batch:
                extend = batch["families"]
            else:
                extend = batch
            cat = integrate(cat, extend)
        else:
            print("Only JSON batch supported in this simple CLI example.")
    else:
        cat = integrate(cat, NEW_FAMS)
    save_catalog(cat)

if __name__ == "__main__":
    main()
