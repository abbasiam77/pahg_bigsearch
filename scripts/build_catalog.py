#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_catalog.py
Merge JSON batches from data/batches into catalog.json (dedupe-safe).
- Keeps stable fields: familySymbol, familyTitle, familyUrl (if any)
- Merges members by geneSymbol; validates PAHG member URL pattern
- Assigns incremental familyId if absent; preserves existing ids
- Updates createdAt/updatedAt UNIX timestamps
"""

import json, re, time
from pathlib import Path

BATCH_DIR = Path("data/batches")
CATALOG   = Path("catalog.json")

URL_RE = re.compile(r"^https://www\.pahgncb\.com/genomedb/public/searchmember\?mid=\d+$")

def now_ts():
    return int(time.time())

def norm_member(m):
    return {
        "memberId": str(m.get("memberId") or m.get("id") or ""),
        "geneSymbol": m["geneSymbol"].strip(),
        "url": m["url"].strip(),
    }

def merge_family(dst, src):
    # merge metadata
    for k in ("familyTitle", "familyUrl"):
        if k in src and src[k]:
            dst[k] = src[k]

    # merge members by geneSymbol
    dst_m = { m["geneSymbol"]: m for m in (dst.get("members") or []) }
    for m in (src.get("members") or []):
        m = norm_member(m)
        if not URL_RE.match(m.get("url","")):
            raise ValueError(f"Bad PAHG URL for {dst.get('familySymbol')}:{m.get('geneSymbol')}: {m.get('url')}")
        dst_m[m["geneSymbol"]] = m
    dst["members"] = sorted(dst_m.values(), key=lambda x: x["geneSymbol"])

def main():
    # start from existing or empty catalog
    if CATALOG.exists():
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))
        families = cat.get("families", [])
    else:
        cat = {"families": []}
        families = cat["families"]

    # index by familySymbol
    fam_index = { f["familySymbol"]: f for f in families if "familySymbol" in f }

    # ensure familyId continuity
    max_id = 0
    for f in families:
        try:
            fid = int(f.get("familyId") or 0)
            if fid > max_id:
                max_id = fid
        except Exception:
            pass

    # load batches
    new_batches = 0
    for p in sorted(BATCH_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        batch_fams = data if isinstance(data, list) else data.get("families", [])
        for f in batch_fams:
            sym = f["familySymbol"].strip()
            fam = {
                "familySymbol": sym,
                "familyTitle": f.get("familyTitle","").strip(),
                "familyUrl": f.get("familyUrl","").strip() or None,
                "members": [norm_member(m) for m in (f.get("members") or [])],
            }
            if sym in fam_index:
                # update existing
                dst = fam_index[sym]
                merge_family(dst, fam)
                dst.setdefault("createdAt", now_ts())
                dst["updatedAt"] = now_ts()
            else:
                # create fresh
                max_id += 1
                fam["familyId"] = max_id
                ts = now_ts()
                fam["createdAt"] = ts
                fam["updatedAt"] = ts
                families.append(fam)
                fam_index[sym] = fam
        new_batches += 1

    # sort families by symbol for stability
    families.sort(key=lambda f: f["familySymbol"])
    cat["families"] = families

    # write catalog.json
    CATALOG.write_text(json.dumps(cat, indent=2), encoding="utf-8")
    print(f"OK: catalog.json updated; batches merged: {new_batches}; families: {len(families)}; members: {sum(len(f.get('members',[])) for f in families)}")

if __name__ == "__main__":
    main()
