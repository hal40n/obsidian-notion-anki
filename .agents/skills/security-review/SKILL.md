---
name: security-review
description: 認証・ユーザー入力・シークレット・APIエンドポイント・決済など機密性の高い機能を実装する際に使用するスキル。セキュリティチェックリストとパターンを網羅する。
---

# セキュリティレビュースキル

すべてのコードがセキュリティのベストプラクティスに従い、潜在的な脆弱性を洗い出すためのスキル。

## 適用タイミング

- 認証・認可を実装するとき
- ユーザー入力やファイルアップロードを扱うとき
- 新しいAPIエンドポイントを作成するとき
- シークレットや認証情報を扱うとき
- 決済機能を実装するとき
- 機密データを保存・送信するとき
- サードパーティAPIと連携するとき

## セキュリティチェックリスト

### 1. シークレット管理

#### NG：絶対にやってはいけない

```typescript
const apiKey = "sk-proj-xxxxx"  // ハードコードされたシークレット
const dbPassword = "password123" // ソースコードに直書き
```

#### OK：必ずこうする

```typescript
const apiKey = process.env.OPENAI_API_KEY
const dbUrl = process.env.DATABASE_URL

// シークレットの存在を検証する
if (!apiKey) {
  throw new Error('OPENAI_API_KEY が設定されていません')
}
```

#### 確認項目

- [ ] APIキー・トークン・パスワードがハードコードされていない
- [ ] すべてのシークレットが環境変数に格納されている
- [ ] `.env.local` が .gitignore に含まれている
- [ ] git履歴にシークレットが含まれていない
- [ ] 本番シークレットはホスティングプラットフォーム（Vercel・Railway）で管理されている

---

### 2. 入力バリデーション

#### ユーザー入力は必ず検証する

```typescript
import { z } from 'zod'

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150)
})

export async function createUser(input: unknown) {
  try {
    const validated = CreateUserSchema.parse(input)
    return await db.users.create(validated)
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, errors: error.errors }
    }
    throw error
  }
}
```

#### Pythonでの入力バリデーション（Pydantic）

```python
from pydantic import BaseModel, EmailStr, constr, conint
from fastapi import HTTPException

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: constr(min_length=1, max_length=100)
    age: conint(ge=0, le=150)

@app.post("/users")
async def create_user(user: CreateUserRequest):
    # FastAPIがPydanticで自動バリデーション
    return await db.create_user(user.dict())
```

#### ファイルアップロードのバリデーション

```typescript
function validateFileUpload(file: File) {
  // サイズチェック（5MB上限）
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    throw new Error('ファイルサイズが大きすぎます（上限5MB）')
  }

  // MIMEタイプチェック
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
  if (!allowedTypes.includes(file.type)) {
    throw new Error('無効なファイル形式です')
  }

  // 拡張子チェック
  const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif']
  const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0]
  if (!extension || !allowedExtensions.includes(extension)) {
    throw new Error('無効な拡張子です')
  }

  return true
}
```

#### 確認項目

- [ ] すべてのユーザー入力がスキーマでバリデーション済み
- [ ] ファイルアップロードが制限されている（サイズ・タイプ・拡張子）
- [ ] ユーザー入力をクエリに直接使用していない
- [ ] ブラックリストではなくホワイトリスト方式でバリデーション
- [ ] エラーメッセージが機密情報を漏らしていない

---

### 3. SQLインジェクション対策

#### NG：SQL文字列を絶対に結合しない

```typescript
// 危険 — SQLインジェクション脆弱性
const query = `SELECT * FROM users WHERE email = '${userEmail}'`
await db.query(query)
```

#### OK：必ずパラメータ化クエリを使う

```typescript
// 安全 — パラメータ化クエリ
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('email', userEmail)

// 生SQLの場合
await db.query(
  'SELECT * FROM users WHERE email = $1',
  [userEmail]
)
```

#### Pythonでの対策（SQLAlchemy）

```python
# NG：f文字列でSQLを組み立てる
query = f"SELECT * FROM users WHERE email = '{email}'"  # 危険

# OK：パラメータバインディングを使う
from sqlalchemy import text

result = db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)

# OK：ORMを使う（最も安全）
user = db.query(User).filter(User.email == email).first()
```

#### 確認項目

- [ ] すべてのDBクエリがパラメータ化されている
- [ ] SQL文字列連結を使っていない
- [ ] ORM・クエリビルダーが正しく使われている
- [ ] Supabaseクエリが適切にサニタイズされている

---

### 4. 認証・認可

#### JWTトークンの取り扱い

```typescript
// NG：localStorageはXSSに脆弱
localStorage.setItem('token', token)

// OK：httpOnly Cookieを使う
res.setHeader('Set-Cookie',
  `token=${token}; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`)
```

#### 認可チェック

```typescript
export async function deleteUser(userId: string, requesterId: string) {
  // 必ず先に認可を確認する
  const requester = await db.users.findUnique({
    where: { id: requesterId }
  })

  if (requester.role !== 'admin') {
    return NextResponse.json(
      { error: '権限がありません' },
      { status: 403 }
    )
  }

  await db.users.delete({ where: { id: userId } })
}
```

#### Pythonでの認可（FastAPI）

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証情報が無効です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    return current_user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, admin = Depends(require_admin)):
    return await db.delete_user(user_id)
```

#### Row Level Security（Supabase）

```sql
-- すべてのテーブルでRLSを有効化する
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- ユーザーは自分のデータのみ参照できる
CREATE POLICY "Users view own data"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- ユーザーは自分のデータのみ更新できる
CREATE POLICY "Users update own data"
  ON users FOR UPDATE
  USING (auth.uid() = id);
```

#### 確認項目

- [ ] トークンをhttpOnly Cookieに保存している（localStorageではない）
- [ ] 機密操作の前に認可チェックがある
- [ ] SupabaseでRow Level Securityが有効
- [ ] ロールベースのアクセス制御が実装されている
- [ ] セッション管理が安全

---

### 5. XSS対策

#### HTMLのサニタイズ

```typescript
import DOMPurify from 'isomorphic-dompurify'

function renderUserContent(html: string) {
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p'],
    ALLOWED_ATTR: []
  })
  return <div dangerouslySetInnerHTML={{ __html: clean }} />
}
```

#### Content Security Policy

```typescript
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
      font-src 'self';
      connect-src 'self' https://api.example.com;
    `.replace(/\s{2,}/g, ' ').trim()
  }
]
```

#### 確認項目

- [ ] ユーザー提供のHTMLがサニタイズされている
- [ ] CSPヘッダーが設定されている
- [ ] バリデーションなしの動的コンテンツレンダリングがない
- [ ] ReactのビルトインXSS保護が活用されている

---

### 6. CSRF対策

#### CSRFトークン

```typescript
import { csrf } from '@/lib/csrf'

export async function POST(request: Request) {
  const token = request.headers.get('X-CSRF-Token')

  if (!csrf.verify(token)) {
    return NextResponse.json(
      { error: '無効なCSRFトークンです' },
      { status: 403 }
    )
  }

  // リクエスト処理
}
```

#### SameSite Cookie

```typescript
res.setHeader('Set-Cookie',
  `session=${sessionId}; HttpOnly; Secure; SameSite=Strict`)
```

#### 確認項目

- [ ] 状態変更を伴う操作にCSRFトークンが使われている
- [ ] すべてのCookieに `SameSite=Strict` が設定されている
- [ ] ダブルサブミットCookieパターンが実装されている

---

### 7. レート制限

#### APIレート制限

```typescript
import rateLimit from 'express-rate-limit'

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分
  max: 100,                  // 15分あたり100リクエスト
  message: 'リクエストが多すぎます'
})

app.use('/api/', limiter)
```

#### コストの高い操作への厳格な制限

```typescript
const searchLimiter = rateLimit({
  windowMs: 60 * 1000, // 1分
  max: 10,             // 1分あたり10リクエスト
  message: '検索リクエストが多すぎます'
})

app.use('/api/search', searchLimiter)
```

#### Pythonでのレート制限（FastAPI + slowapi）

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/search")
@limiter.limit("10/minute")
async def search(request: Request, q: str):
    return await perform_search(q)
```

#### 確認項目

- [ ] すべてのAPIエンドポイントにレート制限がある
- [ ] コストの高い操作にはより厳格な制限がある
- [ ] IPベースのレート制限がある
- [ ] 認証済みユーザーベースのレート制限がある

---

### 8. 機密データの露出防止

#### ログ出力

```typescript
// NG：機密データをログに出力する
console.log('User login:', { email, password })
console.log('Payment:', { cardNumber, cvv })

// OK：機密データをマスクする
console.log('User login:', { email, userId })
console.log('Payment:', { last4: card.last4, userId })
```

#### Pythonでのログ管理

```python
import logging

logger = logging.getLogger(__name__)

# NG
logger.info(f"ログイン: email={email}, password={password}")

# OK
logger.info(f"ログイン: user_id={user_id}, email={email[:3]}***")
```

#### エラーメッセージ

```typescript
// NG：内部情報を公開する
catch (error) {
  return NextResponse.json(
    { error: error.message, stack: error.stack },
    { status: 500 }
  )
}

// OK：ユーザー向けには汎用メッセージにする
catch (error) {
  console.error('内部エラー:', error) // サーバーログにのみ詳細を記録
  return NextResponse.json(
    { error: 'エラーが発生しました。しばらく後でお試しください。' },
    { status: 500 }
  )
}
```

#### 確認項目

- [ ] パスワード・トークン・シークレットがログに含まれていない
- [ ] ユーザー向けエラーメッセージが汎用的
- [ ] 詳細なエラーはサーバーログにのみ記録されている
- [ ] スタックトレースがユーザーに公開されていない

---

### 9. ブロックチェーンセキュリティ（Solana）

#### ウォレット署名の検証

```typescript
import { verify } from '@solana/web3.js'

async function verifyWalletOwnership(
  publicKey: string,
  signature: string,
  message: string
) {
  try {
    const isValid = verify(
      Buffer.from(message),
      Buffer.from(signature, 'base64'),
      Buffer.from(publicKey, 'base64')
    )
    return isValid
  } catch (error) {
    return false
  }
}
```

#### トランザクションの検証

```typescript
async function verifyTransaction(transaction: Transaction) {
  // 送金先を検証する
  if (transaction.to !== expectedRecipient) {
    throw new Error('無効な送金先です')
  }

  // 金額を検証する
  if (transaction.amount > maxAmount) {
    throw new Error('上限金額を超えています')
  }

  // 残高を確認する
  const balance = await getBalance(transaction.from)
  if (balance < transaction.amount) {
    throw new Error('残高が不足しています')
  }

  return true
}
```

#### 確認項目

- [ ] ウォレット署名が検証されている
- [ ] トランザクション詳細がバリデーション済み
- [ ] 送金前に残高チェックがある
- [ ] ブラインドな署名要求をしていない

---

### 10. 依存関係のセキュリティ

#### 定期的なアップデート

```bash
# 脆弱性チェック
npm audit

# 自動修正
npm audit fix

# 依存関係の更新
npm update

# 古いパッケージを確認
npm outdated
```

#### Pythonでの依存関係チェック

```bash
# 脆弱性スキャン
pip install safety
safety check

# 依存関係のアップデート確認
pip list --outdated

# 依存関係の固定（再現性確保）
pip freeze > requirements.txt
```

#### ロックファイル

```bash
# 必ずロックファイルをコミットする
git add package-lock.json

# CI/CDでは npm ci を使う（npm install ではなく）
npm ci
```

#### 確認項目

- [ ] 依存関係が最新
- [ ] 既知の脆弱性がない（npm audit / safety check）
- [ ] ロックファイルがコミットされている
- [ ] GitHubでDependabotが有効化されている
- [ ] 定期的なセキュリティアップデートがある

---

## セキュリティテスト

```typescript
// 認証テスト
test('未認証リクエストを拒否する', async () => {
  const response = await fetch('/api/protected')
  expect(response.status).toBe(401)
})

// 認可テスト
test('管理者権限がないユーザーを拒否する', async () => {
  const response = await fetch('/api/admin', {
    headers: { Authorization: `Bearer ${userToken}` }
  })
  expect(response.status).toBe(403)
})

// 入力バリデーションテスト
test('無効な入力を拒否する', async () => {
  const response = await fetch('/api/users', {
    method: 'POST',
    body: JSON.stringify({ email: 'not-an-email' })
  })
  expect(response.status).toBe(400)
})

// レート制限テスト
test('レート制限を適用する', async () => {
  const requests = Array(101).fill(null).map(() =>
    fetch('/api/endpoint')
  )
  const responses = await Promise.all(requests)
  const tooManyRequests = responses.filter(r => r.status === 429)
  expect(tooManyRequests.length).toBeGreaterThan(0)
})
```

---

## 本番デプロイ前セキュリティチェックリスト

デプロイの前に必ず確認すること：

- [ ] **シークレット**：ハードコードなし、すべて環境変数で管理
- [ ] **入力バリデーション**：すべてのユーザー入力が検証済み
- [ ] **SQLインジェクション**：すべてのクエリがパラメータ化済み
- [ ] **XSS**：ユーザーコンテンツがサニタイズ済み
- [ ] **CSRF**：保護が有効
- [ ] **認証**：トークンの取り扱いが適切
- [ ] **認可**：機密操作前にロールチェックがある
- [ ] **レート制限**：すべてのエンドポイントで有効
- [ ] **HTTPS**：本番環境で強制されている
- [ ] **セキュリティヘッダー**：CSP・X-Frame-Options が設定済み
- [ ] **エラーハンドリング**：エラーに機密データが含まれていない
- [ ] **ログ**：機密データがログに含まれていない
- [ ] **依存関係**：最新かつ脆弱性なし
- [ ] **Row Level Security**：Supabaseで有効化済み
- [ ] **CORS**：適切に設定済み
- [ ] **ファイルアップロード**：バリデーション済み（サイズ・タイプ）
- [ ] **ウォレット署名**：検証済み（ブロックチェーン利用時）

---

**重要：** セキュリティは任意ではない。脆弱性が1つあるだけでプラットフォーム全体が危険にさらされる。迷ったときは、より慎重な選択をすること。
