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

3. **Code Quality Checks**
   - PSR-12 compliance (check for php-cs-fixer config)
   - Strict types declaration in all PHP files
   - Dependency injection (Services.yaml)
   - No direct $GLOBALS access
   - No deprecated API usage

4. **TYPO3 Best Practices**
   - FlexForms in Configuration/FlexForms/
   - TypoScript in Configuration/TypoScript/
   - TCA in Configuration/TCA/
   - Fluid templates in Resources/Private/Templates/

5. **Testing Infrastructure**
   - PHPUnit configuration
   - Functional test setup
   - CI/CD workflow

6. **Generate Conformance Report**
   Use the conformance-report outputStyle.

7. **Provide prioritized action items**
   - Order by severity and effort
   - Include specific code fixes
