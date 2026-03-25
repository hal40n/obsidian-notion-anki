"""
word/ → Notion DB 同期スクリプト
==========================================
word/ ディレクトリの .md ファイルを Notion DB に新規登録する。
同一単語が既に存在する場合はエラーとして扱い、ファイルを残す。
登録成功後はファイルを削除する。

前提条件:
  - .env に NOTION_API_KEY を設定済み
  - config.yaml の word_dir にファイルの置き場所を設定済み

使い方:
  python word_to_notion.py               # word_dir 内を全て登録
  python word_to_notion.py --dry-run     # 確認のみ（書き込み・削除なし）
  python word_to_notion.py --deck Deutsch  # 特定デッキのみ
"""

import argparse
import sys
from pathlib import Path

from notion_client import Client as NotionClient

from src.config import load_config
from src.word_registrar import process_word_files


def main() -> None:
    parser = argparse.ArgumentParser(description="word/ → Notion DB 同期")
    parser.add_argument("--dry-run", action="store_true", help="確認のみ（書き込み・削除なし）")
    parser.add_argument("--deck", type=str, help="特定デッキのみ同期（例: Deutsch）")
    args = parser.parse_args()

    print("=" * 56)
    print("  word/ → Notion DB 同期")
    print("=" * 56)

    if args.dry_run:
        print("⚠️  dry-run モード\n")

    config = load_config()
    word_dir_str = config.get("word_dir", "")

    if not word_dir_str:
        print("❌ config.yaml の word_dir を設定してください。")
        sys.exit(1)

    word_dir = Path(word_dir_str)
    if not word_dir.exists():
        word_dir.mkdir(parents=True)
        print(f"📁 word_dir を作成しました: {word_dir}\n")

    notion = NotionClient(auth=config["notion_api_key"])
    print("🔌 Notion API 接続OK\n")

    stats = process_word_files(
        notion=notion,
        word_dir=word_dir,
        config=config,
        deck_filter=args.deck,
        dry_run=args.dry_run,
    )

    print("\n" + "=" * 56)
    print("  登録完了！")
    print(f"    登録: {stats['created']}  エラー: {stats['errors']}")
    print("=" * 56)


if __name__ == "__main__":
    main()
