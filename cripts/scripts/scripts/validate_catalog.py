#!/usr/bin/env python3
# scripts/validate_catalog.py
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "catalog.json"
SCHEMA = ROOT / "scripts" / "schema_catalog.json"

URL_RX = re.compile(r"^https://www\.pahgncb\.com/genomedb/public/searchmember\?mid=\d+$")

def jsonschema_validate(data, schema):
    # Tiny embedded validator using jsonschema if available; otherwise soft-check only.
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return []
    except ImportError:
        return ["jsonschema not installed; skipped formal schema validation."]
    except Exception as e:
        return [f"Schema validation error: {e}"]

def main():
    data = json.loads(CAT.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    problems = []

    problems += jsonschema_validate(data, schema)

    within_dupes_total = 0
    bad_urls_total = 0
    fams = data.get("families", [])

    # familySymbol uniqueness
    seen_fam = set()
    for f in fams:
        fs = f.get("familySymbol")
        if fs in seen_fam:
            problems.append(f"Duplicate familySymbol found: {fs}")
        seen_fam.add(fs)

        # within-family duplicates
        seen_genes = set()
        for m in f.get("members", []) or []:
            gs = m.get("geneSymbol")
            if gs in seen_genes:
                within_dupes_total += 1
            seen_genes.add(gs)

            url = m.get("url", "")
            if not URL_RX.match(url):
                bad_urls_total += 1

    if within_dupes_total:
        problems.append(f"Within-family duplicate gene entries: {within_dupes_total}")
    if bad_urls_total:
        problems.append(f"Malformed member URLs: {bad_urls_total}")

    if problems:
        print("VALIDATION: FAIL")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    else:
        print("VALIDATION: OK")
        print(f"families: {len(fams)}")
        print(f"members:  {sum(len(f.get('members',[])) for f in fams)}")

if __name__ == "__main__":
    main()
