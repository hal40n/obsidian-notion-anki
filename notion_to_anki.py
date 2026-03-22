"""
Notion → Anki 同期スクリプト
=====================================
Notion DB から Anki Status = "New" or "Updated" のエントリを取得し、
AnkiConnect 経由で Anki にカードを追加/更新する。

前提条件:
  - .env に NOTION_API_KEY を設定済み
  - config.yaml に databases, note_types を設定済み
  - Anki デスクトップが起動中 & AnkiConnect 有効
  - ノートタイプ作成済み

使い方:
  python notion_to_anki.py              # 全DBを同期
  python notion_to_anki.py --dry-run    # 確認のみ
  python notion_to_anki.py --deck Deutsch  # 特定デッキのみ
"""

import argparse
import sys
import time

from notion_client import Client as NotionClient

from src.anki_client import anki_request
from src.config import load_config
from src.note_builder import build_anki_note
from src.notion_sync import fetch_entries, update_notion_page


def sync_deck(
    notion: NotionClient,
    anki_url: str,
    deck: str,
    db_id: str,
    config: dict,
    dry_run: bool = False,
) -> dict:
    """1つのデッキ（Notion DB）を Anki に同期する。

    Args:
        notion: Notion クライアントインスタンス。
        anki_url: AnkiConnect のエンドポイント URL。
        deck: デッキ名（config の databases キーと一致）。
        db_id: Notion データベース ID。
        config: アプリケーション設定辞書。
        dry_run: True の場合、Anki / Notion への書き込みを行わない。

    Returns:
        同期結果の統計辞書（added / updated / skipped / errors）。
    """
    stats = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}
    print(f"\n📖 {deck} (DB: {db_id[:8]}...)")

    entries = fetch_entries(notion, db_id, deck, config)
    if not entries:
        print("  ⏭️  同期対象のエントリがありません（Anki Status = New/Updated が0件）")
        return stats

    print(f"  📥 {len(entries)} 件のエントリを取得")

    for entry in entries:
        word = entry.get("word", "(unknown)")
        status = entry["anki_status"]
        note_id = entry.get("anki_note_id")

        try:
            note = build_anki_note(entry, deck, config)

            if status == "New":
                if dry_run:
                    print(f"  🔍 [追加予定] {word}")
                    stats["added"] += 1
                    continue
                new_note_id = anki_request("addNote", url=anki_url, note=note)
                update_notion_page(notion, entry["page_id"], new_note_id)
                print(f"  ✅ [追加] {word} (ID: {new_note_id})")
                stats["added"] += 1

            elif status == "Updated" and note_id:
                if dry_run:
                    print(f"  🔍 [更新予定] {word} (ID: {note_id})")
                    stats["updated"] += 1
                    continue
                anki_request(
                    "updateNoteFields",
                    url=anki_url,
                    note={"id": note_id, "fields": note["fields"]},
                )
                update_notion_page(notion, entry["page_id"], note_id)
                print(f"  ✅ [更新] {word} (ID: {note_id})")
                stats["updated"] += 1

            else:
                print(f"  ⚠️  [スキップ] {word} — ステータス: {status}, NoteID: {note_id}")
                stats["skipped"] += 1

        except RuntimeError as e:
            if "duplicate" in str(e).lower():
                print(f"  ⏭️  [重複] {word} — Anki に既に存在")
                if not dry_run:
                    try:
                        found = anki_request(
                            "findNotes",
                            url=anki_url,
                            query=f'deck:"{deck}" "Word:{word}"',
                        )
                        if found:
                            update_notion_page(notion, entry["page_id"], found[0])
                    except Exception:
                        pass
                stats["skipped"] += 1
            else:
                print(f"  ❌ [エラー] {word} — {e}")
                stats["errors"] += 1

        except Exception as e:
            print(f"  ❌ [エラー] {word} — {e}")
            stats["errors"] += 1

        # Notion API rate limit: 3 req/sec
        time.sleep(0.35)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Notion → Anki 同期")
    parser.add_argument("--dry-run", action="store_true", help="実行内容の確認のみ")
    parser.add_argument("--deck", type=str, help="特定のデッキのみ同期（例: Deutsch）")
    args = parser.parse_args()

    print("=" * 56)
    print("  Notion → Anki 同期")
    print("=" * 56)

    if args.dry_run:
        print("⚠️  dry-run モード\n")

    config = load_config()
    anki_url = config.get("anki", {}).get("url", "http://localhost:8765")

    notion = NotionClient(auth=config["notion_api_key"])
    print("🔌 Notion API 接続OK")

    try:
        version = anki_request("version", url=anki_url)
        print(f"🔌 AnkiConnect v{version} 接続OK\n")
    except SystemExit:
        raise

    databases = config.get("databases", {})
    if args.deck:
        if args.deck not in databases:
            print(f"❌ デッキ「{args.deck}」が config.yaml に見つかりません。")
            print(f"   利用可能: {', '.join(databases.keys())}")
            sys.exit(1)
        databases = {args.deck: databases[args.deck]}

    total = {"added": 0, "updated": 0, "skipped": 0, "errors": 0}
    for deck, db_id in databases.items():
        stats = sync_deck(notion, anki_url, deck, db_id, config, dry_run=args.dry_run)
        for k in total:
            total[k] += stats[k]

    print("\n" + "=" * 56)
    print("  同期完了！")
    print(
        f"    追加: {total['added']}  更新: {total['updated']}  "
        f"スキップ: {total['skipped']}  エラー: {total['errors']}"
    )
    print("=" * 56)


if __name__ == "__main__":
    main()
