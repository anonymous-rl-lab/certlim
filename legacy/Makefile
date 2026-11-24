.PHONY: help verify core full list test clean

help:
	@echo "make verify   check manifests, contract tests, and every paper number (seconds)"
	@echo "make core     recompute every result the paper reports, then verify"
	@echo "make full     core, plus raw-data download and feature extraction"
	@echo "make list     show the stages without running them"
	@echo "make test     repository contract tests only"

verify:
	python3 reproduce.py --tier verify

core:
	python3 reproduce.py --tier core

full:
	python3 reproduce.py --tier full

list:
	python3 reproduce.py --list

test:
	python3 -m unittest discover -s tests -v

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.py[co]' -delete
