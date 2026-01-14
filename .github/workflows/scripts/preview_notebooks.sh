#!/bin/bash
#
# Preview converted notebook MDX files using Mintlify
#
# This script converts notebooks to MDX and starts a local Mintlify preview server.
# It requires the Mintlify CLI to be installed: npm i -g mint
#
# Usage:
#   ./preview_notebooks.sh [options]
#
# Options:
#   -n, --notebook <path>  Convert and preview a specific notebook
#   -a, --all              Convert all notebooks (default)
#   -p, --port <port>      Port for preview server (default: 3000)
#   -o, --output <dir>     Output directory (default: .preview)
#   -h, --help             Show this help message
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PREVIEW_DIR="${PREVIEW_DIR:-$REPO_ROOT/.preview}"
CONVERT_SCRIPT="$SCRIPT_DIR/convert_notebook_to_mdx.py"
NAVIGATION_SCRIPT="$SCRIPT_DIR/generate_navigation.py"

# Default values
PORT=3000
CONVERT_ALL=true
SPECIFIC_NOTEBOOK=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_help() {
    cat << EOF
Preview converted notebook MDX files using Mintlify

Usage:
  ./preview_notebooks.sh [options]

Options:
  -n, --notebook <path>  Convert and preview a specific notebook
  -a, --all              Convert all notebooks (default)
  -p, --port <port>      Port for preview server (default: 3000)
  -o, --output <dir>     Output directory (default: .preview)
  -h, --help             Show this help message

Examples:
  # Preview all notebooks
  ./preview_notebooks.sh

  # Preview a specific notebook
  ./preview_notebooks.sh -n Getting_Started/Part_1_Loading_Data.ipynb

  # Preview on a different port
  ./preview_notebooks.sh -p 3333

Requirements:
  - Python 3.8+
  - Mintlify CLI: npm i -g mint
EOF
}

check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
        exit 1
    fi

    # Check Mintlify CLI
    if ! command -v mint &> /dev/null; then
        echo -e "${RED}Error: Mintlify CLI is not installed.${NC}"
        echo -e "Install it with: ${GREEN}npm i -g mint${NC}"
        exit 1
    fi

    echo -e "${GREEN}All dependencies satisfied.${NC}"
}

setup_preview_directory() {
    echo -e "${BLUE}Setting up preview directory: $PREVIEW_DIR${NC}"

    # Create preview directory structure
    mkdir -p "$PREVIEW_DIR/examples"

    # Create minimal docs.json for Mintlify preview
    cat > "$PREVIEW_DIR/docs.json" << 'DOCSJSON'
{
  "$schema": "https://mintlify.com/schema.json",
  "name": "Wherobots Examples Preview",
  "logo": {
    "dark": "https://wherobots.com/wp-content/uploads/2023/06/wherobots-logo-white.svg",
    "light": "https://wherobots.com/wp-content/uploads/2023/06/wherobots-logo.svg"
  },
  "favicon": "/favicon.svg",
  "colors": {
    "primary": "#0D9373",
    "light": "#07C983",
    "dark": "#0D9373",
    "anchors": {
      "from": "#0D9373",
      "to": "#07C983"
    }
  },
  "navigation": {
    "tabs": [
      {
        "tab": "Examples",
        "icon": "book-open-cover",
        "groups": []
      }
    ]
  },
  "footerSocials": {
    "github": "https://github.com/wherobots",
    "website": "https://wherobots.com"
  }
}
DOCSJSON

    # Create a simple favicon
    cat > "$PREVIEW_DIR/favicon.svg" << 'FAVICON'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="45" fill="#0D9373"/>
  <text x="50" y="65" font-size="50" text-anchor="middle" fill="white" font-family="Arial, sans-serif">W</text>
</svg>
FAVICON

    # Create an index page
    cat > "$PREVIEW_DIR/examples/index.mdx" << 'INDEX'
---
title: "Wherobots Examples"
description: "Explore Jupyter notebook examples for Wherobots"
icon: "house"
---

# Welcome to Wherobots Examples

This documentation contains examples converted from Jupyter notebooks in the 
[wherobots-examples](https://github.com/wherobots/wherobots-examples) repository.

## Categories

<CardGroup cols={2}>
  <Card title="Getting Started" icon="rocket" href="/examples/Getting_Started">
    Learn the basics of Wherobots with introductory tutorials.
  </Card>
  <Card title="Analyzing Data" icon="chart-line" href="/examples/Analyzing_Data">
    Explore spatial analysis techniques and algorithms.
  </Card>
  <Card title="Reading & Writing Data" icon="database" href="/examples/Reading_and_Writing_Data">
    Work with various spatial data formats and sources.
  </Card>
  <Card title="Open Data Connections" icon="plug" href="/examples/Open_Data_Connections">
    Connect to open data sources like Overture Maps and ESA WorldCover.
  </Card>
</CardGroup>
INDEX

    echo -e "${GREEN}Preview directory ready.${NC}"
}

convert_notebooks() {
    echo -e "${BLUE}Converting notebooks to MDX...${NC}"

    local output_dir="$PREVIEW_DIR/examples"

    if [ -n "$SPECIFIC_NOTEBOOK" ]; then
        # Convert specific notebook
        local notebook_path="$REPO_ROOT/$SPECIFIC_NOTEBOOK"
        if [ ! -f "$notebook_path" ]; then
            echo -e "${RED}Error: Notebook not found: $notebook_path${NC}"
            exit 1
        fi

        # Determine category from path
        local category=$(dirname "$SPECIFIC_NOTEBOOK" | cut -d'/' -f1)
        local subdir="$output_dir/$category"
        mkdir -p "$subdir"

        python3 "$CONVERT_SCRIPT" "$notebook_path" "$subdir" --category "$category" --verbose
    else
        # Convert all notebooks
        echo "Scanning for notebooks in: $REPO_ROOT"

        local count=0
        while IFS= read -r -d '' notebook; do
            local rel_path="${notebook#$REPO_ROOT/}"
            local filename=$(basename "$notebook")

            # Skip excluded notebooks
            if [[ "$filename" == Raster_Inference* ]]; then
                echo -e "${YELLOW}Skipping: $rel_path${NC}"
                continue
            fi

            # Determine category and output path
            local category=$(dirname "$rel_path" | cut -d'/' -f1)
            local subdir="$output_dir/$category"
            mkdir -p "$subdir"

            echo "Converting: $rel_path"
            python3 "$CONVERT_SCRIPT" "$notebook" "$subdir" --category "$category"

            ((count++))
        done < <(find "$REPO_ROOT" -name "*.ipynb" -type f -print0 | sort -z)

        echo -e "${GREEN}Converted $count notebooks.${NC}"
    fi
}

generate_navigation() {
    echo -e "${BLUE}Generating navigation...${NC}"

    python3 "$NAVIGATION_SCRIPT" "$PREVIEW_DIR/examples" "$PREVIEW_DIR/docs.json"

    echo -e "${GREEN}Navigation generated.${NC}"
}

start_preview() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Starting Mintlify Preview Server${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "Preview URL: ${BLUE}http://localhost:$PORT${NC}"
    echo -e "Press ${YELLOW}Ctrl+C${NC} to stop the server."
    echo ""

    cd "$PREVIEW_DIR"
    mint dev --port "$PORT"
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Preview server stopped.${NC}"
    echo -e "Preview files are in: ${BLUE}$PREVIEW_DIR${NC}"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--notebook)
            SPECIFIC_NOTEBOOK="$2"
            CONVERT_ALL=false
            shift 2
            ;;
        -a|--all)
            CONVERT_ALL=true
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -o|--output)
            PREVIEW_DIR="$2"
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_help
            exit 1
            ;;
    esac
done

# Trap Ctrl+C to cleanup
trap cleanup EXIT

# Main execution
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Wherobots Notebook Preview Tool        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

check_dependencies
setup_preview_directory
convert_notebooks
generate_navigation
start_preview
