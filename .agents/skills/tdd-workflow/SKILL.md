---
name: tdd-workflow
description: 新機能実装・バグ修正・リファクタリング時に使用するスキル。80%以上のカバレッジ（ユニット・インテグレーション・E2E）を確保するテスト駆動開発を徹底する。
---

# テスト駆動開発ワークフロー

すべてのコード開発がTDDの原則に従い、包括的なテストカバレッジを確保するためのスキル。

## 適用タイミング

- 新機能・新しい処理を実装するとき
- バグ・不具合を修正するとき
- 既存コードをリファクタリングするとき
- APIエンドポイントを追加するとき
- 新しいコンポーネントを作成するとき
- **既存コードを別言語へ移植するとき**（Python → TypeScript 等。元の振る舞いをテストで固定してから書く）

## 関連する開発フロー方針（必ず一緒に守る）

TDD は単独では機能しない。以下のルールとセットで守ること（詳細は `coding-standards` スキル）：

1. **main 直 push 禁止**：作業はトピックブランチで行う
2. **ライブラリは公開3日以上経過した版のみ**：vitest／jest／playwright 等のテストツール導入時も同じ基準を適用
3. **コミットは適切な粒度**：「テスト追加」と「実装追加」は分けてコミットする（RED と GREEN を別 commit にすると履歴が読みやすい）
4. **TDD は本スキル**：このドキュメント全体

## 移植・リファクタ時の TDD

元コードがある場合、最初のテストは「元コードと同じ出力を返す」ことを期待値として固定する。具体的手順：

1. 元コードを実行して期待値を生成（例：Python 側で `json.dumps(get_stats(df))` の結果を保存）
2. その期待値をテストの fixture として保存（`tests/fixtures/expected_stats.json` 等）
3. 移植先のテストで「fixture と一致する」アサーションを書く
4. 移植コードを書いてテストを通す

これによりランダム要素や境界条件を含むロジックも安全に移植できる。

## 基本原則

### 1. コードの前にテストを書く

必ずテストを先に書き、そのテストを通過させる形で実装する。

### 2. カバレッジ要件

- 最低80%のカバレッジ（ユニット + インテグレーション + E2E）
- すべてのエッジケースを網羅
- エラーシナリオをテスト済み
- 境界条件を検証済み

### 3. テストの種類

#### ユニットテスト

- 個々の関数・ユーティリティ
- コンポーネントのロジック
- 純粋関数
- ヘルパー・ユーティリティ

#### インテグレーションテスト

- APIエンドポイント
- データベース操作
- サービス間の連携
- 外部API呼び出し

#### E2Eテスト（Playwright）

- 重要なユーザーフロー
- 完全なワークフロー
- ブラウザ操作
- UIインタラクション

## TDDワークフローのステップ

### ステップ1：ユーザージャーニーを書く

```text
[役割]として、[目的]のために[アクション]したい

例：
ユーザーとして、正確なキーワードがなくても関連するマーケットを見つけられるよう、
マーケットをセマンティック検索したい。
```

### ステップ2：テストケースを生成する

各ユーザージャーニーに対して、包括的なテストケースを作成する：

```typescript
describe('セマンティック検索', () => {
  it('クエリに関連するマーケットを返す', async () => {
    // テスト実装
  })

  it('空のクエリを適切に処理する', async () => {
    // エッジケースのテスト
  })

  it('Redisが利用できない場合は部分一致検索にフォールバックする', async () => {
    // フォールバック動作のテスト
  })

  it('類似度スコアで結果を並び替える', async () => {
    // ソートロジックのテスト
  })
})
```

### ステップ3：テストを実行する（失敗することを確認）

```bash
npm test
# テストは失敗するはず — まだ実装していない
```

### ステップ4：コードを実装する

テストを通過させるための最小限のコードを書く：

```typescript
// テストに導かれた実装
export async function searchMarkets(query: string) {
  // 実装
}
```

### ステップ5：テストを再実行する

```bash
npm test
# テストが通過するはず
```

### ステップ6：リファクタリングする

テストをグリーンに保ちながらコード品質を改善する：

- 重複の除去
- 命名の改善
- パフォーマンスの最適化
- 可読性の向上

### ステップ7：カバレッジを確認する

```bash
npm run test:coverage
# 80%以上のカバレッジを確認
```

## テストパターン

### ユニットテストパターン（Jest / Vitest）

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Buttonコンポーネント', () => {
  it('正しいテキストでレンダリングされる', () => {
    render(<Button>クリック</Button>)
    expect(screen.getByText('クリック')).toBeInTheDocument()
  })

  it('クリック時にonClickが呼ばれる', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>クリック</Button>)

    fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('disabled propがtrueのとき非活性になる', () => {
    render(<Button disabled>クリック</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

### APIインテグレーションテストパターン

```typescript
import { NextRequest } from 'next/server'
import { GET } from './route'

describe('GET /api/markets', () => {
  it('マーケット一覧を正常に返す', async () => {
    const request = new NextRequest('http://localhost/api/markets')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.success).toBe(true)
    expect(Array.isArray(data.data)).toBe(true)
  })

  it('クエリパラメータを検証する', async () => {
    const request = new NextRequest('http://localhost/api/markets?limit=invalid')
    const response = await GET(request)

    expect(response.status).toBe(400)
  })

  it('データベースエラーを適切に処理する', async () => {
    // データベース障害をモック
    const request = new NextRequest('http://localhost/api/markets')
    // エラーハンドリングのテスト
  })
})
```

### E2Eテストパターン（Playwright）

```typescript
import { test, expect } from '@playwright/test'

test('ユーザーがマーケットを検索・絞り込みできる', async ({ page }) => {
  // マーケットページへ移動
  await page.goto('/')
  await page.click('a[href="/markets"]')

  // ページ読み込みを確認
  await expect(page.locator('h1')).toContainText('マーケット')

  // マーケットを検索
  await page.fill('input[placeholder="マーケットを検索"]', '選挙')

  // デバウンスと結果を待機
  await page.waitForTimeout(600)

  // 検索結果の表示を確認
  const results = page.locator('[data-testid="market-card"]')
  await expect(results).toHaveCount(5, { timeout: 5000 })

  // 結果に検索語が含まれることを確認
  const firstResult = results.first()
  await expect(firstResult).toContainText('選挙', { ignoreCase: true })

  // ステータスで絞り込む
  await page.click('button:has-text("アクティブ")')

  // 絞り込み結果を確認
  await expect(results).toHaveCount(3)
})

test('ユーザーが新しいマーケットを作成できる', async ({ page }) => {
  // ログイン
  await page.goto('/creator-dashboard')

  // マーケット作成フォームに入力
  await page.fill('input[name="name"]', 'テストマーケット')
  await page.fill('textarea[name="description"]', 'テスト説明')
  await page.fill('input[name="endDate"]', '2025-12-31')

  // フォームを送信
  await page.click('button[type="submit"]')

  // 成功メッセージを確認
  await expect(page.locator('text=マーケットを作成しました')).toBeVisible()

  // マーケットページへのリダイレクトを確認
  await expect(page).toHaveURL(/\/markets\/test-market/)
})
```

## テストファイルの構成

```text
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx          # ユニットテスト
│   │   └── Button.stories.tsx       # Storybook
│   └── MarketCard/
│       ├── MarketCard.tsx
│       └── MarketCard.test.tsx
├── app/
│   └── api/
│       └── markets/
│           ├── route.ts
│           └── route.test.ts         # インテグレーションテスト
└── e2e/
    ├── markets.spec.ts               # E2Eテスト
    ├── trading.spec.ts
    └── auth.spec.ts
```

## 外部サービスのモック

### Supabaseモック

```typescript
jest.mock('@/lib/supabase', () => ({
  supabase: {
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => Promise.resolve({
          data: [{ id: 1, name: 'テストマーケット' }],
          error: null
        }))
      }))
    }))
  }
}))
```

### Redisモック

```typescript
jest.mock('@/lib/redis', () => ({
  searchMarketsByVector: jest.fn(() => Promise.resolve([
    { slug: 'test-market', similarity_score: 0.95 }
  ])),
  checkRedisHealth: jest.fn(() => Promise.resolve({ connected: true }))
}))
```

### OpenAIモック

```typescript
jest.mock('@/lib/openai', () => ({
  generateEmbedding: jest.fn(() => Promise.resolve(
    new Array(1536).fill(0.1) // 1536次元の埋め込みをモック
  ))
}))
```

## Pythonのテストパターン

### ユニットテストパターン（pytest）

```python
import pytest
from unittest.mock import MagicMock, patch
from myapp.services import UserService

class TestUserService:
    def test_get_user_returns_user(self):
        repo = MagicMock()
        repo.find_by_id.return_value = {"id": 1, "name": "テストユーザー"}
        service = UserService(repo)

        user = service.get_user(1)

        assert user["name"] == "テストユーザー"
        repo.find_by_id.assert_called_once_with(1)

    def test_get_user_raises_when_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        service = UserService(repo)

        with pytest.raises(ValueError, match="ユーザーが見つかりません"):
            service.get_user(999)

    @pytest.mark.parametrize("query,expected_count", [
        ("", 0),
        ("a", 5),
        ("テスト", 3),
    ])
    def test_search_returns_correct_count(self, query, expected_count):
        # パラメータ化テストでエッジケースを網羅する
        results = search_markets(query)
        assert len(results) == expected_count
```

### APIインテグレーションテストパターン（FastAPI / pytest）

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from myapp.main import app

client = TestClient(app)

class TestMarketsEndpoint:
    def test_get_markets_returns_200(self):
        response = client.get("/api/markets")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_invalid_limit_returns_400(self):
        response = client.get("/api/markets?limit=invalid")
        assert response.status_code == 422  # FastAPIのバリデーションエラー

    def test_database_error_returns_500(self):
        with patch("myapp.routers.markets.get_db") as mock_db:
            mock_db.side_effect = Exception("DB接続エラー")
            response = client.get("/api/markets")
        assert response.status_code == 500
```

### 外部サービスのモック（Python）

```python
from unittest.mock import patch, AsyncMock

# Supabaseモック
@patch("myapp.db.supabase_client")
def test_fetch_market(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = \
        MagicMock(data=[{"id": 1, "name": "テストマーケット"}])

    result = fetch_market(1)
    assert result["name"] == "テストマーケット"

# 非同期サービスのモック
@pytest.mark.asyncio
async def test_generate_embedding():
    with patch("myapp.openai_client.embeddings.create", new_callable=AsyncMock) as mock:
        mock.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 1536)])
        embedding = await generate_embedding("テストテキスト")
    assert len(embedding) == 1536

# Redisモック
@patch("myapp.cache.redis_client")
def test_cache_hit(mock_redis):
    mock_redis.get.return_value = b'{"slug": "test", "score": 0.95}'
    result = get_cached_market("test")
    assert result["slug"] == "test"
```

### フィクスチャとファクトリ

```python
import pytest
from myapp.models import Market, User

@pytest.fixture
def sample_market():
    return Market(id=1, name="テストマーケット", status="active")

@pytest.fixture
def db_session(tmp_path):
    # テスト用インメモリDBを使用する
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()

def test_market_creation(db_session, sample_market):
    db_session.add(sample_market)
    db_session.commit()
    fetched = db_session.get(Market, 1)
    assert fetched.name == "テストマーケット"
```

## テストカバレッジの確認

### TypeScript（Jest）カバレッジ

```bash
npm run test:coverage
```

```json
{
  "jest": {
    "coverageThresholds": {
      "global": {
        "branches": 80,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

### Python（pytest-cov）カバレッジ

```bash
pytest --cov=myapp --cov-report=term-missing --cov-fail-under=80
```

```ini
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=myapp --cov-report=term-missing"

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

## よくあるテストのミス

### NG：実装の詳細をテストしている

```typescript
// 内部状態をテストしない
expect(component.state.count).toBe(5)
```

### OK：ユーザーに見える振る舞いをテストする

```typescript
// ユーザーが見るものをテストする
expect(screen.getByText('Count: 5')).toBeInTheDocument()
```

### NG：壊れやすいセレクター

```typescript
// 変更に弱い
await page.click('.css-class-xyz')
```

### OK：セマンティックなセレクター

```typescript
// 変更に強い
await page.click('button:has-text("送信")')
await page.click('[data-testid="submit-button"]')
```

### NG：テスト間に依存関係がある

```typescript
// テストが互いに依存している
test('ユーザーを作成する', () => { /* ... */ })
test('同じユーザーを更新する', () => { /* 前のテストに依存 */ })
```

### OK：テストを独立させる

```typescript
// 各テストが自身のデータを準備する
test('ユーザーを作成する', () => {
  const user = createTestUser()
  // テストロジック
})

test('ユーザーを更新する', () => {
  const user = createTestUser()
  // 更新ロジック
})
```

## 継続的なテスト

### 開発中のウォッチモード

```bash
npm test -- --watch
# ファイル変更時に自動でテストが実行される
```

### コミット前フック

```bash
# コミットのたびに実行される
npm test && npm run lint
```

### CI/CD連携

```yaml
# GitHub Actions
- name: テストの実行
  run: npm test -- --coverage
- name: カバレッジのアップロード
  uses: codecov/codecov-action@v3
```

## ベストプラクティス

1. **テストを先に書く** — 必ずTDD
2. **テストごとに1つのアサーション** — 単一の振る舞いに集中する
3. **説明的なテスト名** — 何をテストしているかを明示する
4. **Arrange-Act-Assert** — テスト構造を明確にする
5. **外部依存をモックする** — ユニットテストを独立させる
6. **エッジケースをテストする** — null・undefined・空・大量データ
7. **エラーパスをテストする** — ハッピーパスだけでない
8. **テストを速く保つ** — ユニットテストは1件50ms未満
9. **テスト後にクリーンアップする** — 副作用を残さない
10. **カバレッジレポートを確認する** — 漏れを特定する

## 成功の基準

- コードカバレッジ80%以上達成
- すべてのテストが通過（グリーン）
- スキップ・無効化されたテストがない
- テスト実行が速い（ユニットテストは30秒未満）
- E2Eテストが重要なユーザーフローを網羅
- テストが本番前にバグを検出している

---

**重要：** テストは任意ではない。自信を持ったリファクタリング・高速な開発・本番環境の信頼性を支える安全網である。
