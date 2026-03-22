# TYPO3 Conformance Skill

Comprehensive TYPO3 extension conformance checker against official coding standards, architecture patterns, and best practices.

## Repo Structure

```
typo3-conformance-skill/
├── skills/typo3-conformance/    # Skill definition
│   ├── SKILL.md                 # Skill metadata and trigger patterns
│   ├── checkpoints.yaml         # Conformance checkpoints
│   ├── scripts/                 # Check scripts (architecture, coding, file structure, etc.)
│   ├── references/              # 22 reference guides (coding, architecture, TCA, etc.)
│   └── assets/                  # Static assets
├── commands/                    # Slash commands
│   └── check.md                 # /check command definition
├── evals/                       # Skill evaluation tests
├── outputStyles/                # Report output formatting
├── Build/                       # Build utilities
├── .github/workflows/           # CI (lint.yml, release.yml, auto-merge-deps.yml)
├── composer.json                # PHP package definition
└── docs/                        # Architecture and planning docs
    └── ARCHITECTURE.md          # Architecture overview
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
- Generate report: `bash skills/typo3-conformance/scripts/generate-report.sh`
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

## References

- [SKILL.md](skills/typo3-conformance/SKILL.md) -- skill definition and trigger patterns
- [checkpoints.yaml](skills/typo3-conformance/checkpoints.yaml) -- conformance checkpoints
- [references/](skills/typo3-conformance/references/) -- 22 reference guides
- [commands/check.md](commands/check.md) -- /check command definition
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) -- architecture overview
