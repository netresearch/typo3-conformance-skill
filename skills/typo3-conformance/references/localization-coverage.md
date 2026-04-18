# Localization Coverage & XLIFF Hygiene

Checks and patterns for ensuring TYPO3 extension localization is complete, consistent, and not silently broken across languages.

## The Problem

Extensions ship with `Resources/Private/Language/locallang.xlf` (the English source) and per-language files `<lang>.locallang.xlf`. Over time:

- New keys are added to English but not to translations → missing strings show the key ID in the UI
- Translations become orphaned when English keys are removed but localized files keep them
- Some languages have 100% coverage, others drift to 30% — often unnoticed until a user reports broken UI
- Empty `<target>` elements ship as "translated" but render as blank

None of this is caught by PHPUnit, Rector, or PHPStan. It shows up in production.

## Required Layout

```
Resources/Private/Language/
├── locallang.xlf              # English source
├── de.locallang.xlf           # German
├── fr.locallang.xlf           # French
├── <lang>.locallang.xlf       # One per supported language
└── ...
```

Language codes use ISO 639-1 two-letter codes. For region-specific variants use `en-us`, `pt-br`, `zh-cn` (TYPO3 convention).

## Coverage Check Script

Drop-in script that reports coverage per language and fails CI if any language is below threshold:

```bash
#!/usr/bin/env bash
# scripts/check-localization-coverage.sh
set -euo pipefail

LANG_DIR="Resources/Private/Language"
MIN_COVERAGE="${MIN_COVERAGE:-80}"  # override via env
BASELINE="$LANG_DIR/locallang.xlf"

if [[ ! -f "$BASELINE" ]]; then
  echo "No baseline $BASELINE — skipping coverage check"
  exit 0
fi

SOURCE_KEYS=$(xmlstarlet sel -N x="urn:oasis:names:tc:xliff:document:1.2" \
  -t -v 'count(//x:trans-unit)' "$BASELINE")

echo "Baseline keys: $SOURCE_KEYS"

FAIL=0
for f in "$LANG_DIR"/*.locallang.xlf; do
  [[ "$f" == "$BASELINE" ]] && continue
  LANG=$(basename "$f" | cut -d. -f1)

  TRANSLATED=$(xmlstarlet sel -N x="urn:oasis:names:tc:xliff:document:1.2" \
    -t -v 'count(//x:trans-unit[x:target and x:target/text()])' "$f")
  EMPTY=$(xmlstarlet sel -N x="urn:oasis:names:tc:xliff:document:1.2" \
    -t -v 'count(//x:trans-unit[x:target and not(x:target/text())])' "$f")
  ORPHANED=$((TRANSLATED + EMPTY - SOURCE_KEYS))

  PCT=$((TRANSLATED * 100 / SOURCE_KEYS))
  PRINTF "%-6s %4d/%4d (%d%%) translated, %d empty, %d orphaned\n" \
    "$LANG" "$TRANSLATED" "$SOURCE_KEYS" "$PCT" "$EMPTY" "$ORPHANED"

  if (( PCT < MIN_COVERAGE )); then
    echo "  FAIL: $LANG below $MIN_COVERAGE% threshold" >&2
    FAIL=1
  fi
done

exit $FAIL
```

Wire into CI as a required status check. Adjust `MIN_COVERAGE` per extension (70% minimum, 90% for user-facing extensions).

## Common XLIFF Violations

### Empty targets shipped as translations

```xml
<!-- WRONG — ships as blank in the UI -->
<trans-unit id="welcome">
  <source>Welcome</source>
  <target></target>
</trans-unit>

<!-- RIGHT — either translate or omit the trans-unit so TYPO3 falls back to source -->
<trans-unit id="welcome">
  <source>Welcome</source>
  <target>Bienvenue</target>
</trans-unit>
```

### Orphaned keys

A trans-unit in `de.locallang.xlf` whose `id` no longer exists in `locallang.xlf`. TYPO3 silently ignores them, but they bloat the file and create confusion.

Detect: diff trans-unit IDs between source and localized file; flag localized-only IDs.

### Missing translations that shouldn't fall back

For UI labels, missing = fallback to English = acceptable. For regulatory/legal text, missing = broken. Mark critical keys:

```xml
<trans-unit id="privacy_notice" resname="critical">
  <source>Your data is processed...</source>
  <target>...</target>
</trans-unit>
```

And fail CI if any `resname="critical"` trans-unit has an empty target.

## Raw HTML vs Fluid/TYPO3 Form Elements

TYPO3 backend modules and frontend forms should use Fluid ViewHelpers and TYPO3 form elements — not raw `<input>`, `<form>`, `<button>` markup. Reasons:

- CSRF tokens are automatically injected by `<f:form>` / FormEngine; raw forms have none.
- `<f:translate>` + XLIFF integrates with the localization pipeline above; raw `<label>Login</label>` is invisible to Crowdin.
- Accessibility attributes (ARIA, labelledby, describedby) are handled consistently by ViewHelpers; raw markup varies per author.
- Backend styling (t3js-\*, typo3-backend-module-\* classes) is applied by FormEngine; raw forms look foreign.

### Detection pattern

Grep pattern for backend/frontend templates that should be upgraded:

```bash
# Raw <input> / <form> / <button> in Fluid templates — should use ViewHelpers
rg -t html --glob 'Resources/Private/**/*.html' \
  '^\s*<(form|input|button|textarea|select)(\s|>)' \
  --line-number
```

Allowable exceptions:

- `<input type="hidden">` for routing params inside an `<f:form>`
- `<button type="button">` for pure JS interactions where no form submission happens
- Raw elements inside a `<f:format.raw>` wrapping trusted HTML

Everything else should be a ViewHelper or FormEngine field.

### Replacement table

| Raw | Fluid / FormEngine equivalent |
|-----|-------------------------------|
| `<form method="post">` | `<f:form action="..." method="post">` |
| `<input type="text" name="x">` | `<f:form.textfield name="x" />` |
| `<input type="submit" value="Save">` | `<f:form.submit value="{f:translate(key: 'save')}" />` |
| `<button>Save</button>` | `<f:form.submit value="{f:translate(key: 'save')}" />` |
| `<a href="?id=1">Edit</a>` | `<f:link.action action="edit" arguments="{id: 1}">...</f:link.action>` |
| Hard-coded label text | `<f:translate key="..." />` |

### Checkpoint

Add to the skill's `checkpoints.yaml` as a `regex` mechanical check scoped to `Resources/Private/**/*.html`, or as an LLM review with the rubric above.

## XLIFF Encoding and Structure

- Always UTF-8, no BOM
- Namespace: `xmlns="urn:oasis:names:tc:xliff:document:1.2"` (v1.2 for TYPO3 core compatibility; v2.x is not yet supported)
- `<file source-language="en" target-language="de">` — must match the filename
- One `<file>` element per XLIFF file (not multiple)
- `<trans-unit id="...">` must match the key used in `LLL:EXT:...` references

### Lint

```bash
xmllint --noout Resources/Private/Language/*.xlf
```

Non-well-formed XML breaks TYPO3 silently (falls back to source language). Make this part of CI.
