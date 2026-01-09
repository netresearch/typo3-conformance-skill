#!/usr/bin/env bash

#
# TYPO3 Documentation Conformance Checker
#
# Delegates to typo3-docs skill references for documentation validation
# This ensures conformance checks stay in sync with documentation standards
#

set -e

PROJECT_DIR="${1:-.}"
cd "${PROJECT_DIR}"

# Find typo3-docs skill reference (check common plugin cache locations)
DOCS_SKILL_REF=""
for cache_dir in \
    "$HOME/.claude/plugins/cache/netresearch-claude-code-marketplace/typo3-docs/"*/skills/typo3-docs/references \
    "$HOME/.claude/skills/typo3-docs/references" \
    "/opt/claude-skills/typo3-docs/references"
do
    if [ -f "$cache_dir/file-structure.md" ]; then
        DOCS_SKILL_REF="$cache_dir"
        break
    fi
done

echo "## Documentation Conformance"
echo ""

# Check if we found the typo3-docs skill
if [ -n "$DOCS_SKILL_REF" ]; then
    echo "> Using typo3-docs skill references from: $(dirname "$DOCS_SKILL_REF")"
    echo ""
fi

echo "### Required Documentation Files"
echo ""

# Check Documentation/Index.rst (required entry point)
if [ -f "Documentation/Index.rst" ]; then
    echo "- ✅ Documentation/Index.rst present"
elif [ -f "Documentation/Index.md" ]; then
    echo "- ✅ Documentation/Index.md present (Markdown mode)"
elif [ -f "README.rst" ] || [ -f "README.md" ]; then
    echo "- ⚠️  Only README found (single-file documentation mode)"
else
    echo "- ❌ No documentation entry point (need Index.rst, Index.md, or README)"
fi

# Check guides.xml (modern) vs Settings.cfg (legacy)
# Per typo3-docs skill file-structure.md: guides.xml is REQUIRED
if [ -f "Documentation/guides.xml" ]; then
    echo "- ✅ Documentation/guides.xml present (modern PHP-based rendering)"

    # Validate guides.xml has required elements
    if grep -q 'theme="typo3docs"' "Documentation/guides.xml" 2>/dev/null; then
        echo "  - ✅ Uses typo3docs theme"
    else
        echo "  - ⚠️  Should use theme=\"typo3docs\""
    fi

    if grep -q '<project' "Documentation/guides.xml" 2>/dev/null; then
        echo "  - ✅ Has <project> element"
    else
        echo "  - ⚠️  Missing <project> element"
    fi

elif [ -f "Documentation/Settings.cfg" ]; then
    echo "- ⚠️  Documentation/Settings.cfg present (LEGACY)"
    echo "  - ℹ️  Migrate to guides.xml for modern PHP-based rendering"
    echo "  - ℹ️  See: https://docs.typo3.org/m/typo3/docs-how-to-document/main/en-us/"
else
    echo "- ❌ No documentation config (need Documentation/guides.xml)"
fi

echo ""
echo "### Documentation Structure"
echo ""

# Check for Index.rst in subdirectories (required per typo3-docs skill)
if [ -d "Documentation" ]; then
    missing_index=()
    for dir in Documentation/*/; do
        if [ -d "$dir" ]; then
            dirname=$(basename "$dir")
            # Skip special directories
            if [[ "$dirname" == _* ]] || [[ "$dirname" == "Images" ]]; then
                continue
            fi
            if [ ! -f "${dir}Index.rst" ] && [ ! -f "${dir}Index.md" ]; then
                missing_index+=("$dirname")
            fi
        fi
    done

    if [ ${#missing_index[@]} -eq 0 ]; then
        echo "- ✅ All subdirectories have Index.rst"
    else
        echo "- ⚠️  Missing Index.rst in: ${missing_index[*]}"
    fi
fi

# Check for Images directory with screenshots
if [ -d "Documentation/Images" ]; then
    img_count=$(find "Documentation/Images" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.gif" -o -name "*.svg" \) 2>/dev/null | wc -l)
    if [ "$img_count" -gt 0 ]; then
        echo "- ✅ Documentation/Images/ present ($img_count image(s))"
    else
        echo "- ⚠️  Documentation/Images/ exists but empty"
    fi
else
    echo "- ℹ️  No Documentation/Images/ (screenshots recommended)"
fi

# Check for .editorconfig in Documentation
if [ -f "Documentation/.editorconfig" ]; then
    echo "- ✅ Documentation/.editorconfig present"
else
    echo "- ⚠️  Documentation/.editorconfig missing (recommended for consistent formatting)"
fi

echo ""
echo "---"
echo ""

# Return success (documentation issues are warnings, not failures)
exit 0
