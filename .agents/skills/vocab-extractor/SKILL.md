---
name: vocab-extractor
description: 外国語の文献から未カード化の単語を抽出し、obsidian-notion-anki パイプラインで処理可能な Vault 単語ノートを生成するSkill。現状はドイツ語のみ対応。
origin: project
---

# Vocab Extractor Skill

外国語文献（Web記事・PDF抽出テキスト・Kindle Highlights・貼り付けテキスト）から、まだフラッシュカード化していない単語を抽出し、`{vault_path}/500-reference/vocab/{lang}/{lemma}.md` 形式で書き出すSkill。

下流の Notion 同期・Anki 同期は、本プロジェクト `obsidian-notion-anki` の Python パイプライン（`obsidian2notion.py` → `notion_to_anki.py`）に完全委譲する（このSkillは触らない）。

**Phase 1 のスコープ**：ドイツ語（`lang=de`）のみ対応。プロンプトは `prompts/de/` に分離してあり、後のフェーズで他言語を追加可能な構造。

## 既存 Skill との関係

- [[add-word]]：ユーザーが手で与えた単語を `word/` ディレクトリに登録する Skill
- **vocab-extractor**：文献テキストから単語を**自動抽出**して Vault 側 `vocab/de/` に直接書き出す Skill

両者は補完的。本Skillは Vault → Notion → Anki のパイプラインの最上流を担う。

## 設計原則

1. **既存資産を壊さない**：本プロジェクトの Python スクリプトには触らず、`obsidian2notion.py` の `load_vocab_entry` が期待する frontmatter を厳密に満たすノートだけを生成する
2. **重複の絶対回避**：Vault 内 `{vault_path}/500-reference/vocab/de/` に既存するレンマは新規生成しない（学習者の手間とトークン消費を最小化）
3. **構造化I/O**：プロンプトには JSON 形式で入力し、JSON 形式で受け取る（Phase 3 で TypeScript プラグインに移植しやすくするため）
4. **セキュリティ**：APIキー・トークン類は環境変数のみで扱い、生成ノートやログには絶対に書き込まない。学習者の個人日記（`000-personal/`）など機密性の高いソースは入力に含めない

## 環境変数の前提

本 Skill は実行前に以下が解決されていることを期待する：

- `OBSIDIAN_VAULT_PATH`：Obsidian Vault のルート絶対パス（例：`/Users/shm04/Obsidian`）
- `config.yaml` の `obsidian.vault_path` ／ `obsidian.vocab_dirs` ／ `databases`

`OBSIDIAN_VAULT_PATH` が未設定なら即座に例外を投げ、ユーザーに `.env` での設定方法を提示する。

## 1. 入力の受付

ユーザーから以下のいずれかを受け取る：

- **ファイルパス**：Vault 内 `100-inbox/` 配下の Markdown、`500-reference/reading/de/` 配下のテキスト
- **URL**：Web記事（取得は WebFetch で実施）
- **貼り付けテキスト**：チャット欄に直接貼られた長文
- **Kindle Highlights**：Markdown 形式のハイライト一覧

入力が無い場合、`AskUserQuestion` でソースの種類とパスを問う。

## 2. スコープの確認

`AskUserQuestion` で以下を確認する：

| 項目 | デフォルト | 説明 |
| --- | --- | --- |
| 学習者レベル | 独検2級／B1 相当 | 抽出するCEFRレベルの基準 |
| 抽出上限語数 | 20 | 1回の実行で生成するノート数の上限 |
| 出典タイトル | （AIが自動推定） | 生成ノートの `source` に入る文字列 |
| 抽出方針 | 「学習者レベル以上」 | A1基礎語を除外するか／全未知語を出すか |

これらは Skill 内部で「実行コンテキスト JSON」に集約する（Phase 3 で TypeScript の `ExtractRequest` 型になる、`SPEC.md` 参照）。

## 3. テキスト正規化

入力ソースから本文テキストを取り出す。

- Markdown：frontmatter・コードブロック・HTMLタグを除外
- URL：WebFetch で取得 → HTML を Markdown に変換 → 上記同様に正規化
- PDF：ユーザーが既にテキスト化したものを受け取る前提（PDF直処理は Phase 2）
- 不要な英訳・著者注は除く

## 4. 単語抽出とレンマ化

`prompts/de/extract-and-lemmatize.md` のプロンプトに従い JSON を得る。詳細スキーマは `SPEC.md` 参照。

- レンマは DUDEN 辞書見出し形に揃える（`gegangen` → `gehen`、`Häuser` → `Haus`）
- 名詞は冠詞付きで補完できる形（性別がわかるよう `pos` に `Nomen (f.)` まで書く）
- 1ソースあたり最大40候補まで抽出

## 5. 既存 Vault との突合（重複除外）

`prompts/dedupe-against-vault.md` で指示するロジック：

1. `{vault_path}/500-reference/vocab/de/` を `Glob`／`Read` で走査
2. 各ファイル名（`.md` 除く）をレンマ集合として保持
3. ステップ4で得た `candidates` のうち、既存レンマと一致するものを除外
4. ハイフン違い・大文字小文字違い・ウムラウト揺れは AI が判定（`Hausarbeit` ≠ `Haus`）

除外結果は `skipped` 配列に残し、ユーザー報告用にする。

## 6. メタデータ補完

`prompts/de/fill-metadata.md` に従い、各候補について frontmatter と body_markdown を含む JSON を生成。

**強制ルール**：
- `example` 内の対象語は `<<...>>` で挟む（既存パイプライン `src/note_builder.py` の `convert_markers` が `<span class="hl">` に変換）
- `meaning` は独検対策を意識した自然な日本語訳（直訳調を避ける）
- `pos` 名詞は性・複数形まで書く
- `usage` はコロケーションや構文を1つ以上
- `source` はユーザー指定の出典タイトル（無い場合は空文字）

## 7. ノート書き出し

各 `lemma` について `{vault_path}/500-reference/vocab/de/{lemma}.md` を **新規作成** する：

- 既存ファイルが何らかの理由で存在する場合は **絶対に上書きせず**、スキップして報告する
- ファイル名にスラッシュ・コロン・改行を含まない（`Schloss/Schloß` は Schloss に統一）
- 本文には品詞・意味・例文・活用・関連語のセクションを `gehen.md` 形式（Vault に既存）で出力

## 8. 進捗ダッシュボードへの追記

`{vault_path}/200-project/独検対策/学習ログ/{YYYY-MM-DD}_{ソース略名}.md` を作成し、以下を記録：

- 入力ソースの URL / ファイル名
- 抽出した候補数・新規生成数・スキップ数
- 生成された lemma の箇条書きリスト

このログは Vault 側 `dashboard.md` が Dataview で集計する。

## 9. ユーザーへの最終報告

最後に Claude Code のチャット出力として：

- 新規生成された単語数とリスト（上限20語まで表示）
- スキップした既存語数
- 次のアクション：`uv run poe sync-dry` で同期予定確認、問題なければ `uv run poe sync`

を簡潔に提示する。

## 原則

- 一度に過大な数を抽出しない（学習負荷とトークン消費の両面でコントロールする）
- レンマ判定が曖昧な場合は除外（誤ったカードを作るより漏れる方がマシ）
- 学習者個人の機密情報（日記・添削履歴）はソースに含めない設計とする
- API キーや認証トークンを生成ノートに書き込まない
- 既存の `vocab/de/` ノートは絶対に上書きしない
- 詳細なI/Oスキーマ・エラーハンドリング・セキュリティ要件は `SPEC.md` を参照
