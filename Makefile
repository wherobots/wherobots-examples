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

# Notebook directories to convert
NOTEBOOK_DIRS = Getting_Started/ Analyzing_Data/ Reading_and_Writing_Data/ Open_Data_Connections/ scala/

.PHONY: help convert update-nav preview clean all

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  convert     Convert notebooks to MDX files"
	@echo "  update-nav  Update docs.json navigation"
	@echo "  preview     Start Mintlify dev server"
	@echo "  clean       Remove generated MDX files"
	@echo "  all         Run convert, update-nav, then preview"
	@echo ""
	@echo "Configuration:"
	@echo "  DOCS_DIR    Path to docs repo (default: ../docs)"

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

preview: convert update-nav
	@echo "Starting Mintlify dev server..."
	@echo "Open http://localhost:3000 in your browser"
	cd $(DOCS_DIR) && mintlify dev

clean:
	@echo "Removing generated MDX files..."
	rm -rf $(NOTEBOOKS_OUTPUT_DIR)

all: convert update-nav preview
