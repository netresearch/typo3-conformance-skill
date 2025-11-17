# Changelog

All notable changes to the TYPO3 Conformance Checker skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2025-01-17

### Added
- Comprehensive ext_emconf.php validation reference (references/ext-emconf-validation.md)
  - Critical TER upload failure detection (declare(strict_types=1))
  - Complete state values and category validation
  - Version constraint format validation
  - Synchronization with composer.json constraints
- Complete ext_* files validation reference (references/ext-files-validation.md)
  - ext_localconf.php structure and v13 deprecations
  - ext_tables.php phasing out guidance
  - ext_tables.sql v13.4 CHAR/BINARY handling
  - ext_tables_static+adt.sql validation (NEW - was completely missing)
  - ext_conf_template.txt comprehensive syntax and field types
- TYPO3 v13 deprecations tracking (references/v13-deprecations.md)
  - ext_typoscript_constants.typoscript deprecation (v13.1)
  - ext_typoscript_setup.typoscript deprecation (v13.1)
  - addUserTSConfig() removal in v14.0
  - Modern alternatives: Site Sets, Configuration/user.tsconfig, Configuration/page.tsconfig
  - Backend module migration to Configuration/Backend/Modules.php

### Changed
- Skill description now explicitly includes ext_emconf.php validation
- Skill description now explicitly includes comprehensive ext_* files validation
- Skill description now explicitly includes TYPO3 v13 deprecation detection

## [1.4.0] - 2025-01-17

### Added
- Comprehensive composer.json validation reference (references/composer-validation.md)
  - Mandatory fields validation (name, type, description, license, require, autoload)
  - extra.typo3/cms.extension-key requirement detection
  - Version constraint validation with upper bounds enforcement
  - Deprecated properties detection (typo3-ter vendor, self.version)
  - Synchronization validation with ext_emconf.php
  - TYPO3 v12-v13 version constraint patterns

### Changed
- Skill description now explicitly includes composer.json validation

## [1.3.0] - 2025-01-17

### Changed
- Refactored entire SKILL.md to imperative form for consistency
- Converted all workflow descriptions from indicative to imperative voice
- Enhanced clarity and directness throughout documentation
- Improved actionability of all instructions and guidelines

## [1.2.0] - 2024-12-XX

### Added
- Comprehensive TYPO3 Crowdin integration validation
- Translation quality validation and PR noise minimization
- XLIFF 1.2 standards and upgrade guidance
- Translator notes and CI validation guidance for XLIFF files
- Page size guidelines for TYPO3 documentation structure
- Version control best practices documentation (main over master)

### Changed
- Updated Crowdin configuration filename from crowdin.yaml to crowdin.yml

## [1.1.0] - 2024-12-XX

### Added
- Skill ecosystem integration with typo3-tests and typo3-docs specialized skills
- Delegation strategy for deep domain analysis
- Excellence indicators and TYPO3 13 patterns
- Comprehensive build scripts validation
- Development environment detection and validation
- Directory structure validation
- Tea extension best practices (Phases 1-3)
- PHPStan baseline hygiene validation
- PHPStan Level 10 best practices (corrected from Level 9)
- Inclusive language guidelines
- Documentation gap guidance and typo3-docs skill recommendation
- Hooks and events reference integration

### Changed
- Fixed skill name to use hyphen-case (typo3-conformance)

## [1.0.0] - 2024-11-XX

### Added
- Initial TYPO3 conformance checker skill
- Support for TYPO3 12.4 LTS and 13.x
- PHP 8.1 - 8.4 compatibility validation
- PSR-12 and TYPO3 CGL coding standards checks
- Extension architecture validation
- Dependency injection pattern validation
- Services configuration validation
- Testing coverage analysis
- Extbase pattern validation
- Best practices alignment checks
- Dual scoring system (0-100 base + 0-20 excellence)
- Comprehensive version requirements reference
- PHPStan and Rector detection in Build/ directory
- PHP 8.4 support
- Context-appropriate messaging for non-git projects
- Git-tracked files analysis
- Prevention of false positives for local developer tool configs

---

## Version History Summary

- **1.5.0**: Complete TYPO3 v13 file validation and deprecation tracking
- **1.4.0**: Comprehensive composer.json validation
- **1.3.0**: Imperative form refactoring
- **1.2.0**: Crowdin integration and documentation standards
- **1.1.0**: Skill ecosystem integration and excellence indicators
- **1.0.0**: Initial conformance checker implementation
