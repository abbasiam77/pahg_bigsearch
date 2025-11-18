#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Validate catalog.json syntax + structure"
python3 - <<'PY'
import json
with open("catalog.json","r",encoding="utf-8") as f:
    data = json.load(f)
assert isinstance(data, dict), "catalog.json is not a dict"
assert "families" in data, "catalog.json missing 'families'"
print("OK: catalog.json loaded. families =", len(data.get("families",[])))
PY

echo "[2/4] Build index.bs"
python3 scripts/make_index_bs.py

echo "[3/4] Validate index.bs line-by-line JSON"
python3 - <<'PY'
import json
for i, l in enumerate(open("index.bs","r",encoding="utf-8"), 1):
    tag, js = l.rstrip("\n").split("\t", 1)
    assert tag in ("DB","ENTRY"), f"Bad tag at line {i}"
    json.loads(js)
print("OK: index.bs JSON per line")
PY

echo "[4/4] Counts"
printf "Total lines:  %s\n" "$(wc -l < index.bs)"
printf "ENTRY lines:  %s\n" "$(grep -c '^ENTRY' index.bs || true)"
printf "Family ENTRY: %s\n" "$(grep -c '\"type\":\"family\"' index.bs || true)"
printf "Gene ENTRY:   %s\n" "$(grep -c '\"type\":\"gene\"' index.bs || true)"

echo "quick_checks: done."
