#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

p = Path("catalog.json")
try:
    data = json.loads(p.read_text(encoding="utf-8"))
except Exception as e:
    print("ERROR: catalog.json failed to parse:", e)
    sys.exit(1)

families = data.get("families", [])
print(f"families: {len(families)}")

# Basic presence checks
missing = {"familySymbol":0, "familyTitle":0}
members_total = 0
within_family_dupes = {}
bad_urls = []

url_re = re.compile(r"^https://www\.pahgncb\.com/genomedb/public/searchmember\?mid=\d+$")

for fam in families:
    fs = fam.get("familySymbol")
    ft = fam.get("familyTitle")
    if not fs: missing["familySymbol"] += 1
    if not ft: missing["familyTitle"] += 1

    seen = set()
    for m in fam.get("members", []) or []:
        members_total += 1
        gs = m.get("geneSymbol")
        url = m.get("url","")
        if gs in seen:
            within_family_dupes.setdefault(fs or "(no symbol)", set()).add(gs)
        else:
            seen.add(gs)
        if url and not url_re.match(url):
            bad_urls.append((fs, gs, url))

print(f"members: {members_total}")
print("missing familySymbol:", missing["familySymbol"])
print("missing familyTitle :", missing["familyTitle"])
print("\nWithin-family duplicate genes (ONLY warn, allowed across families):")
if within_family_dupes:
    for fs, genes in sorted(within_family_dupes.items()):
        print(" ", fs, ":", ", ".join(sorted(genes)))
else:
    print("  none")

print("\nMalformed member URLs (first 10):")
for tup in bad_urls[:10]:
    print(" ", tup)
print("Total malformed URLs:", len(bad_urls))

# non-fatal warnings only
print("\nvalidate_catalog.py: completed.")
