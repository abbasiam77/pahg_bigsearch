.PHONY: all index validate checks clean

all: index validate

index:
	python3 scripts/make_index_bs.py

validate:
	python3 scripts/validate_catalog.py

checks:
	bash scripts/quick_checks.sh

clean:
	rm -f index.bs
