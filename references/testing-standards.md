# TYPO3 Testing Standards

**Source:** TYPO3 Core API Reference - Testing
**Purpose:** Unit, functional, and acceptance testing standards for TYPO3 extensions

## Testing Framework

TYPO3 uses **typo3/testing-framework** for comprehensive testing:

```bash
# Install testing framework
composer require --dev \
  "typo3/testing-framework":"^8.0.9" \
  "phpunit/phpunit":"^10.5"
```

## Unit Testing

### Unit Test Structure

```php
// ✅ Right: Proper unit test structure
<?php
declare(strict_types=1);

namespace Vendor\ExtensionKey\Tests\Unit\Service;

use TYPO3\TestingFramework\Core\Unit\UnitTestCase;
use Vendor\ExtensionKey\Service\CalculationService;

class CalculationServiceTest extends UnitTestCase
{
    private CalculationService $subject;

    protected function setUp(): void
    {
        parent::setUp();
        $this->subject = new CalculationService();
    }

    /**
     * @test
     */
    public function addReturnsCorrectSum(): void
    {
        $result = $this->subject->add(2, 3);
        $this->assertEquals(5, $result);
    }

    /**
     * @test
     */
    public function multiplyReturnsCorrectProduct(): void
    {
        $result = $this->subject->multiply(4, 5);
        $this->assertEquals(20, $result);
    }
}
```

### PHPUnit Configuration

```xml
<!-- Build/phpunit/UnitTests.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<phpunit
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/10.5/phpunit.xsd"
    bootstrap="../../vendor/typo3/testing-framework/Resources/Core/Build/UnitTestsBootstrap.php"
    colors="true"
    beStrictAboutTestsThatDoNotTestAnything="true"
    failOnWarning="true"
    failOnRisky="true"
    stopOnFailure="false"
>
    <testsuites>
        <testsuite name="Unit tests">
            <directory>../../Tests/Unit/</directory>
        </testsuite>
    </testsuites>
</phpunit>
```

### Running Unit Tests

```bash
# Direct execution
vendor/bin/phpunit -c Build/phpunit/UnitTests.xml

# DDEV execution
ddev exec php vendor/bin/phpunit -c Build/phpunit/UnitTests.xml

# Run specific test
vendor/bin/phpunit -c Build/phpunit/UnitTests.xml --filter "CalculationServiceTest"
```

### Unit Test Best Practices

**✅ Do:**
- Test single units (methods, functions) in isolation
- Mock external dependencies
- Test edge cases and boundary conditions
- Use descriptive test method names
- Follow naming: `methodName<Condition>Returns<Expected>`
- Keep tests fast (no database, no external services)

**❌ Don't:**
- Access database in unit tests
- Depend on file system
- Make HTTP requests
- Test framework internals
- Write integration tests as unit tests

## Functional Testing

### Functional Test Structure

```php
// ✅ Right: Proper functional test structure
<?php
declare(strict_types=1);

namespace Vendor\ExtensionKey\Tests\Functional\Domain\Repository;

use TYPO3\TestingFramework\Core\Functional\FunctionalTestCase;
use Vendor\ExtensionKey\Domain\Repository\ProductRepository;

class ProductRepositoryTest extends FunctionalTestCase
{
    protected array $testExtensionsToLoad = [
        'typo3conf/ext/my_extension',
    ];

    protected ProductRepository $subject;

    protected function setUp(): void
    {
        parent::setUp();

        // Load test data
        $this->importCSVDataSet(__DIR__ . '/Fixtures/products.csv');

        // Set up backend user
        $this->setUpBackendUser(1);

        // Initialize subject
        $this->subject = $this->get(ProductRepository::class);
    }

    /**
     * @test
     */
    public function findAllReturnsAllProducts(): void
    {
        $products = $this->subject->findAll();
        $this->assertCount(3, $products);
    }

    /**
     * @test
     */
    public function findByPriceRangeReturnsMatchingProducts(): void
    {
        $products = $this->subject->findByPriceRange(10.0, 50.0);
        $this->assertCount(2, $products);
    }
}
```

### PHPUnit Functional Configuration

```xml
<!-- Build/phpunit/FunctionalTests.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<phpunit
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/10.5/phpunit.xsd"
    bootstrap="../../vendor/typo3/testing-framework/Resources/Core/Build/FunctionalTestsBootstrap.php"
    colors="true"
    beStrictAboutTestsThatDoNotTestAnything="true"
    failOnWarning="true"
    failOnRisky="true"
    stopOnFailure="false"
>
    <testsuites>
        <testsuite name="Functional tests">
            <directory>../../Tests/Functional/</directory>
        </testsuite>
    </testsuites>
</phpunit>
```

### Running Functional Tests

```bash
# With MySQL/MariaDB
ddev exec \
  typo3DatabaseDriver='mysqli' \
  typo3DatabaseHost='db' \
  typo3DatabasePort=3306 \
  typo3DatabaseUsername='root' \
  typo3DatabasePassword='root' \
  typo3DatabaseName='func' \
  php vendor/bin/phpunit -c Build/phpunit/FunctionalTests.xml

# With SQLite (simpler)
ddev exec \
  typo3DatabaseDriver=pdo_sqlite \
  php vendor/bin/phpunit -c Build/phpunit/FunctionalTests.xml

# With PostgreSQL
ddev exec \
  typo3DatabaseDriver='pdo_pgsql' \
  typo3DatabaseHost='postgres' \
  typo3DatabasePort=5432 \
  typo3DatabaseUsername='postgres' \
  typo3DatabasePassword='postgres' \
  typo3DatabaseName='func' \
  php vendor/bin/phpunit -c Build/phpunit/FunctionalTests.xml
```

### Test Data Fixtures

```csv
# Tests/Functional/Fixtures/products.csv
tx_myext_product,uid,pid,title,price,available
,1,0,Product A,29.99,1
,2,0,Product B,49.99,1
,3,0,Product C,99.99,0
```

### Loading Extensions in Tests

```php
// Load extension under test
protected array $testExtensionsToLoad = [
    'typo3conf/ext/my_extension',
];

// Load additional core extensions
protected array $coreExtensionsToLoad = [
    'typo3/cms-workspaces',
];

// Load fixture extensions
protected array $testExtensionsToLoad = [
    'typo3conf/ext/my_extension',
    'typo3conf/ext/my_extension/Tests/Functional/Fixtures/Extensions/fixture_extension',
];
```

## E2E Testing with Playwright

TYPO3 Core uses **Playwright** exclusively for end-to-end and accessibility testing. This is the modern standard for browser-based testing in TYPO3 extensions.

**Reference:** [TYPO3 Core Build/tests/playwright](https://github.com/TYPO3/typo3/tree/main/Build/tests/playwright)

### Requirements

```json
// package.json
{
  "engines": {
    "node": ">=22.18.0 <23.0.0",
    "npm": ">=11.5.2"
  },
  "devDependencies": {
    "@playwright/test": "^1.56.1",
    "@axe-core/playwright": "^4.9.0"
  },
  "scripts": {
    "playwright:install": "playwright install",
    "playwright:open": "playwright test --ui --ignore-https-errors",
    "playwright:run": "playwright test",
    "playwright:codegen": "playwright codegen"
  }
}
```

### Playwright Configuration

```typescript
// Build/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';
import config from './tests/playwright/config';

export default defineConfig({
  testDir: './tests/playwright',
  timeout: 30000,
  expect: {
    timeout: 10000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../typo3temp/var/tests/playwright-reports' }],
  ],
  outputDir: '../typo3temp/var/tests/playwright-results',

  use: {
    baseURL: config.baseUrl,
    ignoreHTTPSErrors: true,
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'login setup',
      testMatch: /helper\/login\.setup\.ts/,
    },
    {
      name: 'accessibility',
      testMatch: /accessibility\/.*\.spec\.ts/,
      dependencies: ['login setup'],
      use: {
        storageState: './.auth/login.json',
      },
    },
    {
      name: 'e2e',
      testMatch: /e2e\/.*\.spec\.ts/,
      dependencies: ['login setup'],
      use: {
        storageState: './.auth/login.json',
      },
    },
  ],
});
```

### TYPO3-Specific Configuration

```typescript
// Build/tests/playwright/config.ts
export default {
  baseUrl: process.env.PLAYWRIGHT_BASE_URL ?? 'http://web:80/typo3/',
  admin: {
    username: process.env.PLAYWRIGHT_ADMIN_USERNAME ?? 'admin',
    password: process.env.PLAYWRIGHT_ADMIN_PASSWORD ?? 'password',
  },
};
```

### Directory Structure

```
Build/
├── playwright.config.ts          # Main Playwright configuration
├── package.json                  # Node dependencies
├── .nvmrc                        # Node version (22.18)
└── tests/
    └── playwright/
        ├── config.ts             # TYPO3-specific config (baseUrl, credentials)
        ├── e2e/                   # End-to-end tests
        │   ├── dashboard/
        │   ├── extensions/
        │   ├── layout/
        │   ├── list/
        │   ├── media/
        │   ├── preview/
        │   ├── recycler/
        │   ├── redirects/
        │   ├── reports/
        │   ├── setup/
        │   └── users/
        ├── accessibility/        # Accessibility tests (axe-core)
        │   └── modules.spec.ts
        ├── fixtures/             # Page Object Models
        │   ├── setup-fixtures.ts
        │   ├── backend-page.ts
        │   ├── page-tree.ts
        │   ├── file-tree.ts
        │   ├── form-engine.ts
        │   ├── modal.ts
        │   └── doc-header.ts
        └── helper/
            └── login.setup.ts    # Authentication setup
```

### Authentication Setup

```typescript
// Build/tests/playwright/helper/login.setup.ts
import { test as setup, expect } from '@playwright/test';
import config from '../config';

setup('login', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Username').fill(config.admin.username);
  await page.getByLabel('Password').fill(config.admin.password);
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForLoadState('networkidle');

  // Verify login succeeded
  await expect(page.locator('.t3js-topbar-button-modulemenu')).toBeVisible();

  // Save authentication state
  await page.context().storageState({ path: './.auth/login.json' });
});
```

### Page Object Model (Fixtures)

```typescript
// Build/tests/playwright/fixtures/backend-page.ts
import { type Page, type Locator, expect } from '@playwright/test';
import { PageTree } from './page-tree';
import { FormEngine } from './form-engine';
import { DocHeader } from './doc-header';
import { Modal } from './modal';
import { FileTree } from './file-tree';

export class BackendPage {
  readonly page: Page;
  readonly moduleMenu: Locator;
  readonly contentFrame: Locator;

  // Composed page objects
  readonly pageTree: PageTree;
  readonly formEngine: FormEngine;
  readonly docHeader: DocHeader;
  readonly modal: Modal;
  readonly fileTree: FileTree;

  constructor(page: Page) {
    this.page = page;
    this.moduleMenu = page.locator('#modulemenu');
    this.contentFrame = page.frameLocator('#typo3-contentIframe');

    this.pageTree = new PageTree(page);
    this.formEngine = new FormEngine(page);
    this.docHeader = new DocHeader(page);
    this.modal = new Modal(page);
    this.fileTree = new FileTree(page);
  }

  async gotoModule(identifier: string): Promise<void> {
    const moduleLink = this.moduleMenu.locator(`[data-modulemenu-identifier="${identifier}"]`);
    await moduleLink.click();
    await expect(moduleLink).toHaveClass(/modulemenu-action-active/);
  }

  async moduleLoaded(): Promise<void> {
    await this.page.evaluate(() => {
      return new Promise<void>((resolve) => {
        document.addEventListener('typo3-module-loaded', () => resolve(), { once: true });
      });
    });
  }

  async waitForModuleResponse(urlPattern: string | RegExp): Promise<void> {
    await this.page.waitForResponse((response) => {
      const url = response.url();
      const matches = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matches && response.status() === 200;
    });
  }
}
```

### Fixtures Setup

```typescript
// Build/tests/playwright/fixtures/setup-fixtures.ts
import { test as base, type Locator, expect } from '@playwright/test';
import { BackendPage } from './backend-page';
import { PageTree } from './page-tree';
import { Modal } from './modal';

type BackendFixtures = {
  backend: BackendPage;
  pageTree: PageTree;
  modal: Modal;
};

export const test = base.extend<BackendFixtures>({
  backend: async ({ page }, use) => {
    await use(new BackendPage(page));
  },
  pageTree: async ({ page }, use) => {
    await use(new PageTree(page));
  },
  modal: async ({ page }, use) => {
    await use(new Modal(page));
  },
});

export { expect, Locator };
```

### E2E Test Examples

```typescript
// Build/tests/playwright/e2e/layout/page-module.spec.ts
import { test, expect } from '../../fixtures/setup-fixtures';

test.describe('Page Module', () => {
  test('can access page module', async ({ backend }) => {
    await backend.gotoModule('web_layout');
    await backend.moduleLoaded();

    const contentFrame = backend.contentFrame;
    await expect(contentFrame.locator('h1')).toContainText('Page');
  });

  test('can select page in tree', async ({ backend, pageTree }) => {
    await backend.gotoModule('web_layout');
    await pageTree.selectPage('Home');

    await expect(backend.contentFrame.locator('.t3-page-ce')).toBeVisible();
  });

  test('can add content element', async ({ backend }) => {
    await backend.gotoModule('web_layout');
    await backend.contentFrame.getByRole('button', { name: 'Create new content element' }).click();

    await expect(backend.modal.container).toBeVisible();
    await expect(backend.modal.title).toContainText('Create new content element');
  });
});
```

### Accessibility Testing with axe-core

```typescript
// Build/tests/playwright/accessibility/modules.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const modules = [
  { name: 'Page Layout', route: 'module/web/layout' },
  { name: 'List Records', route: 'module/web/list' },
  { name: 'Site Configuration', route: 'module/site/configuration' },
  { name: 'Reports', route: 'module/system/reports' },
  { name: 'Recycler', route: 'module/web/recycler' },
];

for (const module of modules) {
  test(`${module.name} has no accessibility violations`, async ({ page }) => {
    await page.goto(module.route);
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('#typo3-contentIframe')
      .disableRules(['color-contrast']) // Reduce false positives
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
}
```

### Running Playwright Tests

```bash
# Install Playwright browsers
npm run playwright:install

# Run all tests
npm run playwright:run

# Run with UI mode (interactive)
npm run playwright:open

# Run specific test file
npx playwright test e2e/layout/page-module.spec.ts

# Run tests matching pattern
npx playwright test --grep "can access"

# Generate test code (record & playback)
npm run playwright:codegen

# Run in headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug

# Generate HTML report
npx playwright show-report
```

### DDEV Integration

```yaml
# .ddev/docker-compose.playwright.yaml
services:
  playwright:
    container_name: ddev-${DDEV_SITENAME}-playwright
    image: mcr.microsoft.com/playwright:v1.56.1-noble
    volumes:
      - ../:/var/www/html
    working_dir: /var/www/html/Build
    environment:
      - PLAYWRIGHT_BASE_URL=http://web:80/typo3/
    depends_on:
      - web
```

```bash
# Run Playwright in DDEV
ddev exec -s playwright npx playwright test

# Or using DDEV custom command
# .ddev/commands/web/playwright
#!/bin/bash
cd /var/www/html/Build && npx playwright "$@"
```

### CI/CD Integration

```yaml
# .github/workflows/playwright.yml
name: Playwright Tests

on: [push, pull_request]

jobs:
  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install dependencies
        working-directory: ./Build
        run: npm ci

      - name: Install Playwright browsers
        working-directory: ./Build
        run: npx playwright install --with-deps chromium

      - name: Start TYPO3
        run: |
          # Start DDEV or Docker environment
          ddev start
          ddev import-db --file=.ddev/db.sql.gz

      - name: Run Playwright tests
        working-directory: ./Build
        run: npx playwright test
        env:
          PLAYWRIGHT_BASE_URL: https://myproject.ddev.site/typo3/

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: typo3temp/var/tests/playwright-reports/
          retention-days: 30
```

### Best Practices

**✅ Do:**
- Use Page Object Model (fixtures) for reusability
- Store authentication state to avoid repeated logins
- Test user-visible behavior, not implementation details
- Use descriptive test names that explain the scenario
- Wait for specific elements, not arbitrary timeouts
- Use `data-testid` attributes for stable selectors
- Test accessibility with axe-core
- Run tests in CI with proper environment setup

**❌ Don't:**
- Use `page.waitForTimeout()` - use specific waits instead
- Depend on CSS classes that may change
- Test internal TYPO3 Core behavior
- Skip accessibility testing
- Ignore flaky tests - fix the root cause
- Use hard-coded credentials in code (use env vars)

## Test Organization

### Directory Structure

```
Tests/
├── Unit/                         # PHP unit tests
│   ├── Controller/
│   │   └── ProductControllerTest.php
│   ├── Domain/
│   │   ├── Model/
│   │   │   └── ProductTest.php
│   │   └── Repository/
│   │       └── ProductRepositoryTest.php
│   └── Service/
│       └── CalculationServiceTest.php
├── Functional/                   # PHP functional tests
│   ├── Domain/
│   │   └── Repository/
│   │       ├── ProductRepositoryTest.php
│   │       └── Fixtures/
│   │           └── products.csv
│   └── Controller/
│       └── ProductControllerTest.php
Build/
├── playwright.config.ts          # Playwright configuration
├── package.json                  # Node dependencies
├── .nvmrc                        # Node version
└── tests/
    └── playwright/               # Playwright E2E tests
        ├── config.ts             # TYPO3-specific config
        ├── e2e/                   # End-to-end tests
        │   ├── backend/
        │   │   └── module.spec.ts
        │   └── frontend/
        │       └── pages.spec.ts
        ├── accessibility/        # Accessibility tests
        │   └── modules.spec.ts
        ├── fixtures/             # Page Object Models
        │   ├── setup-fixtures.ts
        │   └── backend-page.ts
        └── helper/
            └── login.setup.ts
```

### Naming Conventions

**Unit Tests:**
- Pattern: `<ClassName>Test.php`
- Example: `ProductRepository.php` → `ProductRepositoryTest.php`
- Location: Mirror `Classes/` structure in `Tests/Unit/`

**Functional Tests:**
- Pattern: `<ClassName>Test.php`
- Example: `ProductRepository.php` → `ProductRepositoryTest.php`
- Location: Mirror `Classes/` structure in `Tests/Functional/`

**E2E Tests (Playwright):**
- Pattern: `<feature>.spec.ts`
- Example: `page-module.spec.ts`, `login.spec.ts`
- Location: `Build/tests/playwright/e2e/<category>/`

**Accessibility Tests (Playwright):**
- Pattern: `<area>.spec.ts`
- Example: `modules.spec.ts`, `forms.spec.ts`
- Location: `Build/tests/playwright/accessibility/`

## PHPUnit Attributes (PHP 8.0+)

```php
// ✅ Right: Using PHPUnit attributes
<?php
declare(strict_types=1);

namespace Vendor\ExtensionKey\Tests\Unit\Service;

use PHPUnit\Framework\Attributes\Test;
use PHPUnit\Framework\Attributes\DataProvider;
use TYPO3\TestingFramework\Core\Unit\UnitTestCase;

class CalculationServiceTest extends UnitTestCase
{
    #[Test]
    public function addReturnsCorrectSum(): void
    {
        $this->assertEquals(5, $this->subject->add(2, 3));
    }

    public static function priceDataProvider(): \Generator
    {
        yield 'standard price' => [
            'price' => 100.0,
            'taxRate' => 0.19,
            'expected' => 119.0,
        ];
        yield 'zero price' => [
            'price' => 0.0,
            'taxRate' => 0.19,
            'expected' => 0.0,
        ];
    }

    #[Test]
    #[DataProvider('priceDataProvider')]
    public function calculatePriceWithTax(float $price, float $taxRate, float $expected): void
    {
        $result = $this->subject->calculatePriceWithTax($price, $taxRate);
        $this->assertEquals($expected, $result);
    }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        php: ['8.1', '8.2', '8.3']
        typo3: ['12.4', '13.0']

    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}

      - name: Install dependencies
        run: composer install

      - name: Lint PHP
        run: find . -name \*.php ! -path "./vendor/*" -exec php -l {} \;

      - name: Unit Tests
        run: vendor/bin/phpunit -c Build/phpunit/UnitTests.xml

      - name: Functional Tests
        run: |
          typo3DatabaseDriver=pdo_sqlite \
          vendor/bin/phpunit -c Build/phpunit/FunctionalTests.xml
```

## Conformance Checklist

### Unit Tests
- [ ] Unit tests extend `UnitTestCase`
- [ ] Tests located in `Tests/Unit/` mirroring `Classes/`
- [ ] Test files named `<ClassName>Test.php`
- [ ] No database access in unit tests
- [ ] No file system access in unit tests
- [ ] All public methods tested
- [ ] Edge cases and boundaries tested
- [ ] #[Test] attribute or @test annotation used

### Functional Tests
- [ ] Functional tests extend `FunctionalTestCase`
- [ ] Tests located in `Tests/Functional/`
- [ ] `setUp()` calls `parent::setUp()` first
- [ ] Extensions loaded via `$testExtensionsToLoad`
- [ ] Test data loaded via `importCSVDataSet()`
- [ ] Database operations tested
- [ ] Backend user initialized when needed

### E2E Tests (Playwright)
- [ ] Playwright configured in `Build/playwright.config.ts`
- [ ] Tests located in `Build/tests/playwright/e2e/`
- [ ] Test files named `<feature>.spec.ts`
- [ ] Authentication setup in `helper/login.setup.ts`
- [ ] Page Object Models in `fixtures/` directory
- [ ] Storage state used for session persistence
- [ ] Tests verify user-visible behavior
- [ ] Accessibility tests in `accessibility/` directory
- [ ] axe-core used for WCAG compliance
- [ ] Node.js ≥22.18 specified in `.nvmrc`

### General
- [ ] PHPUnit configuration files present
- [ ] All tests pass locally
- [ ] CI/CD pipeline configured
- [ ] Test coverage >70% for new code
- [ ] Data providers use named arguments
- [ ] Descriptive test method names
