# PAHG BigSearch: Catalog & Index for Gene Families

A minimal, reproducible toolkit to build and validate **`catalog.json`** and **`index.bs`** for the **PAHG** partner dataset, enabling downstream integration with the **BIG Search Engine** and inclusion in public partner listings.

> **Goal:** curate PAHG gene families → generate a normalized `catalog.json` → compile a searchable `index.bs` → ship both with validation and sanity checks.

---

## Table of Contents

- [Overview](#overview)
- [Repository Layout](#repository-layout)
- [Install](#install)
- [Quick Start](#quick-start)
- [Data Model](#data-model)
  - [`catalog.json` schema](#catalogjson-schema)
  - [`index.bs` format](#indexbs-format)
- [Batch Additions](#batch-additions)
- [Makefile Targets](#makefile-targets)
- [Validation & Checks](#validation--checks)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This repo hosts scripts and data for building PAHG’s public search layer:

1. **Collect** family/member metadata (from PAHG web or internal curation).
2. **Assemble** a canonical **`catalog.json`**.
3. **Compile** a line-oriented **`index.bs`** (for ingestion by search backends).
4. **Validate** structure and perform quality checks (URLs, duplicates, counts).
5. **Publish** artifacts to GitHub for downstream partners.

**Primary artifacts**

- `catalog.json` — canonical catalog of **families** and **members**.
- `index.bs` — flattened, line-by-line JSON records (`DB`, `ENTRY`) for search.

---

## Repository Layout

```
.
├── Makefile
├── README.md
├── catalog.json                # generated
├── index.bs                    # generated
├── data/
│   └── batches/                # JSON batches you author (append-only history)
│       ├── 2025-11-17_batch.json
│       └── ...
└── scripts/
    ├── build_catalog.py        # merges batches → catalog.json (dedupe-safe)
    ├── make_index_bs.py        # catalog.json → index.bs
    ├── validate_catalog.py     # schema/field validation
    └── quick_checks.sh         # URL & duplicate checks, counts, etc.
```

> You may add `schemas/` for JSONSchema if desired. This project ships with lightweight, script-based validation to keep dependencies minimal.

---

## Install

- Python 3.9+ recommended.
- No heavy dependencies; standard library only.

Create a virtual environment (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -V
```

---

## Quick Start

From the repository root:

```bash
# 1) Build/refresh catalog from one or more batch files
make build BATCH="data/batches/2025-11-17_batch.json"

# 2) Generate index.bs from catalog.json
make index

# 3) Validate & run checks
make all_checks

# 4) One-shot (build + index + validations + checks)
make all
```

Artifacts will be written to `catalog.json` and `index.bs`. Backups are created automatically before destructive updates (e.g., `*.bak.json`).

---

## Data Model

### `catalog.json` schema

Minimal required shape (all strings unless noted):

```jsonc
{
  "families": [
    {
      "familyId": 215,                      // integer, unique & stable
      "familySymbol": "KCNJ",               // short stable key
      "familyTitle": "Potassium inwardly rectifying channel subfamily J (KCNJ)",
      "familyUrl": "https://www.pahgncb.com/genomedb/public/search?family=KCNJ",
      "createdAt": 1731810813,              // unix epoch (seconds)
      "updatedAt": 1731810813,              // unix epoch (seconds)
      "members": [
        {
          "memberId": "296",                // PAHG member internal id (string ok)
          "geneSymbol": "KCNJ6",
          "url": "https://www.pahgncb.com/genomedb/public/searchmember?mid=296"
        }
      ]
    }
  ]
}
```

**Notes**

- `familySymbol` and `familyTitle` must be present.
- `familyId` must be unique monotonically increasing over time (scripts auto-assign the next id).
- A member’s `url` must match:  
  `https://www.pahgncb.com/genomedb/public/searchmember?mid=<digits>`
- **Cross-family reuse of genes is allowed** (e.g., same `geneSymbol` in multiple families). The checks only dedupe **within** a family.

### `index.bs` format

A newline-delimited file where each line is a tuple: `TAG<TAB>JSON`

- The first line is a single **`DB`** record describing the dataset (name, version, counts).
- Subsequent lines are **`ENTRY`** records (one per family and one per gene member).

Example (abbreviated):

```
DB  {"name":"PAHG","version":"2025-11-17","families":220,"genes":1227}
ENTRY   {"type":"family","id":"KCNJ","title":"Potassium inwardly rectifying channel subfamily J (KCNJ)","attrs":{"familyId":215,"symbol":"KCNJ"}}
ENTRY   {"type":"gene","id":"KCNJ6","title":"KCNJ6","attrs":{"familySymbol":"KCNJ","memberId":"296","url":"https://www.pahgncb.com/genomedb/public/searchmember?mid=296"}}
```

---

## Batch Additions

Author a batch file in `data/batches/` containing families to add/update:

```jsonc
{
  "families": [
    {
      "familySymbol": "PPARGC",
      "familyTitle": "Peroxisome Proliferator-Activated Receptor Gamma, Coactivator (PPARGC)",
      "members": [
        {"memberId":"835","geneSymbol":"PPARGC1A","url":"https://www.pahgncb.com/genomedb/public/searchmember?mid=835"},
        {"memberId":"836","geneSymbol":"PPARGC1B","url":"https://www.pahgncb.com/genomedb/public/searchmember?mid=836"},
        {"memberId":"837","geneSymbol":"PPRC1","url":"https://www.pahgncb.com/genomedb/public/searchmember?mid=837"}
      ]
    }
  ]
}
```

Then run:

```bash
make build BATCH="data/batches/2025-11-17_ppargc.json"
make index
make all_checks
```

- The builder **auto-fills** `familyId`, `createdAt`, `updatedAt` if missing.
- Families are matched by `familySymbol`. If `familySymbol` exists, members are merged (duplicates within the *same* family are ignored).

---

## Makefile Targets

- `make build` — Merge batch files into `catalog.json`.  
  Use `BATCH="file1.json file2.json"` to provide one or more batches.
- `make index` — Compile `index.bs` from the current `catalog.json`.
- `make validate` — Run structural validations.
- `make checks` — Quick sanity checks (counts, URL patterns, within-family dupes).
- `make all` — `build` → `index` → `validate` → `checks`.
- `make clean` — Remove `index.bs` (backups of JSON retained).

---

## Validation & Checks

**Structural validations** (Python):
- Required family fields (`familySymbol`, `familyTitle`).
- Member URL regex: `^https://www\.pahgncb\.com/genomedb/public/searchmember\?mid=\d+$`
- `familyId` is integer; `createdAt`/`updatedAt` are epoch seconds.

**Sanity checks** (Bash + Python):
- Totals (`families`, `members`), and `index.bs` line counts (DB + ENTRY).
- Within-family duplicate members (same `geneSymbol` under one family) → removed.
- Cross-family duplicates **allowed** and reported only if you opt-in.
- Detect malformed lines in `index.bs` (each `ENTRY` must be valid JSON).

Run all:

```bash
make all_checks
```

---

## Examples

- **Build from scratch** (no batches, script may include default seed or prompt):
  ```bash
  make build
  make index
  make all_checks
  ```

- **Incremental add** (recommended workflow):
  ```bash
  # Add a new batch file with families/members you curated
  git add data/batches/2025-11-18_newfamilies.json
  make build BATCH="data/batches/2025-11-18_newfamilies.json"
  make index
  make all_checks
  git commit -m "Add 2025-11-18 batch; rebuild catalog & index"
  ```

---

## Troubleshooting

- **KeyError in `make_index_bs.py`** (e.g., `familyTitle` or `familyUrl`):  
  Ensure batch families supply `familySymbol` and `familyTitle`. `familyUrl` is auto-filled by scripts if omitted.

- **Duplicate genes**:  
  Cross-family duplicates are allowed. Within-family duplicates are dropped automatically (first occurrence wins).

- **Malformed URL**:  
  Ensure member URLs follow the exact pattern with a numeric `mid` as provided by PAHG.

- **Timestamps**:  
  Scripts write epoch seconds; conversions to human-readable are for display only.

---

## Contributing

- Use a new JSON in `data/batches/` per logical curation step.
- Keep `familySymbol` stable across time (renames require a one-time migration batch).
- PRs welcome for new checks and CI (e.g., GitHub Actions for `make all`).

---

## License

This project is released under the **MIT License**. See `LICENSE` for details.
