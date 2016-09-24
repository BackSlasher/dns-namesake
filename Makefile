.PHONY: venv

venv:
	virtualenv .
	bin/pip install -e .[dev]
