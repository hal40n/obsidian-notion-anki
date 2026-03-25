---
name: add-word
description: word/ ディレクトリへの単語ファイル作成。改行区切りで単語を受け取り、Notion DB 登録用の .md ファイルを一括生成する。
origin: project
---

# word/ への単語ファイル作成

## 発火条件

- ユーザーが単語（ドイツ語・英語）を改行区切りや箇条書きで提示し、「wordに追加して」「登録して」「ファイルを作って」などと依頼したとき

## 出力先

プロジェクトルートの `word/` ディレクトリ。

- ファイル名: `<word>.md`（例: `gehen.md`, `singen.md`）
- 1単語 = 1ファイル
- 既に同名ファイルが存在する場合はユーザーに確認してから上書き

## ファイルフォーマット

```markdown
---
word: <単語>
meaning: <意味（日本語）>
deck: <デッキ名>
pos: <品詞>
example: <例文（ハイライトしたい語を <<語>> で囲む）>
example_translation: <例文の日本語訳>
usage: <語法・コロケーション>
lang: <言語コード>
---
```

### YAML の注意事項

フィールドの値に `: `（コロン+スペース）が含まれる場合、YAML がキー区切りと誤解するためダブルクォートで囲むこと。

```yaml
# NG: pos フィールドにコロンが含まれている
pos: Verb (unregelmäßig: geht / ging / gegangen)

# OK: ダブルクォートで囲む
pos: "Verb (unregelmäßig: geht / ging / gegangen)"
```

### フィールド仕様

| フィールド | 必須 | 説明 |
|---|---|---|
| `word` | ◯ | 単語（辞書見出し形式。ドイツ語は不定詞 / 主格） |
| `meaning` | ◯ | 意味（日本語）。複数ある場合は「；」区切り |
| `deck` | ◯ | `config.yaml` の `databases` キーと完全一致させる |
| `pos` | 推奨 | 品詞（下記の標準値から選択） |
| `example` | ◯ | 例文。ハイライトしたい語を `<<語>>` で囲む |
| `example_translation` | ◯ | 例文の日本語訳 |
| `usage` | 任意 | 語法・格支配・コロケーション（例: `gehen + Richtung`） |
| `lang` | 推奨 | 言語コード（`de` / `en`） |

### `pos` の標準値

Notion の Select プロパティと一致させること。活用・格変化などの詳細は `usage` フィールドに記載する。

| 値 | 品詞 |
|---|---|
| `Verb` | 動詞（分離動詞・不規則動詞含む） |
| `Substantiv` | 名詞 |
| `Adjektiv` | 形容詞 |
| `Adverb` | 副詞 |
| `Präposition` | 前置詞 |
| `Konjunktion` | 接続詞 |
| `Pronomen` | 代名詞 |
| `Artikel` | 冠詞 |
| `Redewendung` | 慣用表現・成句 |
| `Partikel` | 小詞（ja, doch, denn など） |

上記にない品詞が必要な場合はここに追加してください。

### `usage` フィールドの使い方

活用・格支配・分離情報などを記載する。

```yaml
# 動詞の例
usage: "unregelmäßig: geht / ging / gegangen; gehen + Richtungsangabe"

# 分離動詞の例
usage: "trennbar; steht auf / stand auf / aufgestanden; aufstehen + Zeitangabe"

# 名詞の例（性・複数形）
usage: "das Haus, -̈er（中性・複数: Häuser）"

# 前置詞の例（格支配）
usage: "mit + Dativ"
```

### `deck` の値

現在 `config.yaml` に定義されているデッキ名:

- `Deutsch` — ドイツ語単語
- `English` — 英語単語（追加済みの場合）

ユーザーが言語を指定しない場合は `Deutsch` をデフォルトとする。

### `<<>>` マーカーについて

例文でユーザーが提示した単語は `<<語>>` で囲む。スクリプトが自動的に Anki の HTML ハイライト（赤字・太字・下線）に変換する。

```plain text
例: Ich <<gehe>> jeden Morgen in den Park.
→ Anki: Ich <span class="hl">gehe</span> jeden Morgen in den Park.
```

- 活用形・変化形でハイライトする（辞書形ではなく文中の実際の形）
- **分離動詞は前綴りと動詞幹を別々にマーカーで囲む**

```plain text
例（aufstehen）: Er <<steht>> jeden Morgen um sechs Uhr <<auf>>.
→ Anki: Er <span class="hl">steht</span> jeden Morgen um sechs Uhr <span class="hl">auf</span>.
```

### exampleについて

例文として暗記をするため本項目は必須とする。

使用する例文はニュースサイトや論文など、実際で使用されているものとすること。

ただし、一文は長くせず、短文とする。

### example_translationについて

exampleの日本語訳を記載する。

ニュースサイトや論文などから引用した場合は、訳文の末尾に出典を明記すること。

```plain text
例: 彼は毎朝6時に起き上がる。（出典: Deutsche Welle）
```

## 作成例

**入力（ユーザーから）:**

```plain text
gehen
singen
```

**出力（`word/gehen.md`）:**

```markdown
---
word: gehen
meaning: 行く；（物事が）うまくいく
deck: Deutsch
pos: Verb
example: Ich <<gehe>> jeden Morgen in den Park.
example_translation: 私は毎朝公園へ歩いて行く。
usage: "unregelmäßig: geht / ging / gegangen; gehen + Richtungsangabe"
lang: de
---
```

**出力（`word/singen.md`）:**

```markdown
---
word: singen
meaning: 歌う
deck: Deutsch
pos: Verb
example: Sie <<singt>> jeden Abend ein Lied.
example_translation: 彼女は毎晩歌を一曲歌う。
usage: "unregelmäßig: singt / sang / gesungen; singen + Akkusativ"
lang: de
---
```

**出力（`word/aufstehen.md`）— 分離動詞の例:**

```markdown
---
word: aufstehen
meaning: 起き上がる；立ち上がる
deck: Deutsch
pos: Verb
example: Er <<steht>> jeden Morgen um sechs Uhr <<auf>>.
example_translation: 彼は毎朝6時に起き上がる。
usage: "trennbar; steht auf / stand auf / aufgestanden; aufstehen + Zeitangabe"
lang: de
---
```

## 実行フロー

ファイル作成後、以下を **自動で順番に実行する**。ユーザーへの確認は不要。

### Step 1: ファイル作成

`word/<word>.md` を生成し、作成件数とファイル名一覧を報告する。

### Step 2: Notion DB へ登録・ファイル削除

```bash
uv run poe word-to-notion
```

登録成功したファイルは **スクリプトが自動削除する**。重複・エラーのファイルは残る。
登録結果（登録数・エラー数）を報告する。

### Step 3: Anki へ同期

```bash
uv run poe sync
```

同期結果（追加数・エラー数）を報告する。

### エラー時の対応

- `word-to-notion` で重複エラーが出た場合: 該当単語をユーザーに報告し、Step 3 は続行する
- `word-to-notion` または `sync` でそれ以外のエラーが出た場合: エラー内容を報告してユーザーに判断を委ねる
