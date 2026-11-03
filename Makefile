UV ?= uv

.PHONY: help setup remove build test format fix fix-unsafe check sdist bdist upload clean clean-all
.PHONY: html clean-html

help:
	@echo "init      install dev packages"
	@echo "setup     local uv install of package"
	@echo "remove    uninstall uv install"
	@echo "test      run pytest suite"
	@echo "format    format source code"
	@echo "fix       apply Ruff lint fixes"
	@echo "fix-unsafe apply Ruff lint fixes, including unsafe fixes"
	@echo "check     check formatting and lint"
	@echo "sdist     build source dist"
	@echo "bdist     build binary dist"
	@echo "upload    dist to pypi"
	@echo "html      generate cython html output"
	@echo "clean     clean"
	@echo "clean-all remove all"
	@echo "clean-html clean html files"

init:
	$(UV) python install "$$(cat .python-version)"
	$(UV) pip install --upgrade -r requirements-dev.txt

setup:
	$(UV) pip install -e .

remove:
	$(UV) pip uninstall machine68k

build:
	$(UV) run --with setuptools --with packaging --with cython python setup.py build

test:
	$(UV) run pytest test

format:
	$(UV) run ruff format .

fix:
	$(UV) run ruff check --fix .

fix-unsafe:
	$(UV) run ruff check --fix --unsafe-fixes .

check:
	$(UV) run ruff format --check .
	$(UV) run ruff check .

sdist:
	$(UV) build --sdist

bdist:
	$(UV) build --wheel

upload: sdist
	$(UV) publish dist/*

html:
	$(UV) run cython --module-name machine68k src/mach.pyx -a

clean:
	$(UV) run --with setuptools --with packaging --with cython python setup.py clean

clean-all:
	rm -rf build/ dist/

clean-html:
	rm -f src/*.html
