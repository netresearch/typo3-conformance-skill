---
description: "Run TYPO3 conformance check on current extension"
---

# TYPO3 Conformance Check

Run a conformance assessment on the current TYPO3 extension.

## Steps

1. **Detect extension metadata**
   - Read `ext_emconf.php` for extension key and version
   - Read `composer.json` for PHP/TYPO3 version constraints
   - Determine target TYPO3 version (v12, v13, v14)

2. **File Structure Check**
   ```
   Required:
   - ext_emconf.php
   - composer.json
   - Classes/
   - Configuration/
   - Resources/

   Optional but recommended:
   - Tests/
   - Documentation/
   - .github/workflows/
   ```

3. **Code Quality Checks** (use grep recipes for speed)
   - PSR-12 compliance (check for php-cs-fixer config)
   - Strict types in all PHP files: `grep -rL 'strict_types' Classes/ --include='*.php'`
   - ext_emconf.php must NOT have strict_types: `grep -l 'strict_types' ext_emconf.php`
   - No direct $GLOBALS: `grep -rn '\$GLOBALS' Classes/ --include='*.php'`
   - No makeInstance for services: `grep -rn 'GeneralUtility::makeInstance' Classes/ --include='*.php'`
   - PHP 8.4 implicit nullable: `grep -rPn '\(\s*[A-Za-z\\]+\s+\$\w+\s*=\s*null' Classes/ --include='*.php' | grep -v '?'`
   - PHPStan baseline size (should trend toward zero)
   - No deprecated API usage

4. **TYPO3 Best Practices**
   - FlexForms in Configuration/FlexForms/
   - TypoScript in Configuration/TypoScript/
   - TCA in Configuration/TCA/ with searchFields and default_sortby
   - Fluid templates in Resources/Private/Templates/
   - DI interface aliases for all injected interfaces in Services.yaml
   - XLIFF key completeness (all LLL: references have matching trans-units)
   - No cache has()+get() anti-pattern: `grep -rn '->has(' Classes/ --include='*.php'`
   - Bootstrap 5 migration: `grep -rn 'data-toggle\|data-dismiss\|data-ride' Resources/ --include='*.html'`
   - Extbase repository queries use model property names, not column names

5. **Testing Infrastructure**
   - PHPUnit configuration
   - Functional test setup
   - CI/CD workflow

6. **Generate Conformance Report**
   Use the conformance-report outputStyle.

7. **Provide prioritized action items**
   - Order by severity and effort
   - Include specific code fixes
