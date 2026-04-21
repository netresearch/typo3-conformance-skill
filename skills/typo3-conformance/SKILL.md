---
name: typo3-conformance
description: "Use when assessing TYPO3 extension quality, conformance checking, standards compliance, modernization to v12/v13/v14 (v14.3 LTS is the default/gold standard), TER readiness, or best practices review. Also triggers on: extension audit, quality score, full assessment, fix all findings, conformance audit, Fluid 5 strict ViewHelpers, ext_tables.php removal, Extbase attributes (Authorize/RateLimit), HashService removal, Bootstrap 5 migration, CSP compliance, ViewHelper security, XLIFF hygiene, PHP 8.4/8.5 compat."
metadata:
  version: "2.11.0"
  repository: https://github.com/netresearch/typo3-conformance-skill
  author: Netresearch DTT GmbH
---

# TYPO3 Extension Conformance Checker

Evaluate TYPO3 extensions against TYPO3 coding standards, architecture patterns, and best practices.

## When to Use

- Assessing extension quality or TER readiness
- Generating scored conformance reports
- Planning modernization to v12/v13/v14 (**v14.3 LTS is the default/gold standard** as of 2026-04-21)

## Delegation

Testing -> `typo3-testing` | Docs -> `typo3-docs` | OpenSSF -> `enterprise-readiness`

## Workflow

### Step 0: Context

Read ext_emconf.php + composer.json to determine TYPO3/PHP version, extension type, scope.

### Steps 1-11: Checks

1. **Metadata** -- Extension key, TYPO3 version, type
2. **Structure** -- composer.json, ext_emconf.php, Classes/, Configuration/, Resources/
3. **Coding** -- strict_types, PSR-12, PHP 8.4 explicit nullable, PHP 8.5 float-to-int
4. **Prohibited** -- No `$GLOBALS`, no `GeneralUtility::makeInstance()` for services
5. **Architecture** -- Constructor DI, Services.yaml, PSR-14 events
6. **Backend** -- ES6 modules, Modal API, CSRF, CSP (v13+)
7. **Testing** -- PHPUnit, Playwright E2E, coverage >70%
8. **Practices** -- DDEV, runTests.sh, CI/CD, quality tools
9. **TER** -- Publish workflow, upload comment format
10. **Audit** -- PHPStan baseline, TCA searchFields/default_sortby, XLIFF completeness, cache has()+get() anti-pattern, Extbase query property names, multi-version adapters
11. **v14 readiness** -- `ext_tables.php` present? (deprecated for v15); `ext_emconf.php` still primary metadata? (prefer `composer.json`); Fluid VHs strict-typed?; `HashService`/`GeneralUtility::hmac()` callers?; magic Extbase repo finders?; XLF 2-space indentation?

### Step 12: Verify

Re-run after fixes. Document score delta (e.g., "58 -> 82").

## Quick Grep Recipes

```bash
# Missing strict_types
grep -rL 'strict_types' Classes/ --include='*.php'
# Prohibited $GLOBALS
grep -rn '\$GLOBALS' Classes/ --include='*.php'
# makeInstance for services
grep -rn 'GeneralUtility::makeInstance' Classes/ --include='*.php'
# PHP 8.4 implicit nullable (deprecated)
grep -rPn '\(\s*[A-Za-z\\]+\s+\$\w+\s*=\s*null' Classes/ --include='*.php' | grep -v '?'
# Cache has()+get() anti-pattern
grep -rn '->has(' Classes/ --include='*.php'
# ext_emconf must NOT have strict_types
grep -l 'strict_types' ext_emconf.php
# PHP 8.5 implicit float-to-int (deprecated)
grep -rn '(int)\s*\$' Classes/ --include='*.php'
# Bootstrap 4 data attributes in Fluid
grep -rn 'data-toggle\|data-dismiss\|data-ride' Resources/ --include='*.html'
# v14: HashService removed -> should not be used
grep -rn 'HashService\|GeneralUtility::hmac(' Classes/ --include='*.php'
# v14: magic Extbase repo finders removed
grep -rn '->findBy[A-Z]\|->findOneBy[A-Z]\|->countBy[A-Z]' Classes/ --include='*.php'
# v14: ext_tables.php deprecated (remove before v15)
[ -f ext_tables.php ] && echo "WARN: ext_tables.php present - deprecated in v14.3 (#109438)"
# v14: ext_emconf.php deprecated (prefer composer.json metadata)
[ -f ext_emconf.php ] && ! grep -q '"name"' composer.json && echo "WARN: ext_emconf.php still primary - migrate metadata to composer.json (#108345)"
```

## Scoring

**Base (0-100):** Architecture(20) + Guidelines(20) + PHP(20) + Testing(20) + Practices(20). Excellence bonus up to 22. Critical issues block regardless.

| Range | Level | Action |
|-------|-------|--------|
| 90+ | Excellent | Production/TER ready |
| 80-89 | Good | Minor fixes |
| 70-79 | Acceptable | Fix before release |
| 50-69 | Needs Work | Significant effort |
| <50 | Critical | Block deployment |

## References

- `references/extension-architecture.md` -- Structure, required files
- `references/coding-guidelines.md` -- PSR-12, naming, PHPStan
- `references/php-architecture.md` -- DI, events, middleware
- `references/testing-standards.md` -- PHPUnit/Playwright
- `references/composer-validation.md` -- composer.json rules
- `references/ext-emconf-validation.md` -- TER fields
- `references/version-requirements.md` -- TYPO3/PHP compat
- `references/dual-version-compatibility.md` -- v12+v13
- `references/v13-v14-dual-compatibility.md` -- v13+v14 (new)
- `references/multi-version-dependency-compatibility.md` -- Adapter pattern
- `references/v13-deprecations.md` -- v13 migration paths (removals mostly in v14.0)
- `references/v14-deprecations.md` -- v14 removals (in 14.0) & deprecations (for v15) authoritative list
- `references/backend-module-v13.md` -- ES6, Modal, a11y (v13-era; v14 additions noted inline)
- `references/ter-publishing.md` -- TER workflow
- `references/report-template.md` -- Report format
- `references/excellence-indicators.md` -- Bonus scoring
- `references/best-practices.md` -- Organizational patterns
- `references/localization-coverage.md` -- XLIFF, raw HTML vs Fluid

Asset templates in `assets/Build/`: PHPStan, PHP-CS-Fixer, Rector, ESLint, Stylelint, TypoScript lint.
