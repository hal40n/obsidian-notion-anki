---
name: e2e-testing
description: PlaywrightのE2Eテストパターン・Page Object Model・設定・CI/CD連携・アーティファクト管理・フレーキーテスト対策。
---

# E2Eテストパターン

安定性・速度・保守性の高いE2Eテストスイートを構築するための、包括的なPlaywrightパターン集。

## テストファイルの構成

```
tests/
├── e2e/
│   ├── auth/
│   │   ├── login.spec.ts
│   │   ├── logout.spec.ts
│   │   └── register.spec.ts
│   ├── features/
│   │   ├── browse.spec.ts
│   │   ├── search.spec.ts
│   │   └── create.spec.ts
│   └── api/
│       └── endpoints.spec.ts
├── fixtures/
│   ├── auth.ts
│   └── data.ts
└── playwright.config.ts
```

## Page Object Model（POM）

```typescript
import { Page, Locator } from '@playwright/test'

export class ItemsPage {
  readonly page: Page
  readonly searchInput: Locator
  readonly itemCards: Locator
  readonly createButton: Locator

  constructor(page: Page) {
    this.page = page
    this.searchInput = page.locator('[data-testid="search-input"]')
    this.itemCards = page.locator('[data-testid="item-card"]')
    this.createButton = page.locator('[data-testid="create-btn"]')
  }

  async goto() {
    await this.page.goto('/items')
    await this.page.waitForLoadState('networkidle')
  }

  async search(query: string) {
    await this.searchInput.fill(query)
    await this.page.waitForResponse(resp => resp.url().includes('/api/search'))
    await this.page.waitForLoadState('networkidle')
  }

  async getItemCount() {
    return await this.itemCards.count()
  }
}
```

## テスト構造

```typescript
import { test, expect } from '@playwright/test'
import { ItemsPage } from '../../pages/ItemsPage'

test.describe('アイテム検索', () => {
  let itemsPage: ItemsPage

  test.beforeEach(async ({ page }) => {
    itemsPage = new ItemsPage(page)
    await itemsPage.goto()
  })

  test('キーワードで検索できる', async ({ page }) => {
    await itemsPage.search('test')

    const count = await itemsPage.getItemCount()
    expect(count).toBeGreaterThan(0)

    await expect(itemsPage.itemCards.first()).toContainText(/test/i)
    await page.screenshot({ path: 'artifacts/search-results.png' })
  })

  test('結果がない場合を処理できる', async ({ page }) => {
    await itemsPage.search('xyznonexistent123')

    await expect(page.locator('[data-testid="no-results"]')).toBeVisible()
    expect(await itemsPage.getItemCount()).toBe(0)
  })
})
```

## Playwright設定

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'playwright-results.xml' }],
    ['json', { outputFile: 'playwright-results.json' }]
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
})
```

## フレーキーテスト対策

### 隔離（Quarantine）

```typescript
test('フレーキー: 複雑な検索', async ({ page }) => {
  test.fixme(true, 'フレーキー - Issue #123')
  // テストコード...
})

test('条件付きスキップ', async ({ page }) => {
  test.skip(process.env.CI, 'CIでフレーキー - Issue #123')
  // テストコード...
})
```

### フレーキーの特定

```bash
npx playwright test tests/search.spec.ts --repeat-each=10
npx playwright test tests/search.spec.ts --retries=3
```

### よくある原因と修正

**レースコンディション：**
```typescript
// BAD: 要素の準備を前提としている
await page.click('[data-testid="button"]')

// GOOD: 自動待機ロケーターを使う
await page.locator('[data-testid="button"]').click()
```

**ネットワークのタイミング：**
```typescript
// BAD: 任意のタイムアウト
await page.waitForTimeout(5000)

// GOOD: 特定の条件を待つ
await page.waitForResponse(resp => resp.url().includes('/api/data'))
```

**アニメーションのタイミング：**
```typescript
// BAD: アニメーション中にクリック
await page.click('[data-testid="menu-item"]')

// GOOD: 安定するまで待つ
await page.locator('[data-testid="menu-item"]').waitFor({ state: 'visible' })
await page.waitForLoadState('networkidle')
await page.locator('[data-testid="menu-item"]').click()
```

## アーティファクト管理

### スクリーンショット

```typescript
await page.screenshot({ path: 'artifacts/after-login.png' })
await page.screenshot({ path: 'artifacts/full-page.png', fullPage: true })
await page.locator('[data-testid="chart"]').screenshot({ path: 'artifacts/chart.png' })
```

### トレース

```typescript
await browser.startTracing(page, {
  path: 'artifacts/trace.json',
  screenshots: true,
  snapshots: true,
})
// ... テストの操作 ...
await browser.stopTracing()
```

### 動画

```typescript
// playwright.config.ts
use: {
  video: 'retain-on-failure',
  videosPath: 'artifacts/videos/'
}
```

## CI/CD連携

```yaml
# .github/workflows/e2e.yml
name: E2Eテスト
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
        env:
          BASE_URL: ${{ vars.STAGING_URL }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

## テストレポートテンプレート

```markdown
# E2Eテストレポート

**日時：** YYYY-MM-DD HH:MM
**所要時間：** Xm Ys
**ステータス：** PASSING / FAILING

## サマリー
- 合計: X | 成功: Y (Z%) | 失敗: A | フレーキー: B | スキップ: C

## 失敗したテスト

### テスト名
**ファイル：** `tests/e2e/feature.spec.ts:45`
**エラー：** 要素が表示されていることを期待していた
**スクリーンショット：** artifacts/failed.png
**推奨される修正：** [説明]

## アーティファクト
- HTMLレポート: playwright-report/index.html
- スクリーンショット: artifacts/*.png
- 動画: artifacts/videos/*.webm
- トレース: artifacts/*.zip
```

## ウォレット / Web3のテスト

```typescript
test('ウォレット接続', async ({ page, context }) => {
  // ウォレットプロバイダーをモック
  await context.addInitScript(() => {
    window.ethereum = {
      isMetaMask: true,
      request: async ({ method }) => {
        if (method === 'eth_requestAccounts')
          return ['0x1234567890123456789012345678901234567890']
        if (method === 'eth_chainId') return '0x1'
      }
    }
  })

  await page.goto('/')
  await page.locator('[data-testid="connect-wallet"]').click()
  await expect(page.locator('[data-testid="wallet-address"]')).toContainText('0x1234')
})
```

## 金融 / 重要フローのテスト

```typescript
test('取引実行', async ({ page }) => {
  // 本番環境ではスキップ（実際のお金が動く）
  test.skip(process.env.NODE_ENV === 'production', '本番環境ではスキップ')

  await page.goto('/markets/test-market')
  await page.locator('[data-testid="position-yes"]').click()
  await page.locator('[data-testid="trade-amount"]').fill('1.0')

  // プレビューを確認
  const preview = page.locator('[data-testid="trade-preview"]')
  await expect(preview).toContainText('1.0')

  // 確認してブロックチェーンの完了を待つ
  await page.locator('[data-testid="confirm-trade"]').click()
  await page.waitForResponse(
    resp => resp.url().includes('/api/trade') && resp.status() === 200,
    { timeout: 30000 }
  )

  await expect(page.locator('[data-testid="trade-success"]')).toBeVisible()
})
```
