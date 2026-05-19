# Prompt: 既存 Vault との重複除外（言語非依存）

入力された `candidates` のうち、すでに Vault 内の単語ノートとして存在するものを除外する。

## 入力

```json
{
  "candidates": [
    { "lemma": "Entscheidung", "...": "..." },
    { "lemma": "gehen", "...": "..." }
  ],
  "existing_lemmas": [
    "gehen",
    "Haus",
    "sprechen"
  ]
}
```

- `existing_lemmas` ：`{vault_root}/500-reference/vocab/{lang}/` を走査して得た既存ファイル名（拡張子なし）の配列

## 判定ルール

各 candidate について：

1. **完全一致**：`candidate.lemma === existing_lemma` の場合は除外（大文字小文字の差は考慮するが、両方独語名詞は元々大文字なので原則尊重）
2. **大文字小文字違いのみ**：除外（`entscheidung` vs `Entscheidung`）
3. **ウムラウト・ß の表記揺れ**：除外（`Strasse` ≡ `Straße`、`ueber` ≡ `über`）
4. **複合語の部分一致は除外しない**：`Hausarbeit` は `Haus` と別物として残す
5. **ハイフン違いは同一とみなす**：`Self-Service` ≡ `Selfservice`（言語非依存）

## 出力

```json
{
  "filtered_candidates": [
    { "lemma": "Entscheidung", "...": "..." }
  ],
  "skipped": [
    {
      "lemma": "gehen",
      "matched_existing": "gehen",
      "reason": "exact_match"
    }
  ]
}
```

- `filtered_candidates`：重複でなかったもの（元の構造を保持）
- `skipped`：除外された候補と、その理由（`exact_match` / `case_insensitive_match` / `umlaut_normalization` / `hyphen_normalization`）

## 禁則

- 曖昧な部分一致での除外は禁止（学習機会を不当に奪う）
- 既存ノートのファイル名以外を判定材料にしない（本文内容や Anki デッキの内容は参照しない）
- candidate の構造を変えない（pos/cefr 等のキーを失わせない）
