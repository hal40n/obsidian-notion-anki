"""
Phase 3: Obsidian → Notion 同期スクリプト
==========================================
Obsidian の vocab/ ディレクトリを走査し、anki_synced = false のエントリを
Notion DB に登録（新規）または更新する。

前提条件:
  - .env に NOTION_API_KEY を設定済み
  - config.yaml の obsidian.vault_path と vocab_dirs を設定済み

使い方:
  python obsidian2notion.py              # 全 vocab_dirs を同期
  python obsidian2notion.py --dry-run   # 確認のみ（ファイル書き換えなし）
  python obsidian2notion.py --deck Deutsch  # 特定デッキのみ
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from notion_client import Client as NotionClient

from src.config import load_config
from src.notion_sync import _get_data_source_id
from src.notion_writer import upsert_entry
from src.obsidian_parser import load_vocab_entry, scan_vocab_files, update_frontmatter_synced


def sync_vocab_dir(
    notion: NotionClient,
    vault_path: Path,
    vocab_dir: str,
    config: dict,
    deck_filter: str | None,
    dry_run: bool,
) -> dict:
    """1つの vocab_dir を処理し、統計を返す。"""
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
    databases = config.get("databases", {})

    files = scan_vocab_files(vault_path, [vocab_dir])
    if not files:
        return stats

    # ds_id キャッシュ（デッキごとに1回だけ databases.retrieve を呼ぶ）
    ds_id_cache: dict[str, str] = {}

    for file_path in files:
        entry = load_vocab_entry(file_path, vault_path, config)
        if entry is None:
            continue

        # デッキフィルタ
        if deck_filter and entry.deck != deck_filter:
            continue

        db_id = databases.get(entry.deck)
        if not db_id:
            print(f"  ⚠️  デッキ「{entry.deck}」の DB ID が config.yaml にありません: {file_path.name}")
            stats["errors"] += 1
            continue

        try:
            if db_id not in ds_id_cache:
                ds_id_cache[db_id] = _get_data_source_id(notion, db_id)
            ds_id = ds_id_cache[db_id]

            result = upsert_entry(notion, db_id, ds_id, entry, dry_run=dry_run)

            if result == "created":
                print(f"  ✅ [登録] {entry.word}")
                stats["created"] += 1
            elif result == "updated":
                print(f"  🔄 [更新] {entry.word}")
                stats["updated"] += 1
            else:
                print(f"  ⏭️  [スキップ] {entry.word}")
                stats["skipped"] += 1

            # 成功時にのみ frontmatter を更新
            if not dry_run and result in ("created", "updated"):
                iso_now = datetime.now(timezone.utc).astimezone().isoformat()
                update_frontmatter_synced(file_path, iso_now)

        except Exception as e:
            print(f"  ❌ [エラー] {entry.word} — {e}")
            stats["errors"] += 1

        # Notion API rate limit: 3 req/sec（find + create/update で最大2リクエスト）
        time.sleep(0.5)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Obsidian → Notion 同期（設計書 v4 Phase 3）")
    parser.add_argument("--dry-run", action="store_true", help="確認のみ（ファイル書き換えなし）")
    parser.add_argument("--deck", type=str, help="特定のデッキのみ同期（例: Deutsch）")
    args = parser.parse_args()

    print("=" * 56)
    print("  Obsidian → Notion 同期（設計書 v4 Phase 3）")
    print("=" * 56)

    if args.dry_run:
        print("⚠️  dry-run モード\n")

    config = load_config()
    obsidian_cfg = config.get("obsidian", {})
    vault_path_str = obsidian_cfg.get("vault_path", "")

    if not vault_path_str or vault_path_str == "/path/to/your/vault":
        print("❌ config.yaml の obsidian.vault_path を設定してください。")
        sys.exit(1)

    vault_path = Path(vault_path_str)
    if not vault_path.exists():
        print(f"❌ vault_path が存在しません: {vault_path}")
        sys.exit(1)

    vocab_dirs: list[str] = obsidian_cfg.get("vocab_dirs", [])
    if not vocab_dirs:
        print("❌ config.yaml の obsidian.vocab_dirs を設定してください。")
        sys.exit(1)

    notion = NotionClient(auth=config["notion_api_key"])
    print("🔌 Notion API 接続OK\n")

    total = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for vocab_dir in vocab_dirs:
        print(f"📂 {vocab_dir}/")
        stats = sync_vocab_dir(
            notion=notion,
            vault_path=vault_path,
            vocab_dir=vocab_dir,
            config=config,
            deck_filter=args.deck,
            dry_run=args.dry_run,
        )
        for k in total:
            total[k] += stats[k]

    print("\n" + "=" * 56)
    print("  同期完了！")
    print(
        f"    登録: {total['created']}  更新: {total['updated']}  "
        f"スキップ: {total['skipped']}  エラー: {total['errors']}"
    )
    print("=" * 56)


if __name__ == "__main__":
    main()
