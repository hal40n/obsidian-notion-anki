"""
Phase 0: Anki ノートタイプ自動作成スクリプト
==========================================
設計書 v4 に基づき、以下のノートタイプを AnkiConnect 経由で作成する。

  1. SentenceVocab_DE — ドイツ語 例文ベースカード（TTS付き）
  2. SentenceVocab_EN — 英語 例文ベースカード（TTS付き）
  3. TermDefinition   — 資格学習 用語→定義カード

前提条件:
  - Anki デスクトップが起動中
  - AnkiConnect アドオン (2055492159) がインストール済み

使い方:
  python setup_anki_note_types.py          # 全ノートタイプを作成
  python setup_anki_note_types.py --dry-run # 実行内容の確認のみ
"""

import argparse
import sys

from src.anki_client import DEFAULT_URL, anki_request
from src.templates import NOTE_TYPES


def model_exists(name: str) -> bool:
    return name in anki_request("modelNames")


def deck_exists(name: str) -> bool:
    return name in anki_request("deckNames")


def create_note_type(nt: dict, dry_run: bool = False) -> bool:
    """ノートタイプを1つ作成する。"""
    name = nt["name"]

    if model_exists(name):
        print(f"  ⏭️  {name} — 既に存在するためスキップ")
        return False

    if dry_run:
        print(f"  🔍 {name} — 作成予定（dry-run）")
        print(f"      フィールド: {', '.join(nt['fields'])}")
        print(f"      デッキ: {nt['deck']}")
        return True

    anki_request(
        "createModel",
        modelName=name,
        inOrderFields=nt["fields"],
        css=nt["css"],
        cardTemplates=[{"Name": "Card 1", "Front": nt["front"], "Back": nt["back"]}],
    )
    print(f"  ✅ {name} — 作成完了")
    return True


def create_deck(deck_name: str, dry_run: bool = False) -> bool:
    """デッキを作成する（存在しなければ）。"""
    if deck_exists(deck_name):
        print(f"  ⏭️  デッキ「{deck_name}」— 既に存在")
        return False

    if dry_run:
        print(f"  🔍 デッキ「{deck_name}」— 作成予定（dry-run）")
        return True

    anki_request("createDeck", deck=deck_name)
    print(f"  ✅ デッキ「{deck_name}」— 作成完了")
    return True


def add_sample_notes(dry_run: bool = False) -> None:
    """動作確認用のサンプルカードを追加する。"""
    samples = [
        {
            "deckName": "Deutsch",
            "modelName": "SentenceVocab_DE",
            "fields": {
                "Word": "gehen",
                "Sentence": 'Ich <span class="hl">gehe</span> jeden Morgen in den Park, um frische Luft zu atmen.',
                "ExampleTranslation": "私は毎朝、新鮮な空気を吸うために公園へ行く。",
                "Meaning": "行く、歩く（※um ... zu 構文で「～するために行く」）",
                "PartOfSpeech": "Verb (unregelmäßig)",
                "Usage": "gehen + Richtung / gehen + um ... zu + Infinitiv",
                "Source": "Deutsch perfekt - März 2026",
                "Language": "de_DE",
            },
            "tags": ["sample", "Deutsch_perfekt"],
        },
        {
            "deckName": "Deutsch",
            "modelName": "SentenceVocab_DE",
            "fields": {
                "Word": "Entscheidung",
                "Sentence": 'Diese <span class="hl">Entscheidung</span> hat mein Leben komplett verändert.',
                "ExampleTranslation": "この決断が私の人生を完全に変えた。",
                "Meaning": "決断、決定",
                "PartOfSpeech": "Nomen (f.), die Entscheidung, -en",
                "Usage": "eine Entscheidung treffen（決断を下す）",
                "Source": "Deutsch perfekt - März 2026",
                "Language": "de_DE",
            },
            "tags": ["sample", "Deutsch_perfekt"],
        },
        {
            "deckName": "Certifications",
            "modelName": "TermDefinition",
            "fields": {
                "Term": "スループット",
                "Definition": "単位時間あたりに処理できるデータ量。ネットワークの実効速度の指標。",
                "Category": "ネットワーク",
            },
            "tags": ["sample", "応用情報"],
        },
    ]

    if dry_run:
        print(f"\n📝 サンプルカード {len(samples)} 件を追加予定（dry-run）")
        for s in samples:
            print(f"   - [{s['modelName']}] {s['fields'].get('Word') or s['fields'].get('Term')}")
        return

    print("\n📝 サンプルカードを追加中...")
    for s in samples:
        word = s["fields"].get("Word") or s["fields"].get("Term")
        try:
            note_id = anki_request("addNote", note=s)
            print(f"  ✅ {word} (ID: {note_id})")
        except RuntimeError as e:
            if "duplicate" in str(e).lower():
                print(f"  ⏭️  {word} — 既に存在するためスキップ")
            else:
                print(f"  ❌ {word} — エラー: {e}")


def main():
    parser = argparse.ArgumentParser(description="Anki ノートタイプ自動作成（設計書 v4 Phase 0）")
    parser.add_argument("--dry-run", action="store_true", help="実行内容を確認するだけで実際には作成しない")
    parser.add_argument("--no-samples", action="store_true", help="サンプルカードを追加しない")
    args = parser.parse_args()

    print("=" * 56)
    print("  Anki ノートタイプ セットアップ（設計書 v4 Phase 0）")
    print("=" * 56)

    if args.dry_run:
        print("⚠️  dry-run モード: 実際には作成しません\n")

    print("🔌 AnkiConnect 接続確認...")
    try:
        version = anki_request("version")
        print(f"  ✅ AnkiConnect v{version} に接続\n")
    except SystemExit:
        raise
    except Exception as e:
        print(f"  ❌ 接続失敗: {e}")
        sys.exit(1)

    print("📂 デッキ作成...")
    for deck_name in sorted({nt["deck"] for nt in NOTE_TYPES}):
        create_deck(deck_name, dry_run=args.dry_run)

    print("\n📋 ノートタイプ作成...")
    for nt in NOTE_TYPES:
        print(f"\n  [{nt['description']}]")
        create_note_type(nt, dry_run=args.dry_run)

    if not args.no_samples:
        add_sample_notes(dry_run=args.dry_run)

    print("\n" + "=" * 56)
    if args.dry_run:
        print("  dry-run 完了。実行するには --dry-run を外してください。")
    else:
        print("  セットアップ完了！")
        print("  Anki でノートタイプとサンプルカードを確認してください。")
        print(f"\n  確認手順:")
        print(f"    1. Anki メニュー → ツール → ノートタイプの管理")
        print(f"       SentenceVocab_DE / SentenceVocab_EN / TermDefinition があるか確認")
        print(f"    2. 「Deutsch」デッキを開いてサンプルカードを確認")
        print(f"    3. 「Certifications」デッキを開いてサンプルカードを確認")
        print(f"\n  ⚠️  TTS を有効にするには:")
        print(f"    macOS: システム設定 → アクセシビリティ → 読み上げ → ドイツ語音声を追加")
        print(f"    iOS:   設定 → アクセシビリティ → 読み上げコンテンツ → 声 → ドイツ語DL")
    print("=" * 56)


if __name__ == "__main__":
    main()
