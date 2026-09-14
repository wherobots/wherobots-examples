#!/bin/bash

# Define the marker for the section we want to replace
START_MARKER="## Repository structure"
END_MARKER="^##"

# Create temporary file
temp_file=$(mktemp)

# List the files the structure is built from. Using git-tracked files rather
# than walking the working directory keeps untracked local directories (scratch
# work, leftovers from a branch switch) out of the README. The exclusions match
# what `tree -I` filtered before: dotfiles, scripts/, assets/, and any README.md.
file_list=$(mktemp)
git ls-files | grep -Ev '^\.|(^|/)README\.md$|(^|/)(scripts|assets)(/|$)' > "$file_list"

# Process the README.md file
awk -v start="$START_MARKER" -v end="$END_MARKER" -v list="$file_list" '
    !found && $0 ~ start {
        print $0
        print ""
        print "```"
        system("LC_ALL=C tree -L 4 --fromfile . < \"" list "\" | sed '\''$d'\''")
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

rm -f "$file_list"

# Compare the original and modified files
if diff "./README.md" "$temp_file" > /dev/null; then
    echo "No changes detected."
else
    echo "Changes detected. Exiting with failure."
    mv "$temp_file" "./README.md"
    exit 1
fi
