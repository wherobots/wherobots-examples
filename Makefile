# Makefile for converting notebooks to MDX and previewing docs
#
# Prerequisites:
#   - Python 3.x
#   - Mintlify CLI: npm install -g mintlify
#   - wherobots/docs repo cloned at ../docs (relative to this repo)

# Configuration
DOCS_DIR ?= ../docs
DOCS_BRANCH ?= main
NOTEBOOKS_OUTPUT_DIR = $(DOCS_DIR)/tutorials/example-notebooks
DOCS_JSON = $(DOCS_DIR)/docs.json

# Notebook directories to convert
NOTEBOOK_DIRS = Getting_Started/ Analyzing_Data/ Reading_and_Writing_Data/ Open_Data_Connections/ scala/

.PHONY: help convert update-nav sync-docs preview preview-branch clean all

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  convert            Convert notebooks to MDX files"
	@echo "  sync-docs          Checkout and pull docs repo branch (default: main)"
	@echo "  update-nav         Update docs.json navigation"
	@echo "  preview            Start Mintlify dev server (uses main branch)"
	@echo "  preview-branch     Preview with a specific docs branch"
	@echo "                     Usage: make preview-branch DOCS_BRANCH=my-branch"
	@echo "  clean              Remove generated MDX files"
	@echo "  all                Run sync-docs, convert, update-nav, then preview"
	@echo ""
	@echo "Configuration:"
	@echo "  DOCS_DIR       Path to docs repo (default: ../docs)"
	@echo "  DOCS_BRANCH    Docs repo branch to use (default: main)"

convert: clean
	@echo "Converting notebooks to MDX..."
	python3 .github/workflows/scripts/notebook_to_mdx.py \
		$(NOTEBOOK_DIRS) \
		-o $(NOTEBOOKS_OUTPUT_DIR) \
		--exclude-prefix Raster_Inference \
		-v

update-nav:
	@echo "Updating docs.json navigation..."
	python3 .github/workflows/scripts/update_docs_navigation.py \
		--docs-json $(DOCS_JSON) \
		--notebooks-dir $(NOTEBOOKS_OUTPUT_DIR)

sync-docs:
	@echo "Syncing docs repo to $(DOCS_BRANCH) branch..."
	cd $(DOCS_DIR) && git checkout -f $(DOCS_BRANCH) && git pull

preview: sync-docs convert update-nav
	@echo "Starting Mintlify dev server..."
	@echo "Open http://localhost:3000 in your browser"
	cd $(DOCS_DIR) && npx mintlify dev

preview-branch: sync-docs convert update-nav
	@echo "Starting Mintlify dev server on $(DOCS_BRANCH) branch..."
	@echo "Open http://localhost:3000 in your browser"
	cd $(DOCS_DIR) && npx mintlify dev

clean:
	@echo "Removing generated MDX files..."
	rm -rf $(NOTEBOOKS_OUTPUT_DIR)

all: sync-docs convert update-nav preview
