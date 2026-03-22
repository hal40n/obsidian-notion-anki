# Notion → Anki 語彙学習ツール

NotionとObsidianに保存した語彙・用語データをAnkiフラッシュカードへ自動同期するPythonスクリプト。

## ワークフロー

```text
【語学学習（ドイツ語・英語など）】
  Notion DB ─────────────────→ Anki
  （単語・例文を直接入力）      （スクリプトで自動生成）

【IT資格学習】
  Obsidian ──→ Notion DB ──→ Anki
  （用語をまとめ）  （同期）  （自動生成）
```

- **語学学習** — Notionのデータベースに単語・例文・意味を入力し、スクリプトでAnkiに出力する
- **資格学習** — ObsidianのMarkdownで用語をまとめ、スクリプトでNotionに同期してからAnkiに出力する

---

## セットアップ

### 必要なもの

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Anki（デスクトップ）+ [AnkiConnect](https://ankiweb.net/shared/info/2055492159)アドオン（コード: `2055492159`）
- Notionインテグレーション

### 1. インストール

```bash
git clone <repo>
cd obsidian-notion-anki
uv sync
```

### 2. 環境変数の設定（`.env`）

プロジェクトルートに `.env` を作成する。

```env
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxx
DEUTSCH_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 資格DBを追加する場合:
# AP_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OBSIDIAN_VAULT_PATH=/path/to/your/vault
```

DB IDはNotionのURL（`notion.so/<DB名>?v=...` の32桁）から取得する。
作成したインテグレーションを各DBに接続することも忘れずに（DB右上 → 「接続」）。

### 3. `config.yaml` の設定

```yaml
databases:
  Deutsch: ${DEUTSCH_DATABASE_ID}
  # 応用情報技術者: ${AP_DATABASE_ID}

note_types:
  Deutsch: "SentenceVocab_DE"
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

`databases` のキーはデッキ名と一致させる。

### 4. Ankiノートタイプの作成

```bash
uv run poe setup-anki-dry  # 確認
uv run poe setup-anki      # 実行
```

---

## 使い方

### Notion → Anki（語学学習）

Notionに `Anki Status = New / Updated` のエントリをAnkiに同期する。

```bash
uv run poe sync                    # 全デッキを同期
uv run poe sync-dry                # 確認のみ（書き込みなし）
uv run poe sync-deck Deutsch       # 特定デッキのみ
```

同期後、Notionの `Anki Status` が `Synced` に更新され、`Anki Note ID` にカードIDが記録される。
以後、エントリを編集して `Anki Status` を `Updated` にすると次回同期時にAnkiも更新される。

### Obsidian → Notion（資格学習）

Obsidianの未同期ファイルをNotionに登録する。

```bash
uv run poe obs2notion      # 同期
uv run poe obs2notion-dry  # 確認のみ
```

その後 `uv run poe sync` を実行するとAnkiにカードが追加される。

---

## Notion DBのプロパティ

### 語学学習用（Deutsch / English）

| プロパティ名 | 型 | Ankiフィールド |
|---|---|---|
| Word | タイトル | Word |
| Meaning | リッチテキスト | Meaning |
| Part of Speech | セレクト | PartOfSpeech |
| Example | リッチテキスト | Sentence（`<<>>`→HTML変換後） |
| Example Translation | リッチテキスト | ExampleTranslation |
| Usage | リッチテキスト | Usage |
| Sources | リッチテキスト | Source |
| Language | セレクト | TTS言語指定に使用 |
| Anki Status | セレクト（`New` / `Synced` / `Updated`） | 同期管理 |
| Anki Note ID | 数値 | 同期管理 |

例文の `<<単語>>` マーカーが `<span class="hl">単語</span>` に変換され、カード上で赤字・太字・下線で強調される。

### 資格学習用（応用情報技術者など）

| プロパティ名 | 型 | Ankiフィールド |
|---|---|---|
| Term | タイトル | Term |
| Definition | リッチテキスト | Definition |
| Category | セレクト | Category（タグにも使用） |
| Anki Status | セレクト（`New` / `Synced` / `Updated`） | 同期管理 |
| Anki Note ID | 数値 | 同期管理 |

---

## Obsidianファイル形式（資格学習用）

`vocab/cert/スループット.md`

```markdown
---
word: スループット
meaning: 単位時間あたりに処理できるデータ量。ネットワークの実効速度の指標。
category: ネットワーク
deck: 応用情報技術者
anki_synced: false
---

## スループット

詳細なメモをここに書く。
```

| フィールド | 必須 | 説明 |
|---|---|---|
| `word` | ◯ | 用語名 |
| `meaning` | ◯ | 定義・意味 |
| `category` | 推奨 | 分野（例: ネットワーク） |
| `deck` | ◯ | `config.yaml` の `databases` キーと一致させる |
| `anki_synced` | 自動 | `false` → 同期後に日時へ自動更新 |

---

## Ankiカードのデザイン

### SentenceVocab（語学学習用）

- **表面**: 例文（対象語を赤字・下線で強調）+ TTS自動読み上げ
- **裏面**: 意味・品詞・語法・出典

### TermDefinition（資格学習用）

- **表面**: 用語
- **裏面**: 定義・カテゴリ

---

## TTS（読み上げ）のセットアップ

### macOS

システム設定 → アクセシビリティ → 読み上げコンテンツ → システムの声 → ドイツ語音声を追加

### iOS

設定 → アクセシビリティ → 読み上げコンテンツ → 声 → ドイツ語 → ダウンロード

---

## ファイル構成

```text
.
├── notion_to_anki.py          # Notion → Anki 同期
├── obsidian2notion.py         # Obsidian → Notion 同期
├── setup_anki_note_types.py   # Ankiノートタイプ・デッキの初期作成
├── src/
│   ├── config.py              # 設定読み込み（config.yaml + .env）
│   ├── models.py              # データモデル（VocabEntry）
│   ├── obsidian_parser.py     # Obsidianファイルパーサー
│   ├── notion_sync.py         # Notion API操作（取得・更新）
│   ├── notion_writer.py       # NotionDBへの登録・更新
│   ├── note_builder.py        # Ankiノート構築・マーカー変換
│   ├── anki_client.py         # AnkiConnectクライアント
│   ├── templates.py           # Ankiカードテンプレート
│   └── card.css               # カード共通CSS
├── tests/
├── config.yaml                # 設定（環境変数プレースホルダー）
├── .env                       # シークレット（git管理外）
└── pyproject.toml
```

---

## 開発

```bash
uv run poe test       # テスト実行
uv run poe test-cov   # カバレッジ付きテスト（80%以上必須）
uv run poe lint       # リントチェック
uv run poe fmt        # フォーマット
uv run poe typecheck  # 型チェック
uv run poe check      # フォーマット・リント・型チェックを一括実行
```
