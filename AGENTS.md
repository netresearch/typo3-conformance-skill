<!-- SPDX-License-Identifier: CC-BY-SA-4.0 -->
<!-- SPDX-FileCopyrightText: Netresearch DTT GmbH -->

# TYPO3 Conformance Skill

Comprehensive TYPO3 extension conformance checker against official coding standards, architecture patterns, and best practices.

## Repo Structure

```
typo3-conformance-skill/
├── skills/typo3-conformance/    # Skill definition
│   ├── SKILL.md                 # Skill metadata and trigger patterns
│   ├── checkpoints.yaml         # Conformance checkpoints
│   ├── scripts/                 # Check scripts (architecture, coding, file structure, etc.)
│   ├── references/              # 24 reference guides (coding, architecture, TCA, etc.)
│   └── assets/                  # Static assets
├── commands/                    # Slash commands
│   └── check.md                 # /check command definition
├── evals/                       # Skill evaluation tests
├── outputStyles/                # Report output formatting
├── Build/                       # Build utilities
├── .github/workflows/           # CI (lint, tests, security, evals, harness, release, ...)
├── tests/                       # Behaviour tests for the shipped scripts
├── composer.json                # PHP package definition
└── docs/                        # Architecture and planning docs
    ├── ARCHITECTURE.md          # Architecture overview
    └── SECURITY-ASSURANCE.md    # Security assurance case
```

## Commands

No Makefile or build scripts defined. Key operations:

- Install PHP dependencies: run `composer` with `install`
- Run full conformance check: `bash skills/typo3-conformance/scripts/check-conformance.sh`
- Check file structure: `bash skills/typo3-conformance/scripts/check-file-structure.sh`
- Check architecture: `bash skills/typo3-conformance/scripts/check-architecture.sh`
- Check coding standards: `bash skills/typo3-conformance/scripts/check-coding-standards.sh`
- Check testing setup: `bash skills/typo3-conformance/scripts/check-testing.sh`
- Check documentation: `bash skills/typo3-conformance/scripts/check-documentation.sh`
- Check PHPStan baseline: `bash skills/typo3-conformance/scripts/check-phpstan-baseline.sh`
- Generate report: `bash skills/typo3-conformance/scripts/generate-report.sh <extension-dir> <report-file> [scores...]` (called by check-conformance.sh)
- Run the script tests: `python3 tests/test_scripts.py`
- Verify harness maturity: `bash scripts/verify-harness.sh --format=text --status`

## Rules

- Extensions must have `ext_emconf.php` and `composer.json`
- All PHP files must declare `strict_types=1`
- Follow PSR-12 coding standards
- Use dependency injection via `Services.yaml` (no direct `$GLOBALS` access)
- TCA in `Configuration/TCA/`, TypoScript in `Configuration/TypoScript/`
- FlexForms in `Configuration/FlexForms/`
- Fluid templates in `Resources/Private/Templates/`
- Delegates testing analysis to typo3-testing-skill and docs to typo3-docs-skill
- **Gold standard is TYPO3 v14.3 LTS** (released 2026-04-21): grade extensions against v14, default version examples to v14.3 (use `^14.3` in composer, `14.3.0-14.3.99` in `ext_emconf.php`). v12/v13 stay in the matrix as "also supported". PHP floor 8.2, ceiling 8.5; Composer ≥ 2.1. Umbrella ticket for removed functionality is [#105377](https://forge.typo3.org/issues/105377)

## References

- [SKILL.md](skills/typo3-conformance/SKILL.md) -- skill definition and trigger patterns
- [checkpoints.yaml](skills/typo3-conformance/checkpoints.yaml) -- conformance checkpoints
- [references/](skills/typo3-conformance/references/) -- 24 reference guides
- [commands/check.md](commands/check.md) -- /check command definition
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) -- architecture overview
- [docs/SECURITY-ASSURANCE.md](docs/SECURITY-ASSURANCE.md) -- security assurance case
