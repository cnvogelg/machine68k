.PHONY: help setup remove test format

help:
	@echo "setup     local pip install of package"
	@echo "remove    uninstall pip install"
	@echo "test      run pytest suite"
	@echo "format    format source code"

setup:
	pip install -e .

remove:
	pip uninstall machine68k

test:
	pytest test

format:
	black .
