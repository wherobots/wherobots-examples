#!/bin/bash

# Define the marker for the section we want to replace
START_MARKER="## Repository structure"
END_MARKER="^##"

# Create temporary file
temp_file=$(mktemp)

# Process the README.md file
awk -v start="$START_MARKER" -v end="$END_MARKER" '
    !found && $0 ~ start {
        print $0
        print ""
        print "```"
        system("tree -L 2 -I \"scripts|README.md|assets\" | sed '\''$d'\''")
        print "```"
        print ""
        found=1
        next
    }
    found && $0 ~ end {
        found=0
    }
    !found {
        print $0
    }
' "./README.md" > "$temp_file"

# Compare the original and modified files
if diff "./README.md" "$temp_file" > /dev/null; then
    echo "No changes detected."
else
    echo "Changes detected. Exiting with failure."
    mv "$temp_file" "./README.md"
    exit 1
fi
