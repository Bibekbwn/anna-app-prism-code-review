#!/usr/bin/env python
"""Update quality_metrics.py to add language-specific accessibility levels."""

import sys

# Read the original file
with open("local-companion/quality_metrics.py", "r", encoding="utf-8") as f:
    content = f.read()

# Check if LANGUAGE_ACCESSIBILITY_LEVEL already exists
if "LANGUAGE_ACCESSIBILITY_LEVEL" in content:
    print("LANGUAGE_ACCESSIBILITY_LEVEL already exists, skipping.")
    sys.exit(0)

# New content to insert after WEB_LANGUAGE line
new_section = '''# Language-specific accessibility check levels
# "full" = all checks (JS/TS), "basic" = core checks only (all other languages)
LANGUAGE_ACCESSIBILITY_LEVEL = {
    "Python": "basic",
    "JavaScript / TypeScript": "full",
    "Go": "basic",
    "Rust": "basic",
    "Java": "basic",
    "C#": "basic",
    "C": "basic",
    "C++": "basic",
    "Ruby": "basic",
    "PHP": "basic",
    "Kotlin": "basic",
    "Swift": "basic",
}

'''

# Find the position after WEB_LANGUAGE line and insert
lines = content.split("\n")
new_lines = []
inserted = False

for i, line in enumerate(lines):
    new_lines.append(line)
    if not inserted and line.strip() == 'WEB_LANGUAGE = "JavaScript / TypeScript"':
        new_lines.append("")  # Add blank line
        new_lines.append(new_section)
        inserted = True

if not inserted:
    print("Could not find WEB_LANGUAGE line to insert after.")
    sys.exit(1)

# Write back
with open("local-companion/quality_metrics.py", "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))

print("Successfully updated quality_metrics.py")