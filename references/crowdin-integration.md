# TYPO3 Crowdin Integration Validation

**Purpose**: Validate TYPO3 extension Crowdin integration against official TYPO3 standards for centralized translation management.

**Official Reference**: https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/ApiOverview/Localization/TranslationServer/Crowdin/ExtensionIntegration.html

## Overview

TYPO3 uses a **centralized translation server architecture** where extensions integrate with TYPO3's Crowdin organization, not standalone Crowdin projects. This ensures consistency across the TYPO3 ecosystem and enables the TYPO3 community's translation workflow.

## Critical Architecture Understanding

```
Extension Repository (GitHub/GitLab/BitBucket)
    ↓ Push to main branch
GitHub Actions: Upload sources to Crowdin
    ↓
TYPO3 Central Crowdin Organization
    ↓ Translators work via TYPO3's Crowdin instance
Crowdin Native Integration (Option A) OR GitHub Actions Download (Option B)
    ↓ Creates PR with translations via service branch (l10n_*)
Extension Repository
    ↓ Maintainer reviews and merges PR
Translations committed to main branch
```

**Key Difference from Standalone Crowdin**:
- ❌ Extensions do NOT create their own Crowdin projects
- ✅ Extensions are added to TYPO3's centralized Crowdin organization
- ✅ TYPO3 localization team manages project setup
- ✅ Translations flow through TYPO3's established ecosystem

## Prerequisites

1. **Repository Hosting**: GitHub, GitLab (SaaS or self-managed), or BitBucket
2. **TYPO3 Org Membership**: Extension must be added by TYPO3 localization team
3. **Contact Channel**: Slack `#typo3-localization-team`
4. **Branch Support**: TYPO3 currently supports one branch/version (typically `main`)

## Configuration File Validation (crowdin.yml)

### Required Structure

```yaml
preserve_hierarchy: 1
files:
  - source: /Resources/Private/Language/*.xlf
    translation: /%original_path%/%two_letters_code%.%original_file_name%
    ignore:
      - /**/%two_letters_code%.%original_file_name%
```

### Validation Checklist

**✅ MUST HAVE:**
- [ ] `preserve_hierarchy: 1` at top level (maintains directory structure)
- [ ] Source pattern uses wildcard: `/Resources/Private/Language/*.xlf`
- [ ] Translation pattern uses variables: `/%original_path%/%two_letters_code%.%original_file_name%`
- [ ] Ignore directive present: `/**/%two_letters_code%.%original_file_name%`

**❌ MUST NOT HAVE:**
- [ ] `project_id_env` or `api_token_env` (belongs in GitHub Actions workflow)
- [ ] `languages_mapping` (Crowdin handles automatically)
- [ ] `type: xliff` (unnecessary, detected automatically)
- [ ] `update_option`, `content_segmentation`, `save_translations` (defaults work)
- [ ] Hardcoded filenames like `locallang_be.xlf` (use wildcard `*.xlf`)

### Common Mistakes

**Mistake 1: Hardcoded Single File**
```yaml
# ❌ WRONG - Not extensible
- source: /Resources/Private/Language/locallang_be.xlf
  translation: /Resources/Private/Language/%two_letters_code%.locallang_be.xlf
```

```yaml
# ✅ CORRECT - Supports multiple files
- source: /Resources/Private/Language/*.xlf
  translation: /%original_path%/%two_letters_code%.%original_file_name%
```

**Mistake 2: Over-Configuration**
```yaml
# ❌ WRONG - Unnecessary complexity
project_id_env: CROWDIN_PROJECT_ID
api_token_env: CROWDIN_PERSONAL_TOKEN
preserve_hierarchy: true
files:
  - source: /Resources/Private/Language/locallang_be.xlf
    translation: /Resources/Private/Language/%two_letters_code%.locallang_be.xlf
    languages_mapping:
      two_letters_code:
        de: de
        es: es
    type: xliff
    update_option: update_as_unapproved
    content_segmentation: true
```

```yaml
# ✅ CORRECT - Simple TYPO3 standard
preserve_hierarchy: 1
files:
  - source: /Resources/Private/Language/*.xlf
    translation: /%original_path%/%two_letters_code%.%original_file_name%
    ignore:
      - /**/%two_letters_code%.%original_file_name%
```

**Mistake 3: Missing Ignore Directive**
```yaml
# ❌ WRONG - Will re-upload translations as sources
- source: /Resources/Private/Language/*.xlf
  translation: /%original_path%/%two_letters_code%.%original_file_name%
```

```yaml
# ✅ CORRECT - Ignores existing translations
- source: /Resources/Private/Language/*.xlf
  translation: /%original_path%/%two_letters_code%.%original_file_name%
  ignore:
    - /**/%two_letters_code%.%original_file_name%
```

### Validation Script

```bash
#!/bin/bash
# Validate crowdin.yml against TYPO3 standards

echo "Validating crowdin.yml for TYPO3 compliance..."

# Check file exists
if [[ ! -f crowdin.yml ]]; then
  echo "❌ crowdin.yml not found"
  exit 1
fi

# Check preserve_hierarchy
if grep -q "preserve_hierarchy: 1" crowdin.yml; then
  echo "✅ preserve_hierarchy: 1 present"
else
  echo "❌ Missing preserve_hierarchy: 1"
fi

# Check wildcard source pattern
if grep -q "/Resources/Private/Language/\*.xlf" crowdin.yml; then
  echo "✅ Wildcard source pattern (*.xlf) present"
else
  echo "❌ Missing wildcard pattern or hardcoded filename"
fi

# Check translation pattern with variables
if grep -q "%original_path%.*%two_letters_code%.*%original_file_name%" crowdin.yml; then
  echo "✅ Translation pattern uses TYPO3 variables"
else
  echo "❌ Translation pattern not TYPO3-compliant"
fi

# Check ignore directive
if grep -q "ignore:" crowdin.yml; then
  echo "✅ Ignore directive present"
else
  echo "❌ Missing ignore directive"
fi

# Check for non-standard fields (should not be present)
if grep -qE "project_id_env|api_token_env|languages_mapping|type:|update_option|content_segmentation" crowdin.yml; then
  echo "⚠️  Non-standard fields detected (remove for TYPO3 compliance)"
fi

# Check file length (should be ~5-7 lines)
line_count=$(wc -l < crowdin.yml)
if [[ $line_count -le 10 ]]; then
  echo "✅ Configuration is concise ($line_count lines)"
else
  echo "⚠️  Configuration is verbose ($line_count lines, TYPO3 standard is ~6 lines)"
fi
```

## GitHub Actions Workflow Validation

### TYPO3-Standard Workflow

**Option A: Simple Upload (Recommended for GitHub)**
```yaml
name: Crowdin

on:
  push:
    branches:
      - main

jobs:
  sync:
    name: Synchronize with Crowdin
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Upload sources
        uses: crowdin/github-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          config: 'crowdin.yml'
          project_id: ${{ secrets.CROWDIN_PROJECT_ID }}
          token: ${{ secrets.CROWDIN_PERSONAL_TOKEN }}
```

**Option B: Native Crowdin-GitHub Integration (No workflow needed)**
- Configure in Crowdin project settings → Integrations
- Crowdin handles both upload and download automatically
- Creates PRs via service branch (e.g., `l10n_main`)

### Validation Checklist

**✅ CORRECT PATTERNS:**
- [ ] Single job named "sync" or similar
- [ ] Triggers on push to main branch only
- [ ] Uses `actions/checkout@v4` (or latest)
- [ ] Uses `crowdin/github-action@v2` (or latest)
- [ ] Provides `CROWDIN_PROJECT_ID` and `CROWDIN_PERSONAL_TOKEN` via secrets
- [ ] References `crowdin.yml` config file
- [ ] GITHUB_TOKEN provided (for action permissions)

**❌ INCORRECT PATTERNS:**
- [ ] Multiple jobs (upload AND download)
- [ ] Cron schedule for downloading translations
- [ ] `create_pull_request: true` in workflow (handled by Crowdin's native integration)
- [ ] Path filters for source files (unnecessary complexity)
- [ ] Manual PR creation logic in workflow
- [ ] Complex if conditions based on event types

### Common Mistakes

**Mistake 1: Download Job in Workflow**
```yaml
# ❌ WRONG - Conflicts with Crowdin's native GitHub integration
jobs:
  upload-sources:
    # ... upload logic

  download-translations:  # ← Should NOT exist
    # ... download and PR creation logic
```

```yaml
# ✅ CORRECT - Single job for upload only
jobs:
  sync:
    name: Synchronize with Crowdin
    # ... upload sources only
```

**Mistake 2: Cron-Based Translation Downloads**
```yaml
# ❌ WRONG - TYPO3 uses Crowdin's native integration for downloads
on:
  push:
    branches: [main]
  schedule:  # ← Should NOT exist for TYPO3 extensions
    - cron: '0 2 * * *'
```

```yaml
# ✅ CORRECT - Upload on push only
on:
  push:
    branches:
      - main
```

**Mistake 3: Path Filters**
```yaml
# ❌ UNNECESSARY - Adds complexity without benefit
on:
  push:
    branches: [main]
    paths:
      - 'Resources/Private/Language/locallang_be.xlf'
```

```yaml
# ✅ BETTER - Simple trigger
on:
  push:
    branches:
      - main
```

### Validation Script

```bash
#!/bin/bash
# Validate GitHub workflow for TYPO3 Crowdin compliance

workflow_file=".github/workflows/crowdin.yml"
[[ ! -f "$workflow_file" ]] && workflow_file=".github/workflows/crowdin.yaml"
[[ ! -f "$workflow_file" ]] && workflow_file=".github/workflows/crowdin-sync.yml"

if [[ ! -f "$workflow_file" ]]; then
  echo "⚠️  No Crowdin workflow found (using native integration?)"
  exit 0
fi

echo "Validating $workflow_file for TYPO3 compliance..."

# Check for download job (should NOT exist)
if grep -q "download.*translation" "$workflow_file"; then
  echo "❌ Download job detected (conflicts with TYPO3's Crowdin integration)"
else
  echo "✅ No download job (correct - handled by Crowdin)"
fi

# Check for cron schedule (should NOT exist)
if grep -q "schedule:" "$workflow_file"; then
  echo "❌ Cron schedule detected (not needed for TYPO3 extensions)"
else
  echo "✅ No cron schedule (correct)"
fi

# Check for single job
job_count=$(grep -c "^  [a-z_-]*:$" "$workflow_file")
if [[ $job_count -eq 1 ]]; then
  echo "✅ Single job present (correct)"
else
  echo "⚠️  Multiple jobs detected ($job_count jobs)"
fi

# Check for required secrets
if grep -q "CROWDIN_PROJECT_ID" "$workflow_file" && grep -q "CROWDIN_PERSONAL_TOKEN" "$workflow_file"; then
  echo "✅ Required secrets referenced"
else
  echo "❌ Missing required secrets (CROWDIN_PROJECT_ID, CROWDIN_PERSONAL_TOKEN)"
fi

# Check for checkout action version
if grep -q "actions/checkout@v4" "$workflow_file"; then
  echo "✅ Using checkout@v4 (current)"
elif grep -q "actions/checkout@v3" "$workflow_file"; then
  echo "⚠️  Using checkout@v3 (consider upgrading to v4)"
fi

# Check for crowdin action version
if grep -q "crowdin/github-action@v2" "$workflow_file"; then
  echo "✅ Using crowdin/github-action@v2"
elif grep -q "crowdin/github-action@v1" "$workflow_file"; then
  echo "⚠️  Using crowdin/github-action@v1 (upgrade to v2)"
fi
```

## Translation File Structure

### File Naming Convention

**Source files** (English):
```
Resources/Private/Language/locallang.xlf
Resources/Private/Language/locallang_be.xlf
Resources/Private/Language/locallang_db.xlf
```

**Translation files**:
```
Resources/Private/Language/de.locallang.xlf
Resources/Private/Language/de.locallang_be.xlf
Resources/Private/Language/de.locallang_db.xlf
```

Pattern: `{two_letter_code}.{original_filename}.xlf`

### XLIFF Structure Requirements

**Critical**: Translation files MUST include both `<source>` and `<target>` elements for optimal Crowdin import.

```xml
<!-- ✅ CORRECT - Has both source and target -->
<trans-unit id="labels.ckeditor.title" xml:space="preserve">
    <source>Image Title</source>
    <target>Bildtitel</target>
</trans-unit>

<!-- ❌ WRONG - Missing source element -->
<trans-unit id="labels.ckeditor.title" xml:space="preserve">
    <target>Bildtitel</target>
</trans-unit>
```

### Validation Script

```bash
#!/bin/bash
# Validate translation file structure

echo "Validating translation file structure..."

# Check source files (no language prefix)
source_files=$(find Resources/Private/Language/ -maxdepth 1 -name "*.xlf" ! -name "*.*\.xlf" 2>/dev/null)
if [[ -n "$source_files" ]]; then
  echo "✅ Source files found:"
  echo "$source_files" | sed 's/^/  /'
else
  echo "❌ No source files found in Resources/Private/Language/"
fi

# Check translation files (with language prefix)
translation_files=$(find Resources/Private/Language/ -maxdepth 1 -name "[a-z][a-z].*.xlf" 2>/dev/null)
if [[ -n "$translation_files" ]]; then
  echo "✅ Translation files found:"
  echo "$translation_files" | sed 's/^/  /'
else
  echo "⚠️  No translation files found (expected for new extensions)"
fi

# Validate XLIFF structure (both source and target elements)
for xlf in Resources/Private/Language/[a-z][a-z].*.xlf; do
  [[ ! -f "$xlf" ]] && continue

  if grep -q "<source>" "$xlf" && grep -q "<target>" "$xlf"; then
    echo "✅ $xlf has both <source> and <target> elements"
  else
    echo "❌ $xlf missing <source> or <target> elements"
  fi
done
```

## Project Setup Workflow

### Step 1: Initial Contact

Contact TYPO3 localization team via Slack:
- Channel: `#typo3-localization-team`
- Provide: Extension name, maintainer email, repository URL
- Request: Add extension to TYPO3's Crowdin organization

### Step 2: Integration Choice

**Option A: Native Crowdin-GitHub Integration** (Recommended)
1. In Crowdin project settings → Integrations
2. Select "Source and translation files mode"
3. Authorize GitHub access and select repository
4. Configure branch (typically `main`)
5. Accept service branch name (e.g., `l10n_main`)
6. Specify `crowdin.yml` as configuration file
7. Enable "One-time translation import" for existing translations
8. Disable "Push Sources" (managed in extension repository)

**Option B: GitHub Actions Workflow**
1. Create `.github/workflows/crowdin.yml` with upload job
2. Configure `CROWDIN_PROJECT_ID` and `CROWDIN_PERSONAL_TOKEN` secrets
3. Translations still downloaded via Crowdin's native integration

### Step 3: Initial Translation Upload

For existing translations, prepare ZIP file:
```bash
zip translations.zip Resources/Private/Language/*.*.xlf
```
Upload via Crowdin UI → Translations tab

### Step 4: Verify Workflow

1. Push source file change to main branch
2. Verify GitHub Actions uploads to Crowdin (if using Option B)
3. Wait for translations to complete in Crowdin
4. Verify Crowdin creates PR with translations via service branch
5. Review and merge translation PR

## Scoring Criteria

### Base Scoring (0-2 points)

**0 points**: No Crowdin integration
- `crowdin.yml` not present
- No translation automation

**+1 point**: Basic Crowdin integration
- `crowdin.yml` exists
- Some configuration present
- May not follow TYPO3 standards

**+2 points**: TYPO3-compliant Crowdin integration
- `crowdin.yml` follows TYPO3 standard format
- `preserve_hierarchy: 1` present
- Wildcard source patterns (`*.xlf`)
- Proper translation pattern with variables
- Ignore directive present
- No unnecessary fields
- GitHub workflow (if present) only uploads sources
- No download job or cron schedule

### Excellence Validation

For full +2 points, ALL of the following must be true:

1. **Configuration Compliance**:
   - ✅ `preserve_hierarchy: 1`
   - ✅ Source: `/Resources/Private/Language/*.xlf`
   - ✅ Translation: `/%original_path%/%two_letters_code%.%original_file_name%`
   - ✅ Ignore directive present
   - ✅ No project_id_env or api_token_env in crowdin.yml
   - ✅ No languages_mapping or unnecessary fields

2. **Workflow Compliance** (if GitHub Actions used):
   - ✅ Single job for upload
   - ✅ No download job
   - ✅ No cron schedule
   - ✅ Triggers on push to main
   - ✅ Uses latest action versions

3. **Translation Structure**:
   - ✅ Source files in `Resources/Private/Language/` (no language prefix)
   - ✅ Translation files follow `{lang}.{filename}.xlf` pattern
   - ✅ XLIFF files have both `<source>` and `<target>` elements

## Automated Validation Command

```bash
#!/bin/bash
# Comprehensive TYPO3 Crowdin integration validation

score=0
max_score=2

echo "=== TYPO3 Crowdin Integration Validation ==="
echo

# Check crowdin.yml existence
if [[ ! -f crowdin.yml ]]; then
  echo "❌ crowdin.yml not found (0/2 points)"
  exit 0
fi
echo "✅ crowdin.yml found"

# Validate configuration
config_valid=true

if ! grep -q "preserve_hierarchy: 1" crowdin.yml; then
  echo "❌ Missing preserve_hierarchy: 1"
  config_valid=false
fi

if ! grep -q "/Resources/Private/Language/\*.xlf" crowdin.yml; then
  echo "❌ Missing wildcard source pattern (*.xlf)"
  config_valid=false
fi

if ! grep -q "%original_path%.*%two_letters_code%.*%original_file_name%" crowdin.yml; then
  echo "❌ Translation pattern not TYPO3-compliant"
  config_valid=false
fi

if ! grep -q "ignore:" crowdin.yml; then
  echo "❌ Missing ignore directive"
  config_valid=false
fi

if grep -qE "project_id_env|api_token_env|languages_mapping" crowdin.yml; then
  echo "⚠️  Non-standard fields detected"
  config_valid=false
fi

if [[ "$config_valid" == true ]]; then
  score=2
  echo "✅ Configuration fully TYPO3-compliant (+2 points)"
else
  score=1
  echo "⚠️  Configuration present but not fully compliant (+1 point)"
fi

# Check GitHub workflow (optional)
workflow_file=""
for f in .github/workflows/crowdin.yml .github/workflows/crowdin.yaml .github/workflows/crowdin-sync.yml; do
  [[ -f "$f" ]] && workflow_file="$f" && break
done

if [[ -n "$workflow_file" ]]; then
  echo
  echo "=== GitHub Workflow Validation ==="

  if grep -q "download.*translation\|schedule:" "$workflow_file"; then
    echo "⚠️  Workflow has download job or cron schedule (not TYPO3 standard)"
    score=1  # Downgrade to +1 point
  else
    echo "✅ Workflow follows TYPO3 standards (upload only)"
  fi
fi

echo
echo "=== Final Score: $score/$max_score points ==="
```

## Common Anti-Patterns

### Anti-Pattern 1: Standalone Crowdin Project Mindset
❌ Creating independent Crowdin project
❌ Using personal Crowdin account
❌ Configuring download workflows in GitHub Actions
✅ Contacting TYPO3 localization team for setup
✅ Using TYPO3's centralized Crowdin organization
✅ Letting Crowdin's native integration handle downloads

### Anti-Pattern 2: Over-Engineering Configuration
❌ 90-line `crowdin.yml` with every possible option
❌ Explicit language mapping for all supported languages
❌ Complex PR templates and commit messages in config
✅ Simple 6-line `crowdin.yml` following TYPO3 standard
✅ Letting Crowdin handle language detection automatically
✅ Using Crowdin's default PR behavior

### Anti-Pattern 3: Dual-Job Workflows
❌ Upload job + Download job + Cron schedule
❌ Manual PR creation in GitHub Actions
❌ Complex conditional logic for different event types
✅ Single upload job triggered on main branch push
✅ Crowdin's native integration creates PRs automatically
✅ Simple, maintainable workflow

## References

- **Official TYPO3 Documentation**: https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/ApiOverview/Localization/TranslationServer/Crowdin/ExtensionIntegration.html
- **Crowdin GitHub Action**: https://github.com/marketplace/actions/crowdin-action
- **TYPO3 Slack**: `#typo3-localization-team` channel
- **Example Extension**: Check `EXT:news` or other popular extensions for reference implementations

## Translation Quality Validation

### Detecting Untranslated Strings

**Problem**: Translation files may contain strings where `<source>` equals `<target>`, indicating untranslated content.

**Detection Script**:
```python
import re
from pathlib import Path

def find_untranslated(lang_files):
    """Find strings where source == target (untranslated)"""
    for filepath in lang_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract source/target pairs
        units = re.findall(
            r'<trans-unit id="([^"]+)"[^>]*>.*?<source>([^<]+)</source>\s*<target>([^<]+)</target>.*?</trans-unit>',
            content,
            re.DOTALL
        )
        
        untranslated = []
        for unit_id, source, target in units:
            if source.strip() == target.strip():
                untranslated.append((unit_id, source.strip()))
        
        if untranslated:
            print(f"{filepath.name}: {len(untranslated)} untranslated")
            for unit_id, text in untranslated[:3]:
                print(f"  - {text}")
```

**Validation Points**:
- Brand names (e.g., "Retina", "Ultra") may legitimately remain unchanged
- Technical terms may be international (e.g., "Standard")
- All other matches should be reviewed for proper translation

## Minimizing Crowdin PR Noise

### Problem: Excessive Formatting Changes

Crowdin PRs often contain many cosmetic changes that make review difficult:
- Whitespace differences
- Attribute reordering
- Added `state` attributes
- Line ending inconsistencies

### Solution: Preemptive Configuration

#### 1. .editorconfig

Add XLIFF/XML formatting rules:

```ini
[*.{xlf,xml}]
indent_style = tab
indent_size = 4
trim_trailing_whitespace = true
```

**Purpose**: Ensures consistent formatting between local files and Crowdin exports

#### 2. .gitattributes

Add line ending handling:

```
*.xlf text eol=lf linguist-language=XML
*.xml text eol=lf
```

**Purpose**: Enforces LF line endings for XLIFF files, prevents CRLF/LF mixing

#### 3. crowdin.yml Export Options

Add export configuration:

```yaml
preserve_hierarchy: 1
files:
  - source: /Resources/Private/Language/*.xlf
    translation: /%original_path%/%two_letters_code%.%original_file_name%
    ignore:
      - /**/%two_letters_code%.%original_file_name%
    # Minimize formatting changes
    export_options:
      export_quotes: none
      export_pattern: default
      export_approved_only: false
```

**Purpose**: Controls Crowdin's export formatting behavior

#### 4. Preemptive state="translated" Attributes

Add `state="translated"` to all target elements **before** Crowdin does:

```bash
# Add to all translated targets
find Resources/Private/Language -name "*.locallang_be.xlf" \
  -exec sed -i 's/<target>/<target state="translated">/g' {} \;
```

Or via Python:

```python
import re
from pathlib import Path

for filepath in Path('Resources/Private/Language').glob('*.locallang_be.xlf'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add state="translated" to targets without it
    new_content = re.sub(
        r'<target(?![^>]*state=)([^>]*)>',
        r'<target state="translated"\1>',
        content
    )
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"{filepath.name}: Added state attributes")
```

**Purpose**: Prevents Crowdin from adding `state="translated"` in its PRs

### Unavoidable Changes

Some formatting differences cannot be prevented:

- **XML attribute reordering**: Crowdin's XML parser may reorder attributes
  - Example: `target-language="de"` position may change
  - This is cosmetic and doesn't affect functionality

- **Comment preservation**: Crowdin may remove or reformat XML comments

**Recommendation**: Accept these cosmetic changes and focus PR reviews on actual translation content.

### Impact Assessment

**Before optimization**:
```diff
- <file source-language="en" target-language="de" datatype="plaintext">
+ <file source-language="en" datatype="plaintext" target-language="de">
  
- <target>Translated text</target>
+ <target state="translated">Translated text</target>

(Plus many whitespace and line ending changes)
```

**After optimization**:
```diff
(Minimal diff showing only actual translation changes or unavoidable attribute reordering)
```

## XLIFF Version Standards

### XLIFF 1.2 vs 1.0

**TYPO3 Recommendation**: Use XLIFF 1.2 for all translation files

**Benefits of XLIFF 1.2**:
- Better tooling support across translation platforms
- Enhanced validation capabilities with proper namespace
- Recommended by OASIS XLIFF Technical Committee
- Improved interoperability with CAT (Computer-Assisted Translation) tools
- Required for modern Crowdin features and validation

### Version Detection

Check current XLIFF version in translation files:

```bash
grep -h "xliff version" Resources/Private/Language/*.xlf | sort -u
```

**XLIFF 1.0 format** (deprecated):
```xml
<?xml version="1.0" encoding="utf-8" standalone="yes" ?>
<xliff version="1.0">
    <file source-language="en" datatype="plaintext" product-name="rte_ckeditor_image">
```

**XLIFF 1.2 format** (recommended):
```xml
<?xml version="1.0" encoding="utf-8" standalone="yes" ?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
    <file source-language="en" datatype="plaintext" product-name="rte_ckeditor_image">
```

### Key Differences

1. **Version attribute**: `version="1.0"` → `version="1.2"`
2. **Namespace declaration**: Must add `xmlns="urn:oasis:names:tc:xliff:document:1.2"`
3. **Validation**: XLIFF 1.2 has stricter schema validation
4. **Tooling**: Modern CAT tools prefer XLIFF 1.2

### Upgrade Script

Automated XLIFF 1.0 → 1.2 conversion:

```python
#!/usr/bin/env python3
import re
from pathlib import Path

def upgrade_xliff_to_1_2(filepath):
    """Upgrade XLIFF file from version 1.0 to 1.2"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already 1.2
    if 'version="1.2"' in content:
        return False

    # Upgrade version and add namespace
    new_content = content.replace(
        '<xliff version="1.0">',
        '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">'
    )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True

    return False

# Upgrade all XLIFF files
upgraded_count = 0
for filepath in Path('Resources/Private/Language').glob('*.xlf'):
    if upgrade_xliff_to_1_2(filepath):
        print(f"✅ Upgraded: {filepath.name}")
        upgraded_count += 1
    else:
        print(f"⏭️  Already XLIFF 1.2: {filepath.name}")

print(f"\nUpgraded {upgraded_count} files to XLIFF 1.2")
```

**Bash alternative** (simple sed replacement):

```bash
#!/bin/bash
# Upgrade all XLIFF files from 1.0 to 1.2

for file in Resources/Private/Language/*.xlf; do
    if grep -q 'version="1.0"' "$file"; then
        sed -i 's|<xliff version="1.0">|<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">|g' "$file"
        echo "✅ Upgraded: $file"
    else
        echo "⏭️  Already XLIFF 1.2: $file"
    fi
done
```

### Validation

Verify XLIFF 1.2 compliance after upgrade:

```bash
# Check all files have version 1.2
if grep -q 'version="1.0"' Resources/Private/Language/*.xlf 2>/dev/null; then
    echo "❌ Some files still use XLIFF 1.0"
    grep -l 'version="1.0"' Resources/Private/Language/*.xlf
    exit 1
else
    echo "✅ All files use XLIFF 1.2"
fi

# Check all files have namespace
if grep -L 'xmlns="urn:oasis:names:tc:xliff:document:1.2"' Resources/Private/Language/*.xlf 2>/dev/null | grep -q .; then
    echo "❌ Some files missing XLIFF 1.2 namespace"
    grep -L 'xmlns="urn:oasis:names:tc:xliff:document:1.2"' Resources/Private/Language/*.xlf
    exit 1
else
    echo "✅ All files have proper XLIFF 1.2 namespace"
fi
```

### Testing After Upgrade

1. **TYPO3 Backend**: Verify translations still load correctly
2. **Crowdin Upload**: Test that Crowdin accepts XLIFF 1.2 files
3. **Translation Export**: Confirm Crowdin exports maintain XLIFF 1.2 format
4. **XML Validation**: Use xmllint or online validators to check schema compliance

```bash
# Validate XML syntax
for file in Resources/Private/Language/*.xlf; do
    xmllint --noout "$file" 2>&1 && echo "✅ $file" || echo "❌ $file"
done
```

### Best Practices

1. **All files same version**: Upgrade all XLIFF files together, don't mix versions
2. **Test before commit**: Verify in TYPO3 backend before committing
3. **Document in PR**: Mention XLIFF version upgrade in PR description
4. **Crowdin compatibility**: Confirm Crowdin continues to work after upgrade

## Validation Scoring Impact

### Translation Quality (+2 points)

- **Basic state attributes** (+1): All translated targets have `state="translated"`
- **Complete translations** (+1): No untranslated strings (source != target except for brand names)

### Configuration Quality (+1 point)

- **Formatting rules** (+0.5): .editorconfig and .gitattributes present
- **Export options** (+0.5): crowdin.yml includes export_options configuration

### XLIFF Version (+1 point)

- **XLIFF 1.2 compliance** (+1): All translation files use XLIFF 1.2 with proper namespace declaration

**Total possible improvement**: +4 points to conformance score
