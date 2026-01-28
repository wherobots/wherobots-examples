# Makefile for converting notebooks to MDX and previewing docs
#
# Prerequisites:
#   - Python 3.x
#   - Mintlify CLI: npm install -g mintlify
#   - wherobots/docs repo cloned at ../docs (relative to this repo)

# Configuration
DOCS_DIR ?= ../docs
NOTEBOOKS_OUTPUT_DIR = $(DOCS_DIR)/tutorials/example-notebooks
DOCS_JSON = $(DOCS_DIR)/docs.json

# Dynamically find all directories containing notebooks
NOTEBOOK_DIRS = $(shell find . -name "*.ipynb" -type f | xargs -I {} dirname {} | sort -u | grep -v ".ipynb_checkpoints")

.PHONY: help cleanup convert update-nav preview clean all

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  cleanup     Remove orphaned MDX files (deleted/renamed notebooks)"
	@echo "  convert     Convert notebooks to MDX files"
	@echo "  update-nav  Update docs.json navigation"
	@echo "  preview     Start Mintlify dev server"
	@echo "  clean       Remove generated MDX files"
	@echo "  all         Run cleanup, convert, update-nav, then preview"
	@echo ""
	@echo "Configuration:"
	@echo "  DOCS_DIR    Path to docs repo (default: ../docs)"

cleanup:
	@echo "Cleaning up orphaned MDX files..."
	python3 .github/workflows/scripts/cleanup_orphaned_mdx.py \
		$(NOTEBOOK_DIRS) \
		--mdx-dir $(NOTEBOOKS_OUTPUT_DIR) \
		--exclude-prefix Raster_Inference \
		-v

convert:
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

preview: cleanup convert update-nav
	@echo "Starting Mintlify dev server..."
	@echo "Open http://localhost:3000 in your browser"
	cd $(DOCS_DIR) && mintlify dev

clean:
	@echo "Removing generated MDX files..."
	rm -rf $(NOTEBOOKS_OUTPUT_DIR)

all: cleanup convert update-nav preview
