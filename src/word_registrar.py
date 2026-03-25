"""word/ ファイルを Notion DB へ登録するロジック

重複チェック付きの新規作成のみを行う（upsert は行わない）。
"""

import time
from pathlib import Path

from notion_client import Client as NotionClient

from src.models import LangVocabEntry
from src.notion_sync import _get_data_source_id
from src.notion_writer import create_page, find_existing_page
from src.word_file_parser import parse_word_file, scan_word_files


def register_entry(
    notion: NotionClient,
    db_id: str,
    ds_id: str,
    entry: LangVocabEntry,
    dry_run: bool = False,
) -> None:
    """重複チェック付きで Notion に新規作成する。

    既存ページが見つかった場合は RuntimeError を発生させる。
    dry_run でも重複チェックは実行する。

    Args:
        notion: Notion クライアントインスタンス。
        db_id: 作成先データベース ID。
        ds_id: data source ID。
        entry: 登録する語彙エントリ。
        dry_run: True の場合、API への書き込みを行わない。

    Raises:
        RuntimeError: 同一単語が Notion DB に既に存在する場合。
    """
    existing = find_existing_page(notion, ds_id, entry)
    if existing is not None:
        raise RuntimeError(f"単語「{entry.word}」は既に Notion DB に存在します")
    if not dry_run:
        create_page(notion, db_id, entry)


def _process_single_file(
    notion: NotionClient,
    file_path: Path,
    config: dict,
    ds_id_cache: dict[str, str],
    deck_filter: str | None,
    dry_run: bool,
) -> tuple[str, bool]:
    """1ファイルを処理し、(結果ラベル, ファイル削除すべきか) を返す。

    Args:
        notion: Notion クライアントインスタンス。
        file_path: 処理対象の word/*.md ファイルパス。
        config: アプリケーション設定辞書。
        ds_id_cache: db_id → ds_id のキャッシュ辞書。
        deck_filter: 同期対象デッキ名。None の場合は全デッキを対象とする。
        dry_run: True の場合、書き込みと削除を行わない。

    Returns:
        (結果ラベル, ファイルを削除すべきか) のタプル。
        結果ラベル: "created" / "error" / "skip"
    """
    entry = parse_word_file(file_path, config)
    if entry is None:
        print(f"  ⚠️  [スキップ] フォーマット不正: {file_path.name}")
        return "error", False

    if deck_filter and entry.deck != deck_filter:
        return "skip", False

    db_id = config.get("databases", {}).get(entry.deck)
    if not db_id:
        print(f"  ⚠️  デッキ「{entry.deck}」の DB ID が config.yaml にありません: {file_path.name}")
        return "error", False

    if db_id not in ds_id_cache:
        ds_id_cache[db_id] = _get_data_source_id(notion, db_id)
    ds_id = ds_id_cache[db_id]

    try:
        register_entry(notion, db_id, ds_id, entry, dry_run=dry_run)
        print(f"  ✅ [登録] {entry.word}")
        return "created", not dry_run
    except RuntimeError as e:
        print(f"  ❌ [重複] {e}")
        return "error", False


def process_word_files(
    notion: NotionClient,
    word_dir: Path,
    config: dict,
    deck_filter: str | None = None,
    dry_run: bool = False,
) -> dict:
    """word/ ディレクトリのファイルを一括処理して統計を返す。

    成功したファイルは削除する（dry_run の場合は削除しない）。
    重複・フォーマット不正・DB 設定漏れはエラーカウントに加算し、ファイルは残す。

    Args:
        notion: Notion クライアントインスタンス。
        word_dir: スキャン対象ディレクトリ。
        config: アプリケーション設定辞書。
        deck_filter: 同期対象デッキ名。None の場合は全デッキを対象とする。
        dry_run: True の場合、API への書き込みとファイル削除を行わない。

    Returns:
        同期結果の統計辞書（created / errors）。
    """
    stats = {"created": 0, "errors": 0}
    files = scan_word_files(word_dir)
    if not files:
        return stats

    ds_id_cache: dict[str, str] = {}

    for file_path in files:
        try:
            label, should_delete = _process_single_file(
                notion, file_path, config, ds_id_cache, deck_filter, dry_run
            )
        except Exception as e:
            print(f"  ❌ [エラー] {file_path.name} — {e}")
            stats["errors"] += 1
            time.sleep(0.5)
            continue

        if label == "created":
            stats["created"] += 1
            if should_delete:
                file_path.unlink()
        elif label == "error":
            stats["errors"] += 1

        time.sleep(0.5)

    return stats
