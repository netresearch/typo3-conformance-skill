---
name: typo3-conformance
description: "Agent Skill: Evaluate TYPO3 extensions for conformance to v12/v13/v14 standards. Use when assessing quality, generating reports, or planning modernization. By Netresearch."
file_triggers:
  - "ext_emconf.php"
  - "ext_localconf.php"
  - "**/Configuration/TCA/**/*"
  - "**/*.typoscript"
---

# TYPO3 Extension Conformance Checker

Evaluate TYPO3 extensions for standards compliance, architecture patterns, and best practices.

## Skill Delegation

**IMPORTANT:** When performing conformance checks, you MUST invoke these skills for comprehensive validation:

| Skill | When to Invoke | What It Validates |
|-------|----------------|-------------------|
| **typo3-docs** | Documentation/ folder exists | RST syntax, guides.xml, rendering, TYPO3 directives |
| **typo3-tests** | Tests/ folder exists | PHPUnit config, test patterns, coverage requirements |

### How to Delegate

1. **For Documentation:** After running `check-documentation.sh`, invoke the typo3-docs skill:
   ```
   Use typo3-docs skill to validate Documentation/ folder
   ```
   This provides comprehensive RST validation beyond basic file structure checks.

2. **For Testing:** After running `check-testing.sh`, invoke the typo3-tests skill:
   ```
   Use typo3-tests skill to validate Tests/ folder
   ```
   This provides detailed test pattern and coverage analysis.

The bash scripts only check file structure. The delegated skills provide deep content validation.

## Evaluation Workflow

1. **Initial Assessment** - Extension key, TYPO3 version, type
2. **File Structure** - composer.json, ext_emconf.php, required directories
3. **Coding Standards** - strict_types, types, PSR-12
4. **Prohibited Patterns** - No `$GLOBALS`, no `GeneralUtility::makeInstance()` for services
5. **PHP Architecture** - Constructor DI, Services.yaml, PSR-14 events, TcaSchemaFactory
6. **Backend Module v13** - ES6 modules, Modal API, CSRF
7. **Testing** - PHPUnit, Playwright E2E, coverage >70%
8. **Best Practices** - DDEV, runTests.sh, quality tools, CI/CD
9. **TER Publishing** - Workflow validation, upload comment format, CI TER compatibility check

## Scoring

**Base (0-100)**: Architecture 20 + Guidelines 20 + PHP 20 + Testing 20 + Practices 20

**Excellence (0-22 bonus)**: Optional features for exceptional quality

## Commands

```bash
scripts/check-conformance.sh /path/to/extension
```

## References

| File | Purpose |
|------|---------|
| `extension-architecture.md` | Directory structure |
| `coding-guidelines.md` | PSR-12, naming |
| `backend-module-v13.md` | Backend modernization |
| `php-architecture.md` | DI, events, services, PSR-17/18 |
| `testing-standards.md` | PHPUnit, Playwright |
| `excellence-indicators.md` | Bonus scoring |
| `multi-tier-configuration.md` | Provider → Model → Config architecture |
| `backend-wizard-patterns.md` | Setup wizard DTOs, AJAX, ES6 |
| `ter-publishing.md` | TER workflow, upload comments, CI checks |

---

> **Contributing:** https://github.com/netresearch/typo3-conformance-skill
