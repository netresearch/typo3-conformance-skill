# Architecture

## Overview

The typo3-conformance-skill is an AI agent skill that evaluates TYPO3 extensions against official coding standards, architecture patterns, and best practices. It follows the [Agent Skills](https://agentskills.io) open standard and acts as an orchestrator that delegates to specialized skills for deep domain analysis.

## Components

### Skill Definition (`skills/typo3-conformance/`)

- **SKILL.md**: Entry point loaded by AI agents. Contains trigger patterns, scoring rubric, and orchestration instructions.
- **checkpoints.yaml**: Conformance checkpoints organized by category with scoring weights.
- **references/**: 22 reference guides covering coding guidelines, directory structure, TCA, hooks/events, testing, documentation, and more.
- **scripts/**: Modular check scripts, each focused on one conformance domain.

### Check Scripts (`skills/typo3-conformance/scripts/`)

| Script | Domain |
|--------|--------|
| `check-conformance.sh` | Full conformance orchestrator |
| `check-file-structure.sh` | Required/recommended file layout |
| `check-architecture.sh` | DI, TCA, TYPO3 API usage |
| `check-coding-standards.sh` | PSR-12, strict types, naming |
| `check-testing.sh` | PHPUnit config, test infrastructure |
| `check-documentation.sh` | RST docs, inline docs |
| `check-phpstan-baseline.sh` | PHPStan baseline analysis |
| `generate-report.sh` | Structured conformance report |

### Commands (`commands/`)

- **check.md**: Defines the `/check` slash command for running a conformance assessment interactively.

### Output Styles (`outputStyles/`)

- Report templates for formatting conformance assessment results.

## Orchestration Pattern

The skill acts as an orchestrator, delegating to specialized skills when available:

```
typo3-conformance-skill (orchestrator)
  ├── typo3-testing-skill    -- deep testing analysis (20 points)
  ├── typo3-docs-skill       -- documentation validation (bonus)
  └── fallback               -- surface-level checks if skills unavailable
```

## Scoring

Extensions are scored across categories (file structure, coding standards, architecture, testing, etc.) with weighted points. The report provides a total score and prioritized action items.

## Integration

- **composer.json**: Enables installation via Composer with `netresearch/composer-agent-skill-plugin`
- **CI/CD**: GitHub Actions workflows handle linting and release automation
