#!/usr/bin/env bash
set -euo pipefail

python3 scripts/make_index_bs.py > /dev/null
python3 - <<'PY'
import json
cat = json.load(open("catalog.json","r",encoding="utf-8"))
print("catalog.json: JSON OK")
print("families:", len(cat.get("families", [])))
print("members:", sum(len(f.get("members", [])) for f in cat.get("families", [])))
PY

python3 - <<'PY'
import json
for i, l in enumerate(open("index.bs","r",encoding="utf-8"), 1):
    tag, js = l.rstrip("\n").split("\t", 1)
    assert tag in ("DB","ENTRY")
    json.loads(js)
print("index.bs: line-by-line JSON OK")
PY

echo "Total lines:  $(wc -l < index.bs)"
echo "ENTRY lines:  $(grep -c '^ENTRY' index.bs)"
echo "Family ENTRY: $(grep -c '\"type\":\"family\"' index.bs)"
echo "Gene ENTRY:   $(grep -c '\"type\":\"gene\"' index.bs)"
