---
name: typo3-conformance
description: "Use when assessing TYPO3 extension quality, generating conformance reports, or planning modernization to v12/v13/v14 standards."
file_triggers:
  - "ext_emconf.php"
  - "ext_localconf.php"
  - "**/Configuration/TCA/**/*"
  - "**/*.typoscript"
---

# TYPO3 Extension Conformance Checker

Evaluate TYPO3 extensions for standards compliance, architecture patterns, and best practices.

## When to Use

- Assessing extension quality before production deployment
- Generating conformance reports for code review
- Planning modernization to TYPO3 v12/v13/v14 standards
- Validating TER publishing readiness

## Skill Delegation

- **Testing details**: Delegate to `typo3-testing` skill
- **Documentation validation**: Delegate to `typo3-docs` skill
- **OpenSSF Scorecard**: Delegate to `enterprise-readiness` skill

## Evaluation Workflow

### Step 0: Understand Extension Context (always first)

Before checking files, understand: purpose, target TYPO3/PHP version, extension type (plugin, module, site package, library), criticality (production vs experimental), and codebase scope.

### Steps 1-9: Conformance Checks

1. **Initial Assessment** -- Extension key, target TYPO3 version, extension type
2. **File Structure** -- composer.json, ext_emconf.php, required directories
3. **Coding Standards** -- strict_types, type declarations, PSR-12
4. **Prohibited Patterns** -- No `$GLOBALS` access, no `GeneralUtility::makeInstance()` for services
5. **PHP Architecture** -- Constructor DI, Services.yaml, PSR-14 events
6. **Backend Modules** -- ES6 modules, Modal API, CSRF protection (v13+)
7. **Testing** -- PHPUnit setup, Playwright E2E, coverage >70%
8. **Best Practices** -- DDEV setup, runTests.sh, quality tools, CI/CD
9. **TER Publishing** -- Workflow, upload comment format, CI compatibility

### Step 10: Verification Loop

After fixes, re-run conformance checks. Document score improvement (e.g., "58 -> 82"). Ensure no regressions.

## Scoring System

**Base Score (0-100):** Architecture (20) + Guidelines (20) + PHP Patterns (20) + Testing (20) + Best Practices (20). Excellence bonus up to 22 additional points.

| Score Range | Interpretation | Action |
|------------|----------------|--------|
| 90-100+ | Excellent | Ready for production and TER |
| 80-89 | Good | Minor improvements recommended |
| 70-79 | Acceptable | Address before major releases |
| 50-69 | Needs Work | Significant improvements required |
| Below 50 | Critical | Block deployment until resolved |

**Critical issues** (security, data loss, core incompatibility) block deployment regardless of score.

## Running Checks

```bash
# Full conformance check
scripts/check-conformance.sh /path/to/extension

# Individual checks
scripts/check-file-structure.sh /path/to/extension
scripts/check-coding-standards.sh /path/to/extension
scripts/check-architecture.sh /path/to/extension
scripts/check-testing.sh /path/to/extension
scripts/check-phpstan-baseline.sh /path/to/extension
scripts/generate-report.sh /path/to/extension
```

## References

Detailed guidance for each evaluation area:

- `references/extension-architecture.md` -- Directory structure, required files
- `references/coding-guidelines.md` -- PSR-12, naming conventions, TYPO3 style
- `references/php-architecture.md` -- DI, services, events, Extbase, middleware
- `references/testing-standards.md` -- PHPUnit and Playwright requirements
- `references/composer-validation.md` -- composer.json validation rules
- `references/ext-emconf-validation.md` -- TER requirements, field specs
- `references/version-requirements.md` -- TYPO3/PHP compatibility matrix
- `references/dual-version-compatibility.md` -- v12+v13 patterns
- `references/v13-deprecations.md` -- Deprecated APIs and migration paths
- `references/backend-module-v13.md` -- ES6, Modal API, accessibility
- `references/ter-publishing.md` -- TER publication requirements
- `references/report-template.md` -- Standard report structure
- `references/excellence-indicators.md` -- Bonus scoring criteria
- `references/best-practices.md` -- Tea extension organizational patterns

### Asset Templates

Quality tool configs in `assets/Build/`: PHPStan (`phpstan/`), PHP-CS-Fixer (`php-cs-fixer/`), Rector (`rector/`), ESLint (`eslint/`), Stylelint (`stylelint/`), TypoScript lint (`typoscript-lint/`).
