# PAHG BigSearch: Catalog & Index Builder

This repository contains scripts and data to build a **PAHG gene-family catalog** (`catalog.json`) and a **search index** (`index.bs`) suitable for downstream use, including:
- Integration with **BIG Search** (CNCB/NGDC): https://ngdc.cncb.ac.cn/search/specific?db=pahg&q=
- Listing PAHG as a **Partner Database**: https://ngdc.cncb.ac.cn/partners

The workflow is designed for **append-only curation**: you author JSON “batches” for newly curated families; the toolchain merges them into `catalog.json` (dedupe-safe), validates the catalog, and emits a reproducible `index.bs`.

---

## Repository Layout

```
.
├── Makefile
├── README.md
├── LICENSE
├── .gitignore
├── catalog.json                # built from data/batches (tracked)
├── index.bs                    # generated (ignored by default; see below)
├── data/
│   └── batches/                # append-only JSON batches you author
│       ├── 2025-11-17_batch.json
│       └── ...
└── scripts/
    ├── build_catalog.py        # merges batches → catalog.json (dedupe-safe)
    ├── make_index_bs.py        # catalog.json → index.bs
    ├── validate_catalog.py     # schema/field validation
    └── quick_checks.sh         # URL & duplicate checks, counts, etc.
```

> If a directory/file is missing, create it (empty) and commit; the scripts assume the above structure.

---

## Quick Start

### Prerequisites
- **Python 3.8+**
- **GNU make**
- **bash** (for `scripts/quick_checks.sh`)

(Optional but recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if you add one later
```

### 1) Add a curation batch

Create a file like `data/batches/2025-11-17_batch.json`:

```json
{
  "families": [
    {
      "familySymbol": "PPARGC",
      "familyTitle": "Peroxisome Proliferator-Activated Receptor Gamma, Coactivator (PPARGC)",
      "members": [
        {"memberId": "835", "geneSymbol": "PPARGC1A", "url": "https://www.pahgncb.com/genomedb/public/searchmember?mid=835"},
        {"memberId": "836", "geneSymbol": "PPARGC1B", "url": "https://www.pahgncb.com/genomedb/public/searchmember?mid=836"},
        {"memberId": "837", "geneSymbol": "PPRC1",    "url": "https://www.pahgncb.com/genomedb/public/searchmember?mid=837"}
      ]
    }
  ]
}
```

**Rules:**
- `familySymbol` = short unique tag (e.g., `KCNJ`, `PPARGC`).
- `familyTitle` = human-readable family title.
- Each `member` must include `memberId` (string), `geneSymbol`, and a `url` in the form  
  `https://www.pahgncb.com/genomedb/public/searchmember?mid=<NUM>`.

### 2) Build the catalog and index

```bash
# Merge batches → catalog.json (dedupe-safe)
make catalog.json

# Convert catalog.json → index.bs
make index.bs
```

### 3) Validate & run quick checks

```bash
# Structural and field validation
make validate

# Convenience checks (URL format, counts, within-family duplicates)
bash scripts/quick_checks.sh
```

---

## Data Model (Catalog)

`catalog.json` is an object with a single top-level key:

```json
{
  "families": [
    {
      "familyId": "auto-assigned integer as string",
      "familySymbol": "KCNJ",
      "familyTitle": "Potassium inwardly rectifying channel subfamily J (KCNJ)",
      "familyUrl": "https://www.pahgncb.com/genomedb/public/searchfamily?fid=...",   // optional
      "createdAt": 1731513600,       // unix timestamp (optional)
      "updatedAt": 1731513600,       // unix timestamp (optional)
      "members": [
        {
          "memberId": "296",
          "geneSymbol": "KCNJ6",
          "url": "https://www.pahgncb.com/genomedb/public/searchmember?mid=296"
        }
      ]
    }
  ]
}
```

**Notes**
- `familyId` is assigned during merging (monotonic).  
- The pipeline **allows** the same `geneSymbol` to exist under multiple families (phylogenetically meaningful).
- Within a given family, duplicate `geneSymbol` entries are removed.

---

## Generated Artifacts Policy

- **`catalog.json`** — **tracked** (canonical merged state).
- **`index.bs`** — **generated** and **ignored by default** (reproducible from `catalog.json`).

If you want to **publish `index.bs`** (e.g., attach exact bytes in a tagged release):

```bash
# Start tracking index.bs
sed -i '/^index\.bs$/d' .gitignore
git add .gitignore index.bs
git commit -m "track index.bs artifact for release"
git push
```

Revert to ignoring later:

```bash
echo 'index.bs' >> .gitignore
git rm --cached index.bs
git commit -m "chore: ignore generated index.bs"
git push
```

---

## Makefile Targets

```bash
make catalog.json   # merges data/batches → catalog.json
make index.bs       # catalog.json → index.bs
make validate       # schema/field checks
make all            # = catalog.json + index.bs
```

---

## Validation & Quality Checks

### `make validate` (Python)
- Ensures required keys exist.
- Verifies URL format: `https://www.pahgncb.com/genomedb/public/searchmember?mid=<digits>`.
- Confirms `members` arrays are present and non-empty.

### `scripts/quick_checks.sh` (bash)
- Confirms JSON is parseable.
- Counts families/members.
- Scans for malformed member URLs.
- Detects **within-family** duplicate `geneSymbol`s (fixes suggested).
- (Optional) Prints top recently updated families.

Run:
```bash
bash scripts/quick_checks.sh
```

---

## Reproducible Build

Typical workflow:

```bash
# 1) Author/append new batch JSON(s)
git add data/batches/2025-11-17_batch.json
git commit -m "Add PPARGC and PPP2R2 batches"

# 2) Build + Validate
make catalog.json
make validate
make index.bs
bash scripts/quick_checks.sh

# 3) Commit catalog (index.bs is ignored by default)
git add catalog.json
git commit -m "Update catalog.json after new batches"
git push
```

---

## Troubleshooting

- **“KeyError: 'familyUrl' in make_index_bs.py”**  
  Update scripts or ensure `familyUrl` access is optional in your code. Our current script handles missing `familyUrl` gracefully.

- **`.gitignore` not respected / junk files show up on GitHub**  
  Add patterns to `.gitignore`, then **untrack** the files:
  ```bash
  git rm -r --cached path-or-file
  git commit -m "prune junk"
  git push
  ```

- **Auth failures (HTTPS)**  
  Use **SSH** remote:
  ```bash
  git remote set-url origin git@github.com:<USER>/<REPO>.git
  ```

---

## Contributing / Editing Policy

- Treat `data/batches/*.json` as an **append-only audit log** of curation.
- `catalog.json` is derived; track it to represent the current published state.
- `index.bs` is derived; **ignore by default**; track only when you explicitly want to publish an artifact.

---

## License

This project is released under the **MIT License** (see [LICENSE](LICENSE)).

---

## Acknowledgments

- PAHG database curation team.
- CNCB/NGDC for BIG Search and partner program.
