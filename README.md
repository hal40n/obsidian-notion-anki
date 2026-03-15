# Notion → Anki 語彙学習ツール

NotionとObsidianに保存した語彙データをAnkiフラッシュカードへ自動同期するツール群。

## ワークフロー

```text
【英語・ドイツ語単語】
Notion（直接入力） → Anki

【CS用語・資格学習】
Obsidian（vocab/cert/） → Notion → Anki
```

## セットアップ

### 必要なもの

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Anki（デスクトップ）+ [AnkiConnect](https://ankiweb.net/shared/info/2055492159)アドオン
- Notionインテグレーション

### インストール

```bash
git clone <repo>
cd obsidian-notion-anki
uv sync
```

### 環境変数の設定

`.env` ファイルをプロジェクトルートに作成:

```env
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxx
DEUTSCH_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# English や資格DBを追加する場合:
# ENGLISH_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# CERT_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OBSIDIAN_VAULT_PATH=/path/to/your/vault
```

### config.yaml の設定

```yaml
databases:
  Deutsch: ${DEUTSCH_DATABASE_ID}
  # English: ${ENGLISH_DATABASE_ID}
  # 応用情報技術者: ${CERT_DATABASE_ID}

note_types:
  Deutsch: "SentenceVocab_DE"
  # English: "SentenceVocab_EN"
  # 応用情報技術者: "TermDefinition"

tts_lang:
  SentenceVocab_DE: "de_DE"
  SentenceVocab_EN: "en_US"

obsidian:
  vault_path: ${OBSIDIAN_VAULT_PATH}
  vocab_dirs:
    - "vocab/cert"

anki:
  url: "http://localhost:8765"
```

### Ankiノートタイプの作成

```bash
uv run poe setup-anki
```

---

## 使い方

### Phase 2: Notion → Anki（英語・ドイツ語単語）

NotionのDBに `Anki Status = New` または `Updated` のレコードをAnkiに同期する。

```bash
# 全デッキを同期
uv run poe sync

# 確認のみ（ファイル変更なし）
uv run poe sync-dry

# 特定デッキのみ
uv run poe sync-deck Deutsch
```

### Phase 3: Obsidian → Notion（CS用語・資格）

Obsidianの `vocab/cert/` 配下の未同期ファイルをNotionに登録する。

```bash
# 全ファイルを同期
uv run poe obs2notion

# 確認のみ
uv run poe obs2notion-dry
```

---

## Notion DB の設定

### 言語学習用（Deutsch / English）

| プロパティ名 | 型 |
| --- | --- |
| Word | タイトル |
| Meaning | リッチテキスト |
| Part of Speech | セレクト |
| Example | リッチテキスト |
| Example Translation | リッチテキスト |
| Usage | リッチテキスト |
| Sources | リッチテキスト |
| Language | セレクト |
| Anki Status | セレクト（`New` / `Synced` / `Updated`） |
| Anki Note ID | 数値 |

### 資格学習用（応用情報技術者など）

| プロパティ名 | 型 |
| --- | --- |
| Term | タイトル |
| Definition | リッチテキスト |
| Category | セレクト |
| Anki Status | セレクト（`New` / `Synced` / `Updated`） |
| Anki Note ID | 数値 |

---

## Obsidian ファイル形式（CS用語）

`vocab/cert/スループット.md`

```markdown
---
word: スループット
meaning: 単位時間あたりに処理できるデータ量。
category: ネットワーク
deck: 応用情報技術者
anki_synced: false
---

## スループット

詳細なメモをここに書く。
```

**フィールド一覧:**

| フィールド | 必須 | 説明 |
| --- | --- | --- |
| `word` | ◯ | 用語名 |
| `meaning` | ◯ | 定義・意味 |
| `category` | 推奨 | 分野（例: ネットワーク） |
| `deck` | ◯ | config.yaml の databases キーと一致させる |
| `anki_synced` | 自動 | `false` → 同期後に日時へ自動更新 |

---

## Ankiカードのデザイン

### SentenceVocab（言語学習用）

- **表面**: 例文（対象語を赤字・下線で強調） + TTS自動読み上げ
- **裏面**: 意味・品詞・語法・出典

例文内の `<<gehen>>` マーカーが `<span class="hl">gehen</span>` に変換される。

### TermDefinition（資格学習用）

- **表面**: 用語
- **裏面**: 定義・カテゴリ

---

## TTS（読み上げ）のセットアップ

### macOS

システム設定 → アクセシビリティ → 読み上げ → ドイツ語音声（Anna Enhanced 推奨）を追加

### iOS

設定 → アクセシビリティ → 読み上げコンテンツ → 声 → ドイツ語 → ダウンロード

---

## ファイル構成

```text
.
├── notion_to_anki.py          # Phase 2: Notion → Anki
├── obsidian2notion.py         # Phase 3: Obsidian → Notion
├── setup_anki_note_types.py   # Phase 0: Ankiノートタイプ作成
├── src/
│   ├── config.py              # 設定読み込み
│   ├── models.py              # データモデル
│   ├── obsidian_parser.py     # Obsidianファイルパーサー
│   ├── notion_sync.py         # Notion API操作
│   ├── notion_writer.py       # Notionへの書き込み
│   ├── note_builder.py        # Ankiノート構築
│   ├── anki_client.py         # AnkiConnect クライアント
│   └── templates.py           # Ankiカードテンプレート
├── tests/
├── config.yaml                # 設定（環境変数プレースホルダー）
├── .env                       # シークレット（git管理外）
└── pyproject.toml
```

---

## 開発

```bash
# テスト実行
uv run poe test

# カバレッジ付きテスト（80%以上必須）
uv run poe test-cov

# リント
uv run poe lint

# フォーマット
uv run poe fmt

# 型チェック
uv run poe typecheck
```
