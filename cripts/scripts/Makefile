# ---- Config ----
PY        ?= python3
CATALOG   ?= catalog.json
INDEX     ?= index.bs
# Optional: pass one or more batch files, e.g.:
# make build BATCH="data/batches/2025-11-17_batch.json data/batches/more.json"
BATCH     ?=

# ---- Top-level ----
.PHONY: all build index validate checks quick all_checks clean help

all: build index validate checks

# Build/refresh catalog.json from batches (or internal defaults if script supports it)
build:
	@echo "==> Building $(CATALOG)"
	$(PY) scripts/build_catalog.py $(BATCH)

# Produce index.bs from catalog.json
index:
	@echo "==> Building $(INDEX)"
	$(PY) scripts/make_index_bs.py

# JSON/schema validations
validate:
	@echo "==> Validating catalog and index"
	$(PY) scripts/validate_catalog.py

# Extra sanity checks (counts, malformed URLs, duplicates within a family, etc.)
checks:
	@echo "==> Running quick checks"
	bash scripts/quick_checks.sh

# Convenience: run validate + checks
all_checks: validate checks

# Remove generated artifacts (keeps backups)
clean:
	@echo "==> Cleaning generated files"
	@rm -f $(INDEX)

help:
	@echo "Targets:"
	@echo "  make build     - Build/refresh $(CATALOG) from batches (use BATCH=\"...\" to specify files)"
	@echo "  make index     - Build $(INDEX) from $(CATALOG)"
	@echo "  make validate  - Run JSON/schema validations"
	@echo "  make checks    - Run extra sanity checks"
	@echo "  make all       - build + index + validate + checks"
	@echo "  make clean     - Remove generated index file"
