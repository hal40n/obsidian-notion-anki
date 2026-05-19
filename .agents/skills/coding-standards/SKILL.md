---
name: coding-standards
description: プロジェクト横断的なコーディング規約のベースライン。命名・可読性・イミュータビリティ・コード品質レビューに適用する。フレームワーク固有のパターンにはフロントエンドまたはバックエンドのスキルを使用すること。
---

# コーディング標準とベストプラクティス

プロジェクト横断的に適用できる、コーディング規約のベースライン。

このスキルは共通の土台であり、詳細なフレームワークのプレイブックではない。

- React・状態管理・フォーム・レンダリング・UIアーキテクチャには `frontend-patterns` を使用する
- リポジトリ/サービス層・エンドポイント設計・バリデーション・サーバー固有の関心事には `backend-patterns` または `api-design` を使用する
- フルなスキルウォークスルーではなく最短の再利用可能なルール層が必要な場合は `rules/common/coding-style.md` を使用する

---

## 開発フローの基本方針（必須・違反禁止）

以下の4つは、すべての開発作業に**例外なく**適用する。コードを書く前に毎回確認する。

### 1. main ブランチへの直接プッシュ禁止

- 作業前に必ずトピックブランチを切る：`git switch -c <type>/<short-description>`
- プレフィックス：`feat/` `fix/` `refactor/` `perf/` `docs/` `test/` `chore/`
- main から最新を取った上で派生：`git fetch origin && git switch -c <name> origin/main`
- 完了後は PR 作成（`gh pr create`）またはローカルで `git merge --no-ff <branch>` 後に push
- ユーザーが「直接 main で良い」と明示した場合のみ例外
- 既に main で作業を始めてしまったら、コミット前に `git switch -c <branch>` でブランチに変更を持ち越す

### 2. ライブラリは公開／更新から3日以上経過したバージョンのみ使用可

- 新規導入・アップデート時は、**そのバージョンの公開日**を必ず確認する
- 確認方法：`npm view <pkg> time` / `pip show <pkg>` / PyPI Release history / `gh release view` / GitHub Tags
- 3日未満なら**一つ前の安定版**を採用するか、3日経過まで待つ
- 「公開」には新規・パッチ・マイナー・メジャーすべてのリリースを含む
- バージョン無指定での `npx` / `uvx` / `pip install` は禁止。必ずバージョンを明示
- pre-commit hook・GitHub Actions の `uses:` も同じ基準で適用
- **理由**：公開直後はサプライチェーン攻撃や未発見バグの温床。3日のクッションで初期インシデント報告を観測する時間を確保

### 3. コミットはレビュー可能な粒度に分割

- **1 コミット ＝ 1 つの論理的変更**（新機能 1 つ、リファクタ 1 種、バグ修正 1 件）
- 目安：差分 200 行以下、変更ファイル 5〜10 個以下
- 依存関係順に積む：型定義 → ライブラリ層 → UI、テスト → 実装、リファクタ → 新機能
- メッセージは「何を／なぜ」を明示。`feat:`／`fix:`／`refactor:`／`perf:`／`docs:`／`test:`／`chore:` プレフィックス
- 関連する変更でも、検証や差し戻しの単位が違うなら分ける
- 既に大きい変更ができてしまった場合は `git add -p`／`git reset HEAD~` で分割を試みる

### 4. TDD（テスト駆動開発）の徹底

- 実装より先にテストを書く：**RED → GREEN → REFACTOR**
- 詳細は `tdd-workflow` スキルを参照
- 移植・リファクタも例外なし。元コードの出力を期待値スナップショットとして固定してから書く
- カバレッジ 80% 以上

---

## 有効化するタイミング

- 新しいプロジェクトやモジュールを開始するとき
- 品質と保守性のためにコードをレビューするとき
- 規約に従って既存コードをリファクタリングするとき
- 命名・フォーマット・構造の一貫性を強制するとき
- リント・フォーマット・型チェックのルールを設定するとき
- 新しいコントリビューターにコーディング規約を説明するとき

## スコープの境界

このスキルを有効化する対象：

- 説明的な命名
- イミュータビリティのデフォルト
- 可読性・KISS・DRY・YAGNIの徹底
- エラーハンドリングの期待値とコードスメルのレビュー

このスキルを主要なソースとして使わないもの：

- Reactのコンポジション・フック・レンダリングパターン
- バックエンドアーキテクチャ・API設計・データベース層
- より狭いスキルが既に存在するドメイン固有のフレームワークガイダンス

---

## コード品質の原則

### 1. 可読性第一

- コードは書かれるより読まれる回数の方が多い
- 変数名・関数名は明確にする
- コメントより自己文書化するコードを優先する
- 一貫したフォーマットを維持する

### 2. KISS（Keep It Simple, Stupid）

- 動作する最もシンプルな解決策を選ぶ
- 過剰設計を避ける
- 早すぎる最適化をしない
- 賢いコードより理解しやすいコード

### 3. DRY（Don't Repeat Yourself）

- 共通ロジックを関数として抽出する
- 再利用可能なコンポーネントを作る
- モジュール間でユーティリティを共有する
- コピペプログラミングを避ける

### 4. YAGNI（You Aren't Gonna Need It）

- 必要になる前に機能を作らない
- 投機的な汎用化を避ける
- 必要なときだけ複雑さを追加する
- シンプルに始めて、必要になったらリファクタリングする

---

## TypeScript/JavaScript 標準

### 変数の命名

```typescript
// PASS: GOOD: 説明的な名前
const marketSearchQuery = 'election'
const isUserAuthenticated = true
const totalRevenue = 1000

// FAIL: BAD: 不明瞭な名前
const q = 'election'
const flag = true
const x = 1000
```

### 関数の命名

```typescript
// PASS: GOOD: 動詞-名詞パターン
async function fetchMarketData(marketId: string) { }
function calculateSimilarity(a: number[], b: number[]) { }
function isValidEmail(email: string): boolean { }

// FAIL: BAD: 不明瞭または名詞のみ
async function market(id: string) { }
function similarity(a, b) { }
function email(e) { }
```

### イミュータビリティパターン（CRITICAL）

```typescript
// PASS: スプレッド演算子を常に使用する
const updatedUser = {
  ...user,
  name: 'New Name'
}

const updatedArray = [...items, newItem]

// FAIL: 直接ミューテーションは絶対にしない
user.name = 'New Name'  // BAD
items.push(newItem)     // BAD
```

### エラーハンドリング

```typescript
// PASS: GOOD: 包括的なエラーハンドリング
async function fetchData(url: string) {
  try {
    const response = await fetch(url)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Fetch failed:', error)
    throw new Error('Failed to fetch data')
  }
}

// FAIL: BAD: エラーハンドリングなし
async function fetchData(url) {
  const response = await fetch(url)
  return response.json()
}
```

### Async/Await のベストプラクティス

```typescript
// PASS: GOOD: 可能な場合は並列実行する
const [users, markets, stats] = await Promise.all([
  fetchUsers(),
  fetchMarkets(),
  fetchStats()
])

// FAIL: BAD: 不要なのに逐次実行している
const users = await fetchUsers()
const markets = await fetchMarkets()
const stats = await fetchStats()
```

### 型安全性

```typescript
// PASS: GOOD: 適切な型定義
interface Market {
  id: string
  name: string
  status: 'active' | 'resolved' | 'closed'
  created_at: Date
}

function getMarket(id: string): Promise<Market> {
  // 実装
}

// FAIL: BAD: 'any' の使用
function getMarket(id: any): Promise<any> {
  // 実装
}
```

---

## React ベストプラクティス

### コンポーネント構造

```typescript
// PASS: GOOD: 型定義付きの関数コンポーネント
interface ButtonProps {
  children: React.ReactNode
  onClick: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}

export function Button({
  children,
  onClick,
  disabled = false,
  variant = 'primary'
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {children}
    </button>
  )
}

// FAIL: BAD: 型なし・構造が不明瞭
export function Button(props) {
  return <button onClick={props.onClick}>{props.children}</button>
}
```

### カスタムフック

```typescript
// PASS: GOOD: 再利用可能なカスタムフック
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}

// 使用例
const debouncedQuery = useDebounce(searchQuery, 500)
```

### 状態管理

```typescript
// PASS: GOOD: 適切な状態更新
const [count, setCount] = useState(0)

// 前の状態に基づく更新には関数アップデートを使用する
setCount(prev => prev + 1)

// FAIL: BAD: 直接の状態参照
setCount(count + 1)  // 非同期シナリオで古くなる可能性がある
```

### 条件付きレンダリング

```typescript
// PASS: GOOD: 明確な条件付きレンダリング
{isLoading && <Spinner />}
{error && <ErrorMessage error={error} />}
{data && <DataDisplay data={data} />}

// FAIL: BAD: 三項演算子の連鎖
{isLoading ? <Spinner /> : error ? <ErrorMessage error={error} /> : data ? <DataDisplay data={data} /> : null}
```

---

## API設計標準

### REST APIの規約

```Text
GET    /api/markets              # 一覧取得
GET    /api/markets/:id          # 個別取得
POST   /api/markets              # 新規作成
PUT    /api/markets/:id          # 更新（全体）
PATCH  /api/markets/:id          # 更新（一部）
DELETE /api/markets/:id          # 削除

# フィルタリングにはクエリパラメータを使用
GET /api/markets?status=active&limit=10&offset=0
```

### レスポンスフォーマット

```typescript
// PASS: GOOD: 一貫したレスポンス構造
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}

// 成功レスポンス
return NextResponse.json({
  success: true,
  data: markets,
  meta: { total: 100, page: 1, limit: 10 }
})

// エラーレスポンス
return NextResponse.json({
  success: false,
  error: 'Invalid request'
}, { status: 400 })
```

### 入力バリデーション

```typescript
import { z } from 'zod'

// PASS: GOOD: スキーマバリデーション
const CreateMarketSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().min(1).max(2000),
  endDate: z.string().datetime(),
  categories: z.array(z.string()).min(1)
})

export async function POST(request: Request) {
  const body = await request.json()

  try {
    const validated = CreateMarketSchema.parse(body)
    // バリデーション済みデータで処理を続ける
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      }, { status: 400 })
    }
  }
}
```

---

## ファイル構成

### プロジェクト構造

```Text
src/
├── app/                    # Next.js App Router
│   ├── api/               # APIルート
│   ├── markets/           # Marketページ
│   └── (auth)/           # 認証ページ（ルートグループ）
├── components/            # Reactコンポーネント
│   ├── ui/               # 汎用UIコンポーネント
│   ├── forms/            # フォームコンポーネント
│   └── layouts/          # レイアウトコンポーネント
├── hooks/                # カスタムReactフック
├── lib/                  # ユーティリティと設定
│   ├── api/             # APIクライアント
│   ├── utils/           # ヘルパー関数
│   └── constants/       # 定数
├── types/                # TypeScript型定義
└── styles/              # グローバルスタイル
```

### ファイルの命名規則

```Text
components/Button.tsx          # コンポーネントはPascalCase
hooks/useAuth.ts              # フックはcamelCase（'use'プレフィックス）
lib/formatDate.ts             # ユーティリティはcamelCase
types/market.types.ts         # 型定義は.typesサフィックス
```

---

## コメントとドキュメント

### コメントを書くとき

```typescript
// PASS: GOOD: WHYを説明する（WHATではなく）
// 障害時にAPIを圧迫しないよう指数バックオフを使用する
const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)

// 大きな配列のパフォーマンスのため、意図的にミューテーションを使用している
items.push(newItem)

// FAIL: BAD: 明らかなことを述べている
// カウンターを1増やす
count++

// nameにユーザーの名前を設定する
name = user.name
```

### 公開APIへのJSDoc

```typescript
/**
 * 意味的類似性を使ってマーケットを検索する。
 *
 * @param query - 自然言語の検索クエリ
 * @param limit - 最大結果件数（デフォルト: 10）
 * @returns 類似度スコア順のマーケット配列
 * @throws {Error} OpenAI APIが失敗した場合やRedisが利用不可の場合
 *
 * @example
 * ```typescript
 * const results = await searchMarkets('election', 5)
 * console.log(results[0].name) // "Trump vs Biden"
 * ```
 */
export async function searchMarkets(
  query: string,
  limit: number = 10
): Promise<Market[]> {
  // 実装
}
```

---

## パフォーマンスのベストプラクティス

### メモ化

```typescript
import { useMemo, useCallback } from 'react'

// PASS: GOOD: 高コストな計算をメモ化する
const sortedMarkets = useMemo(() => {
  return markets.sort((a, b) => b.volume - a.volume)
}, [markets])

// PASS: GOOD: コールバックをメモ化する
const handleSearch = useCallback((query: string) => {
  setSearchQuery(query)
}, [])
```

### 遅延読み込み

```typescript
import { lazy, Suspense } from 'react'

// PASS: GOOD: 重いコンポーネントを遅延読み込みする
const HeavyChart = lazy(() => import('./HeavyChart'))

export function Dashboard() {
  return (
    <Suspense fallback={<Spinner />}>
      <HeavyChart />
    </Suspense>
  )
}
```

### データベースクエリ

```typescript
// PASS: GOOD: 必要なカラムだけ取得する
const { data } = await supabase
  .from('markets')
  .select('id, name, status')
  .limit(10)

// FAIL: BAD: すべてを取得する
const { data } = await supabase
  .from('markets')
  .select('*')
```

---

## テスト標準

### テスト構造（AAAパターン）

```typescript
test('類似度を正しく計算する', () => {
  // Arrange（準備）
  const vector1 = [1, 0, 0]
  const vector2 = [0, 1, 0]

  // Act（実行）
  const similarity = calculateCosineSimilarity(vector1, vector2)

  // Assert（検証）
  expect(similarity).toBe(0)
})
```

### テストの命名

```typescript
// PASS: GOOD: 説明的なテスト名
test('クエリに一致するマーケットがない場合に空配列を返す', () => { })
test('OpenAI APIキーが欠落している場合にエラーをスローする', () => { })
test('Redisが利用不可の場合に部分文字列検索にフォールバックする', () => { })

// FAIL: BAD: 曖昧なテスト名
test('動作する', () => { })
test('テスト検索', () => { })
```

---

## コードスメルの検出

以下のアンチパターンに注意する：

### 1. 長すぎる関数

```typescript
// FAIL: BAD: 50行超の関数
function processMarketData() {
  // 100行のコード
}

// PASS: GOOD: 小さな関数に分割する
function processMarketData() {
  const validated = validateData()
  const transformed = transformData(validated)
  return saveData(transformed)
}
```

### 2. 深いネスト

```typescript
// FAIL: BAD: 5段以上のネスト
if (user) {
  if (user.isAdmin) {
    if (market) {
      if (market.isActive) {
        if (hasPermission) {
          // 何か処理する
        }
      }
    }
  }
}

// PASS: GOOD: アーリーリターンを使う
if (!user) return
if (!user.isAdmin) return
if (!market) return
if (!market.isActive) return
if (!hasPermission) return

// 何か処理する
```

### 3. マジックナンバー

```typescript
// FAIL: BAD: 説明のない数値
if (retryCount > 3) { }
setTimeout(callback, 500)

// PASS: GOOD: 名前付き定数を使う
const MAX_RETRIES = 3
const DEBOUNCE_DELAY_MS = 500

if (retryCount > MAX_RETRIES) { }
setTimeout(callback, DEBOUNCE_DELAY_MS)
```

---

## Python 標準

### 変数・関数の命名

```python
# PASS: GOOD: 説明的な名前（snake_case）
market_search_query = 'election'
is_user_authenticated = True
total_revenue = 1000

def fetch_market_data(market_id: str) -> dict: ...
def calculate_similarity(vec_a: list, vec_b: list) -> float: ...
def is_valid_email(email: str) -> bool: ...

# FAIL: BAD: 不明瞭な名前
q = 'election'
flag = True
x = 1000

def market(id): ...
def sim(a, b): ...
```

### イミュータビリティパターン

```python
# PASS: GOOD: 新しいオブジェクトを返す
updated_user = {**user, "name": "New Name"}
updated_list = [*items, new_item]

# PASS: GOOD: dataclassのreplace
from dataclasses import replace
updated_user = replace(user, name="New Name")

# FAIL: BAD: 直接ミューテーション
user["name"] = "New Name"   # BAD（共有状態を変更する）
items.append(new_item)      # BAD（副作用がある）
```

### 型ヒント

```python
from typing import Optional
from dataclasses import dataclass

# PASS: GOOD: 型ヒント付きの関数と型定義
@dataclass
class Market:
    id: str
    name: str
    status: str  # 'active' | 'resolved' | 'closed'

def get_market(market_id: str) -> Optional[Market]:
    ...

def search_markets(query: str, limit: int = 10) -> list[Market]:
    ...

# FAIL: BAD: 型ヒントなし
def get_market(id):
    ...
```

### エラーハンドリング

```python
import logging

logger = logging.getLogger(__name__)

# PASS: GOOD: 具体的な例外・ログ・再スロー
def fetch_data(url: str) -> dict:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logger.error("タイムアウト: %s", url)
        raise
    except requests.HTTPError as e:
        logger.error("HTTPエラー %s: %s", e.response.status_code, url)
        raise

# FAIL: BAD: 握りつぶし・裸のexcept
def fetch_data(url):
    try:
        return requests.get(url).json()
    except:
        pass
```

### リソース管理

```python
# PASS: GOOD: コンテキストマネージャを使う
with open("data.json") as f:
    data = json.load(f)

with db.transaction():
    db.execute("INSERT INTO markets ...")

# FAIL: BAD: 手動クローズ（例外で閉じられない）
f = open("data.json")
data = json.load(f)
f.close()
```

### Pythonicなパターン

```python
# PASS: GOOD: リスト内包表記
active_markets = [m for m in markets if m.status == "active"]
market_names = [m.name for m in markets]

# PASS: GOOD: enumerate・zip
for i, market in enumerate(markets):
    print(f"{i}: {market.name}")

for market, score in zip(markets, scores):
    print(f"{market.name}: {score}")

# FAIL: BAD: Cスタイルのループ
active_markets = []
for m in markets:
    if m.status == "active":
        active_markets.append(m)
```

### 非同期処理

```python
import asyncio

# PASS: GOOD: 並列実行
async def fetch_all():
    users, markets, stats = await asyncio.gather(
        fetch_users(),
        fetch_markets(),
        fetch_stats()
    )
    return users, markets, stats

# FAIL: BAD: 逐次実行（並列化できる）
async def fetch_all():
    users = await fetch_users()
    markets = await fetch_markets()
    stats = await fetch_stats()
```

### ドキュメント（docstring）

```python
def search_markets(query: str, limit: int = 10) -> list[Market]:
    """意味的類似性を使ってマーケットを検索する。

    Args:
        query: 自然言語の検索クエリ
        limit: 最大結果件数（デフォルト: 10）

    Returns:
        類似度スコア順のMarketオブジェクトのリスト

    Raises:
        APIError: 外部APIへの接続に失敗した場合
        ValueError: queryが空文字の場合

    Example:
        >>> results = search_markets('election', 5)
        >>> print(results[0].name)
        'Trump vs Biden'
    """
```

### テスト（pytest）

```python
# PASS: GOOD: AAAパターン・説明的なテスト名
def test_returns_empty_list_when_no_markets_match():
    # Arrange
    query = "存在しないキーワード"

    # Act
    result = search_markets(query)

    # Assert
    assert result == []


def test_raises_value_error_when_query_is_empty():
    with pytest.raises(ValueError, match="クエリが空です"):
        search_markets("")


# FAIL: BAD: 曖昧なテスト名
def test_search():
    assert search_markets("x") is not None
```

### コードスメル（Python版）

```python
# FAIL: BAD: 深いネスト
def process(user, market):
    if user:
        if user.is_admin:
            if market:
                if market.is_active:
                    # 処理

# PASS: GOOD: アーリーリターン
def process(user, market):
    if not user:
        return
    if not user.is_admin:
        return
    if not market or not market.is_active:
        return
    # 処理


# FAIL: BAD: マジックナンバー
if retry_count > 3:
    time.sleep(0.5)

# PASS: GOOD: 名前付き定数
MAX_RETRIES = 3
RETRY_DELAY_SEC = 0.5

if retry_count > MAX_RETRIES:
    time.sleep(RETRY_DELAY_SEC)
```

---

**Remember**: コード品質は交渉の余地がない。明確で保守しやすいコードが、迅速な開発と自信を持ったリファクタリングを可能にする。
