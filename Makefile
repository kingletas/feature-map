# feature-map: draw what a tool does as one picture, from a plain outline.
#
# Run `make` with no arguments for the list.

SHELL         := /usr/bin/env bash
.SHELLFLAGS   := -eu -o pipefail -c
.DEFAULT_GOAL := help

PREFIX ?= $(HOME)/bin
FM     ?= ./bin/feature-map

.PHONY: help
help: ## Show this help
	@echo
	@echo "  feature-map: draw what a tool does as one picture"
	@echo
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "  Draw one:   make map SPEC=examples/notebook.md OUT=local.d/notebook.png"
	@echo

.PHONY: check
check: test ## Compile, lint where available, and run the tests
	@python3 -m py_compile $(FM)
	@if command -v ruff >/dev/null; then ruff check bin tests; else echo "ruff not installed, lint skipped"; fi

.PHONY: test
test: ## Run the tests, on invented outlines
	@python3 -m unittest discover -s tests -q

.PHONY: map
map: ## Draw SPEC into OUT (the format follows OUT's extension)
	@if [ -z "$(SPEC)" ] || [ -z "$(OUT)" ]; then \
		echo "usage: make map SPEC=examples/notebook.md OUT=local.d/notebook.png"; exit 2; fi
	@$(FM) render "$(SPEC)" -o "$(OUT)"
	@echo "wrote $(OUT)"

.PHONY: example
example: ## Draw the bundled example into local.d/
	@mkdir -p local.d
	@$(FM) render examples/notebook.md -o local.d/notebook.svg
	@$(FM) render examples/notebook.md -o local.d/notebook.png || echo "png skipped: no Chromium-based browser found"
	@echo "wrote local.d/notebook.*"

.PHONY: install
install: ## Install the command into PREFIX (default ~/bin)
	@install -d "$(PREFIX)"
	@install -m 0755 $(FM) "$(PREFIX)/feature-map"
	@echo "installed $(PREFIX)/feature-map"

.PHONY: uninstall
uninstall: ## Remove the installed command
	@rm -f "$(PREFIX)/feature-map"
	@echo "removed $(PREFIX)/feature-map"
