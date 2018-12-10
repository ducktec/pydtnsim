help:
	@echo "The following targets are available:"
	@echo
	@echo "test:  Run unittests with pytest"
	@echo "docs:  Genertate HTML Sphinx documentation"

test:
	pytest tests/

docs:
	cd docs; make html

.PHONY: test docs
