.PHONY: docs install help

help:
	@echo "The following targets are available:"
	@echo
	@echo "test:  Run unittests with pytest"
	@echo "docs:  Genertate HTML Sphinx documentation"

install:
	pip install pipenv --upgrade
	pipenv install --dev

docs:
	cd docs; make html
