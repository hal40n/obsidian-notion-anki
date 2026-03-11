# Obsidian → Notion → Anki 語彙学習ワークフロー設計書 v4

## 変更履歴

| Ver | 変更内容 |
|-----|---------|
| v1 | 初版 |
| v2 | 例文ベースカード設計、Vault構造への適合、`<<word>>`マーカー、ドイツ語対応 |
| v3 | リソースと語彙ノートの分離設計、資格学習カードから例文削除、TTS対応追加、Notion DB→Obsidian表示 |
| v4 | Notion→Obsidian表示を廃止しBases/Dataviewで完結、Notionは純粋なDB+同期ハブに限定、Web Clipper連携を将来像に追加 |

---

## 1. ワークフロー全体像

```plain text
┌─────────────┐     ┌────────────────────────────────────┐
│  リソース     │     │           Obsidian                   │
│ (記事/書籍/  │────▶│  reference/ リソースノート             │
│  Podcast/    │     │       ↕ [[リンク]]                    │
│  YouTube)    │     │  vocab/ 語彙ノート ──── Bases/Dataview で俯瞰
└─────────────┘     └──────────┬─────────────────────────────┘
                               │ obsidian2notion.py
                               ▼
                    ┌──────────────────┐
                    │  Notion（DBハブ）  │  ← 純粋にDBとして使用
                    │  語彙DB (用途別)   │    フィルタ・同期状態管理
                    └────────┬─────────┘
                             │ notion2anki.py
                             ▼
                    ┌──────────────────┐
                    │       Anki        │
                    │  例文カード + TTS  │
                    └──────────────────┘
```

**各ツールの役割分担：**

| ツール | 役割 | やらないこと |
|--------|------|------------|
| **Obsidian** | 知識のホーム。リソースノート、語彙ノートの作成・閲覧・俯瞰 | Ankiとの直接同期 |
| **Notion** | 語彙DBのハブ。同期状態管理、フィルタ・ソート | 語彙の閲覧・学習（それはObsidianとAnkiの仕事） |
| **Anki** | 記憶定着。例文ベースのフラッシュカード + TTS読み上げ | 語彙の管理・編集 |

**設計のポイント：**

- リソースノートと語彙ノートを分離し、`[[リンク]]` で接続
- 1つの語彙ノートに複数のリソースからリンク可能（多対多の関係）
- Obsidianの Backlinks で「この単語はどのリソースに登場したか」を自動確認
- 語彙の俯瞰は Obsidian の Bases / Dataview で完結（Notionには見に行かない）

---

## 2. Obsidian 側の設計

### 2.1 ノート構造：リソースと語彙の分離

```plain text
reference/  →  リソースノート（読書・視聴メモ）
                 本文中で [[gehen]] のように語彙ノートへリンク

vocab/      →  語彙ノート（1単語 = 1ノート）
  de/            ドイツ語
  en/            英語
  cert/          資格学習用語
```

**なぜ分離するか：**

- 同じ単語が複数のリソースに登場する → 語彙ノートは1つ、リソースからのリンクが複数
- Obsidian の Backlinks で「この単語がどのリソースで使われたか」を自動追跡
- 語彙ノート単体で完結するため、Notionへの同期がシンプルになる
- 既存の `words/` ディレクトリの運用思想とも一致する

### 2.2 ディレクトリ構成

```plain text
Vault/
├── _config/
│   └── _templates/
│       ├── vocab-lang.md          # 言語学習用テンプレート（NEW）
│       ├── vocab-cert.md          # 資格学習用テンプレート（NEW）
│       ├── memo.md
│       ├── new_note.md
│       └── ...
├── reference/                     # リソースノート（既存）
│   ├── Deutsch perfekt März 2026.md
│   ├── Domain-Driven Design.md
│   └── ...
├── vocab/                         # 語彙ノート（NEW）
│   ├── de/                        #   ドイツ語
│   │   ├── gehen.md
│   │   ├── Entscheidung.md
│   │   └── ...
│   ├── en/                        #   英語
│   │   ├── nevertheless.md
│   │   └── ...
│   └── cert/                      #   資格用語
│       ├── スループット.md
│       ├── MTBF.md
│       └── ...
├── words/                         # 既存の単語ノート → 段階的に vocab/cert/ へ移行
├── memo/
├── permanent/
├── procedure/
├── project/
└── task/
```

### 2.3 リソースノートでの語彙リンク

リソースノート内で覚えたい単語に出会ったら `[[vocab/de/gehen|gehen]]` でリンクを張る。
語彙ノートがまだ存在しない場合、リンクを張った時点で自動作成のトリガーになる。

```markdown
---
title: "Deutsch perfekt - Ausgabe März 2026"
type: magazine
language: de
tags: [german, B1]
---

# Deutsch perfekt - März 2026

## Notes

Heute habe ich einen Artikel über Alltagsleben in Deutschland gelesen.
Der Autor beschreibt, wie er jeden Morgen in den Park [[vocab/de/gehen|geht]],
um frische Luft zu atmen.

Die wichtigste [[vocab/de/Entscheidung|Entscheidung]] in seinem Leben war,
nach Berlin zu ziehen.

（このように本文中で自然にリンクを張る）
```

**メリット：**

- Obsidian の Graph View で リソース ↔ 語彙 の関連が視覚化される
- Backlinks パネルで「gehen が使われている全リソース」を一覧できる
- リソースノートの本文が語彙の注釈で汚れない

### 2.4 語彙ノートのフォーマット（言語学習用）

テンプレート: `_config/_templates/vocab-lang.md`

```markdown
---
word: "gehen"
meaning: "行く、歩く"
pos: "Verb (unregelmäßig)"
example: "Ich <<gehe>> jeden Morgen in den Park, um frische Luft zu atmen."
example_translation: "私は毎朝、新鮮な空気を吸うために公園へ行く。"
usage: "gehen + Richtung / gehen + um ... zu + Infinitiv"
deck: "Deutsch"
lang: "de"
anki_synced: false
---

## gehen

**意味：** 行く、歩く（※um ... zu 構文で「〜するために行く」）

**品詞：** Verb (unregelmäßig)

**活用：** gehe, gehst, geht / ging / ist gegangen

**例文：**
- Ich ==gehe== jeden Morgen in den Park, um frische Luft zu atmen.
- Er ==ging== gestern ins Kino.

**語法：**
- gehen + 方向 (in den Park, nach Hause, zur Arbeit)
- gehen + um ... zu + 不定詞（～するために行く）
- Es geht mir gut.（私は元気です ← 非人称用法）

**関連語：**
- [[vocab/de/ausgehen|ausgehen]]（外出する）
- [[vocab/de/weggehen|weggehen]]（立ち去る）
```

**設計意図：**

- `frontmatter` にスクリプトがパースする構造化データを集約
- 本文（`---` 以降）は人間が読む用のリッチな学習ノート
- frontmatter の `example:` に `<<gehe>>` マーカー → Ankiカードの表面で赤字化
- 本文の `==gehe==` は Obsidian のハイライト表記（Obsidian上で黄色表示）
- Backlinks に出典が自動表示されるため、Source フィールドは frontmatter に不要
  （スクリプトが Backlinks を読み取って自動補完）

### 2.5 語彙ノートのフォーマット（資格学習用）

テンプレート: `_config/_templates/vocab-cert.md`

```markdown
---
word: "スループット"
meaning: "単位時間あたりに処理できるデータ量。ネットワークの実効速度の指標。"
category: "ネットワーク"
deck: "応用情報技術者"
anki_synced: false
---

## スループット

**定義：**
単位時間あたりに処理できるデータ量。ネットワークやシステムの実効的な処理能力を測る指標。

**補足：**
- 理論上の最大値（帯域幅）とは異なり、実際の通信環境での実測値
- ボトルネックとなる区間によってスループットが制限される
```

**v2からの変更点：**

- `example:` と `usage:` を削除（資格学習では不要）
- `category:` を追加（分野別管理）
- シンプルな用語→定義のカードに特化

### 2.6 frontmatter フィールド一覧

| フィールド | 言語学習 | 資格学習 | 説明 |
|-----------|---------|---------|------|
| `word` | ◯ 必須 | ◯ 必須 | 単語・用語 |
| `meaning` | ◯ 必須 | ◯ 必須 | 意味・定義 |
| `pos` | ◯ 推奨 | — | 品詞 |
| `example` | ◯ 推奨 | — | 例文（`<<word>>` マーカー付き） |
| `example_translation` | ◯ 推奨 | — | 例文の日本語訳 |
| `usage` | △ 任意 | — | 語法・コロケーション |
| `category` | — | ◯ 推奨 | 分野カテゴリ |
| `deck` | ◯ 必須 | ◯ 必須 | Ankiデッキ名 / Notion DB振り分け |
| `lang` | ◯ 推奨 | — | 言語コード（de, en）→ TTS言語指定に使用 |
| `anki_synced` | 自動 | 自動 | `false` / 同期日時 |

---

## 3. Notion 側の設計

### 3.1 DB 構成

```plain text
📚 Language Learning/
├── 🇩🇪 Deutsch Vocabulary
├── 🇬🇧 English Vocabulary
└── ...

📝 Certifications/
├── 応用情報技術者
├── PL-900
└── ...
```

### 3.2 言語学習用 DB プロパティ

| プロパティ名 | 型 | Ankiフィールド |
|---|---|---|
| Word | Title | Word |
| Meaning | Rich text | Meaning |
| Part of Speech | Select | PartOfSpeech |
| Example | Rich text | Sentence（`<<>>`→HTML変換後） |
| Example Translation | Rich text | ExampleTranslation |
| Usage | Rich text | Usage |
| Sources | Rich text | Source（Backlinksから自動取得） |
| Language | Select | → TTS言語指定に使用 |
| Anki Status | Select (`New`/`Synced`/`Updated`) | 同期管理 |
| Anki Note ID | Number | 同期管理 |
| Created | Created time | — |
| Last Edited | Last edited time | 差分同期用 |

### 3.3 資格学習用 DB プロパティ

| プロパティ名 | 型 | Ankiフィールド |
|---|---|---|
| Term | Title | Term |
| Definition | Rich text | Definition |
| Category | Select | Category（タグにも使用） |
| Anki Status | Select (`New`/`Synced`/`Updated`) | 同期管理 |
| Anki Note ID | Number | 同期管理 |
| Created | Created time | — |
| Last Edited | Last edited time | 差分同期用 |

### 3.4 推奨ビュー

**言語学習用：**

- All (Table) / Unsynced / By Source / By POS / Recently Added (Gallery)

**資格学習用：**

- All (Table) / Unsynced / By Category (Board)

---

## 4. Anki 側の設計

### 4.1 ノートタイプ①：SentenceVocab（言語学習用）

**コンセプト：** 例文を表面に表示し、対象語を赤字強調。
裏面で意味・語法を確認。TTS で例文を読み上げ。

**フィールド：**

| フィールド名 | 内容 |
|---|---|
| Word | 単語（検索・管理用） |
| Sentence | 例文HTML（`<span class="hl">gehe</span>` 形式） |
| ExampleTranslation | 例文の日本語訳 |
| Meaning | 意味・訳 |
| PartOfSpeech | 品詞 |
| Usage | 語法・コロケーション |
| Source | 出典（リソース名） |
| Language | 言語コード（de, en） |

**カードテンプレート（表面）：**

```html
<div class="card front">
  {{tts de_DE:Sentence}}
  <div class="sentence">{{Sentence}}</div>
  <div class="hint">強調された語の意味と語法は？</div>
</div>
```

**カードテンプレート（裏面）：**

```html
<div class="card back">
  <div class="sentence">{{Sentence}}</div>
  {{#ExampleTranslation}}
  <div class="translation">{{ExampleTranslation}}</div>
  {{/ExampleTranslation}}
  <hr>
  <div class="word-header">{{Word}}</div>
  {{#PartOfSpeech}}
  <div class="pos">〔{{PartOfSpeech}}〕</div>
  {{/PartOfSpeech}}
  <div class="meaning">{{Meaning}}</div>
  {{#Usage}}
  <div class="usage">📝 {{Usage}}</div>
  {{/Usage}}
  {{#Source}}
  <div class="source">📖 {{Source}}</div>
  {{/Source}}
</div>
```

**TTS について：**

- `{{tts de_DE:Sentence}}` はAnki標準のTTSタグ
- macOS / iOS のOS組み込み音声を自動的に使用
- macOS: システム設定 → アクセシビリティ → 読み上げ でドイツ語音声を追加
- iOS: 設定 → アクセシビリティ → 読み上げコンテンツ → 声 → ドイツ語の音声をDL
- 言語コードの例: `de_DE`（ドイツ語）, `en_US`（英語）, `ja_JP`（日本語）
- スピード調整: `{{tts de_DE speed=0.8:Sentence}}`
- 複数デバイス対応: `{{tts de_DE voices=Apple_Anna,Microsoft_Katja:Sentence}}`

**HTMLハイライト内のTTS読み上げ：**
TTS は HTML タグを無視してテキストだけ読み上げるため、
`<span class="hl">gehe</span>` は正常に "gehe" として発音される。

**注意：TTS タグの言語コードはデッキ固定ではなくカード単位で制御したい場合：**
Language フィールドに `de_DE` を格納し、JavaScript で動的にTTS タグを生成する方法もあるが、
Anki の TTS は Mustache テンプレートでのみ動作するため、
言語ごとにカードタイプを分ける（SentenceVocab_DE, SentenceVocab_EN）か、
config.yaml の `note_types` マッピングで制御するのが安全。

→ **推奨：`note_types` でデッキごとにテンプレートを分ける**

```yaml
note_types:
  Deutsch: "SentenceVocab_DE"    # {{tts de_DE:Sentence}}
  English: "SentenceVocab_EN"    # {{tts en_US:Sentence}}
```

### 4.2 ノートタイプ②：TermDefinition（資格学習用）

**コンセプト：** 用語を表面、定義を裏面。シンプルな暗記カード。
例文なし、TTSなし。

**フィールド：**

| フィールド名 | 内容 |
|---|---|
| Term | 用語 |
| Definition | 定義・説明 |
| Category | 分野カテゴリ |

**カードテンプレート（表面）：**

```html
<div class="card front">
  <div class="term">{{Term}}</div>
</div>
```

**カードテンプレート（裏面）：**

```html
<div class="card back">
  <div class="term">{{Term}}</div>
  <hr>
  <div class="definition">{{Definition}}</div>
  {{#Category}}
  <div class="category">📁 {{Category}}</div>
  {{/Category}}
</div>
```

### 4.3 CSS（共通）

```css
.card {
  font-family: "Noto Sans JP", "Noto Sans", sans-serif;
  font-size: 18px;
  text-align: left;
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  line-height: 1.7;
}

/* 例文中の対象語: 赤字・太字・下線 */
.hl {
  color: #e53e3e;
  font-weight: bold;
  text-decoration: underline;
}

.sentence { font-size: 20px; margin-bottom: 12px; }
.hint { font-size: 13px; color: #999; margin-top: 20px; }
.word-header { font-size: 22px; font-weight: bold; margin-bottom: 4px; }
.pos { font-size: 14px; color: #718096; margin-bottom: 8px; }
.meaning { font-size: 18px; margin-bottom: 12px; }

.usage {
  font-size: 14px;
  color: #4a5568;
  background: #f7fafc;
  padding: 8px 12px;
  border-left: 3px solid #4299e1;
  margin-bottom: 8px;
}

.source { font-size: 12px; color: #a0aec0; margin-top: 16px; }
.term { font-size: 22px; font-weight: bold; text-align: center; }
.definition { font-size: 18px; }
.category { font-size: 12px; color: #a0aec0; margin-top: 16px; }

/* ナイトモード */
.nightMode .card { background: #1a202c; color: #e2e8f0; }
.nightMode .hl { color: #fc8181; }
.nightMode .usage { background: #2d3748; border-left-color: #63b3ed; color: #cbd5e0; }
```

### 4.4 表示例（言語学習カード）

**表面（TTS がドイツ語で例文を読み上げ）：**

```plain text
🔊 (自動再生)

Ich gehe jeden Morgen in den Park, um frische Luft zu atmen.
    ^^^^
   （赤字・太字・下線）

強調された語の意味と語法は？
```

**裏面：**

```plain text
Ich gehe jeden Morgen in den Park, um frische Luft zu atmen.
私は毎朝、新鮮な空気を吸うために公園へ行く。

───────────────────────────

gehen
〔Verb (unregelmäßig)〕

行く、歩く（※um ... zu 構文で「～するために行く」）

📝 gehen + Richtung / gehen + um ... zu + Infinitiv

📖 Deutsch perfekt - Ausgabe März 2026
```

---

## 5. Obsidian での語彙俯瞰（Bases / Dataview）

Notion には語彙の閲覧目的ではアクセスしない。
vocab/ フォルダの frontmatter を Obsidian のネイティブ機能で俯瞰する。

### 5.1 方法 A：Bases（コアプラグイン・推奨）

Obsidian の Bases プラグインで `vocab/de/` 等をテーブル / カード表示する。

- frontmatter の `word`, `meaning`, `pos`, `deck`, `anki_synced` がカラムとして表示
- フィルタ: `anki_synced = false` で未同期の語彙だけ抽出
- グループ: `pos` で品詞別にまとめる
- プラグイン依存が少なく、Obsidian ネイティブで安定

**設定例：**

- 新規 Base を作成 → Source に `vocab/de` フォルダを指定
- 表示カラム: word, meaning, pos, usage, anki_synced
- ルール: `Where [file] [is in folder] [vocab/de]`

### 5.2 方法 B：Dataview クエリ

Bases が使いにくい場合や、より柔軟なクエリが必要な場合に使用。

**ドイツ語 語彙一覧：**

```dataview
TABLE meaning AS "意味", pos AS "品詞", usage AS "語法", anki_synced AS "同期"
FROM "vocab/de"
SORT file.name ASC
```

**未同期の語彙（全言語）：**

```dataview
TABLE meaning AS "意味", deck AS "デッキ", file.folder AS "分類"
FROM "vocab"
WHERE anki_synced = false
SORT file.ctime DESC
```

**資格用語 カテゴリ別：**

```dataview
TABLE meaning AS "定義", category AS "分野"
FROM "vocab/cert"
GROUP BY category
```

**最近追加した語彙 TOP 20：**

```dataview
TABLE meaning AS "意味", deck AS "デッキ"
FROM "vocab"
SORT file.ctime DESC
LIMIT 20
```

### 5.3 ダッシュボードノート（任意）

`vocab/_dashboard.md` として語彙学習の全体像を1ページにまとめることも可能：

```markdown
# 語彙ダッシュボード

## 統計
`$= dv.pages('"vocab/de"').length` ドイツ語
`$= dv.pages('"vocab/en"').length` 英語
`$= dv.pages('"vocab/cert"').length` 資格用語
`$= dv.pages('"vocab"').where(p => p.anki_synced == false).length` 未同期

## 未同期の語彙
（上記の Dataview クエリを埋め込み）

## 最近追加
（上記の Dataview クエリを埋め込み）
```

---

## 6. スクリプト構成

### 6.1 アーキテクチャ

```plain text
scripts/
├── .env                        # シークレット（git管理外）
├── config.yaml                 # 設定（パス、DBマッピング等）
├── models.py                   # VocabEntry データモデル
├── obsidian_parser.py          # frontmatter パーサー + <<word>> 変換
├── obsidian2notion.py          # Obsidian vocab/ → Notion DB
├── notion2anki.py              # Notion DB → AnkiConnect
├── migrate_words.py            # 既存 words/ → vocab/cert/ 移行
├── sync_all.py                 # 一括実行ランナー
└── requirements.txt
```

### 6.2 .env（シークレット管理）

```env
# Notion Integration Token
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxx

# 必要に応じて追加
# CLAUDE_API_KEY=sk-ant-xxxxxxxx
```

### 6.3 config.yaml（設定）

```yaml
databases:
  Deutsch: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  English: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  応用情報技術者: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

note_types:
  Deutsch: "SentenceVocab_DE"
  English: "SentenceVocab_EN"
  応用情報技術者: "TermDefinition"

tts_lang:
  SentenceVocab_DE: "de_DE"
  SentenceVocab_EN: "en_US"

obsidian:
  vault_path: "/path/to/your/vault"
  vocab_dirs:
    - "vocab/de"
    - "vocab/en"
    - "vocab/cert"

anki:
  url: "http://localhost:8765"
```

### 6.4 obsidian2notion.py — 処理フロー

```plain text
1. config の vocab_dirs 内の .md ファイルをスキャン
2. 各ファイルの frontmatter を読み取り
3. anki_synced が false のエントリを抽出
4. deck → databases マッピングで対象Notion DB を決定
5. Notion API でページ作成
   - Word/Term → Title
   - meaning, pos, example, usage, category → Rich text / Select
   - Sources → Obsidian の Backlinks を取得して自動入力
     （vault_path から backlinks を解析、またはユーザーが手動記入）
   - Anki Status → "New"
6. 成功後、frontmatter の anki_synced を日時に更新
7. 重複チェック: Word (Title) で既存エントリがあれば
   - 内容が変わっていれば Anki Status を "Updated" に
   - 変わっていなければスキップ
```

**Backlinks の取得方法：**

```python
import os, re

def get_backlinks(vault_path: str, target_note: str) -> list[str]:
    """
    Vault内を検索し、target_note へのリンクを含むファイル名を返す。
    例: target_note="vocab/de/gehen" → "gehen" へのリンクを持つノートを探す
    """
    backlinks = []
    link_patterns = [
        re.compile(rf'\[\[{re.escape(target_note)}(\|[^\]]+)?\]\]'),
        re.compile(rf'\[\[{re.escape(os.path.basename(target_note))}(\|[^\]]+)?\]\]'),
    ]
    for root, _, files in os.walk(vault_path):
        for f in files:
            if not f.endswith('.md'):
                continue
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as fh:
                content = fh.read()
            for pattern in link_patterns:
                if pattern.search(content):
                    backlinks.append(f.replace('.md', ''))
                    break
    return backlinks
```

### 6.5 notion2anki.py — ノートタイプ別分岐

```python
def create_anki_note(entry: dict, deck: str, config: dict) -> dict:
    note_type = config["note_types"][deck]

    if note_type.startswith("SentenceVocab"):
        sentence_html = convert_markers(entry["example"])  # <<word>> → <span class="hl">
        return {
            "deckName": deck,
            "modelName": note_type,
            "fields": {
                "Word":         entry["word"],
                "Sentence":     sentence_html,
                "Meaning":      entry["meaning"],
                "PartOfSpeech": entry.get("pos", ""),
                "Usage":        entry.get("usage", ""),
                "Source":       ", ".join(entry.get("sources", [])),
                "Language":     entry.get("lang", ""),
            },
            "tags": [s.replace(" ", "_") for s in entry.get("sources", [])]
        }

    elif note_type == "TermDefinition":
        return {
            "deckName": deck,
            "modelName": "TermDefinition",
            "fields": {
                "Term":       entry["word"],
                "Definition": entry["meaning"],
                "Category":   entry.get("category", ""),
            },
            "tags": [entry.get("category", "").replace(" ", "_")]
        }
```

---

## 7. 運用フロー

### 日常サイクル

```plain text
Step 1: リソースを消費 → reference/ にノート作成
        覚えたい単語に出会ったら [[vocab/de/gehen|gehen]] でリンク

Step 2: vocab/de/gehen.md を作成（テンプレートから）
        frontmatter に word, meaning, example, usage, deck を記入

Step 3: python obsidian2notion.py
        → vocab/ の未同期ノートを Notion DB に登録

Step 4: Notion で確認・加筆修正（任意）
        → 修正した場合 Anki Status を "Updated" に

Step 5: python notion2anki.py
        → Anki にカード追加/更新（TTS付き）

Step 6: Anki で学習
        → 例文が読み上げられ、赤字の語の意味と語法を回答
```

### ショートカット（Step 3 + 5 一括）

```bash
python sync_all.py
```

---

## 8. 既存 words/ からの移行

### Phase 4 で実行

```plain text
1. words/ の .md を走査
2. ファイル名 → word（用語名）
3. 本文をパース → meaning, category を抽出
4. vocab/cert/ に新フォーマットの .md を生成
   (frontmatter: word, meaning, category, deck, anki_synced: false)
5. obsidian2notion.py → notion2anki.py で Notion + Anki に反映
6. words/ はアーカイブ化（_archive/words/ 等に移動）
```

---

## 9. 実装の優先順位

| Phase | タスク | 成果 |
|-------|--------|------|
| **0** | Anki ノートタイプ作成（SentenceVocab_DE + TermDefinition） | 受け皿完成 |
| **1** | Notion DB 作成（Deutsch Vocabulary） | Notion にDB完成 |
| **2** | notion2anki.py | **手動入力 → Anki同期が即可能** |
| **3** | obsidian2notion.py + obsidian_parser.py | Obsidian → Notion 自動化 |
| **4** | Bases / Dataview で vocab/ を俯瞰表示 | Obsidian内で語彙管理が完結 |
| **5** | migrate_words.py（既存 words/ → vocab/cert/） | 既存資産を統合 |
| **6** | 資格学習用 DB + TermDefinition 対応 | 横展開 |
| **7** | TTS 音声の最適化（速度調整、音声選択） | 学習体験の向上 |
| **8** | sync_all.py + 自動化（cron / Shortcuts） | 完全自動化 |

---

## 10. 注意事項・制約

### Notion API

- Rate limit: 3 requests/second
- Rich text プロパティ上限: 2000文字
- 各DBにIntegration の接続許可が必要

### AnkiConnect

- Anki デスクトップ起動必須（コード: 2055492159）
- HTML をフィールドに直接渡せる
- TTS タグは HTML タグを無視してテキストのみ読み上げ

### TTS 音声のセットアップ

- **macOS:** システム設定 → アクセシビリティ → 読み上げ → ドイツ語音声を追加
  （Enhanced 版を推奨。Anna (Enhanced) 等）
- **iOS:** 設定 → アクセシビリティ → 読み上げコンテンツ → 声 → ドイツ語 → DL
  （Enhanced 版の方が自然な発音）
- Siri の声は Apple 専用アプリ限定のため、Anki では使用不可

### `<<word>>` マーカー

- 活用形も `<<活用形>>` で囲んでOK
- 1例文1マーカーが原則
- マーカー未設定時は word:: の値で自動検索（フォールバック）

---

## 11. 将来の拡張案

### 近い将来

- **Claude API 自動補完**: word:: だけ入力 → meaning, example, usage を自動生成
- **Cloze deletion**: `<<gehe>>` → `{{c1::gehe}}` への変換で穴埋めカード対応
- **逆引きカード**: Meaning → Word のカードタイプ追加

### Web Clipper → 自動語彙カード生成（目標像）

```plain text
Web ブラウザ上でテキストをハイライト
      │
      ▼
Obsidian Web Clipper でクリップ
      │
      ▼  ハイライト部分から語彙を検出
reference/ にリソースノート自動作成
  + [[vocab/de/gehen|gehen]] リンクを自動挿入
      │
      ▼  vocab/ に語彙ノートが未存在なら自動作成
vocab/de/gehen.md を生成
  (Claude API で meaning, example, usage を自動補完)
      │
      ▼  既存の同期パイプラインが自動処理
obsidian2notion.py → notion2anki.py
      │
      ▼
Anki に例文カード追加（TTS付き）
```

**実現に必要な要素：**

- Obsidian Web Clipper のハイライト→frontmatter変換
- Templaterプラグイン or カスタムスクリプトで vocab/ に語彙ノートを自動生成
- Claude API で意味・例文・語法の自動生成（language 検出含む）
- sync_all.py の自動実行（ファイル変更を検知してトリガー）

### さらに将来

- **画像対応**: Notion DB に画像URL → Ankiカードにイメージ
- **進捗ダッシュボード**: AnkiConnect API で復習統計取得 → Obsidian ダッシュボードに表示
- **Obsidian Dataview 自動集計**: 語彙数の推移グラフ、カテゴリ別分布
