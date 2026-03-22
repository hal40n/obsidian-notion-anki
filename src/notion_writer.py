"""Notion へのページ作成・更新・重複チェック"""

from typing import Literal

from notion_client import Client as NotionClient

from src.models import CertVocabEntry, LangVocabEntry, VocabEntry
from src.notion_sync import get_text_property


def _rich_text(value: str) -> list[dict]:
    """Rich text プロパティの値を構築する。

    Args:
        value: テキスト文字列。2000文字を超える場合は切り詰める。

    Returns:
        Notion API の rich_text プロパティ値リスト。
    """
    return [{"text": {"content": value[:2000]}}]


def _select(value: str) -> dict:
    """Select プロパティの値を構築する。

    Args:
        value: 選択肢名。空文字の場合は None を設定する。

    Returns:
        Notion API の select プロパティ値辞書。
    """
    return {"select": {"name": value} if value else None}


def _title(value: str) -> list[dict]:
    """Title プロパティの値を構築する。

    Args:
        value: タイトル文字列。

    Returns:
        Notion API の title プロパティ値リスト。
    """
    return [{"text": {"content": value}}]


def build_lang_properties(entry: LangVocabEntry) -> dict:
    """言語学習用エントリから Notion properties dict を構築する。

    Args:
        entry: 言語学習用語彙エントリ。

    Returns:
        Notion API に渡す properties 辞書。Anki Status は "New" に設定される。
    """
    return {
        "Word": {"title": _title(entry.word)},
        "Meaning": {"rich_text": _rich_text(entry.meaning)},
        "Part of Speech": _select(entry.pos),
        "Example": {"rich_text": _rich_text(entry.example)},
        "Example Translation": {"rich_text": _rich_text(entry.example_translation)},
        "Usage": {"rich_text": _rich_text(entry.usage)},
        "Sources": {"rich_text": _rich_text(", ".join(entry.sources))},
        "Language": _select(entry.lang),
        "Anki Status": {"select": {"name": "New"}},
    }


def build_cert_properties(entry: CertVocabEntry) -> dict:
    """資格学習用エントリから Notion properties dict を構築する。

    Args:
        entry: 資格学習用語彙エントリ。

    Returns:
        Notion API に渡す properties 辞書。Anki Status は "New" に設定される。
    """
    return {
        "Term": {"title": _title(entry.word)},
        "Definition": {"rich_text": _rich_text(entry.meaning)},
        "Category": _select(entry.category),
        "Anki Status": {"select": {"name": "New"}},
    }


def build_properties(entry: VocabEntry) -> dict:
    """エントリ型に応じた Notion properties dict を返す。

    Args:
        entry: 語彙エントリ（LangVocabEntry または CertVocabEntry）。

    Returns:
        Notion API に渡す properties 辞書。
    """
    if isinstance(entry, LangVocabEntry):
        return build_lang_properties(entry)
    return build_cert_properties(entry)


def _title_prop_name(entry: VocabEntry) -> str:
    """エントリ型に応じた Notion の Title プロパティ名を返す。

    Args:
        entry: 語彙エントリ。

    Returns:
        LangVocabEntry の場合は "Word"、CertVocabEntry の場合は "Term"。
    """
    return "Word" if isinstance(entry, LangVocabEntry) else "Term"


def find_existing_page(
    notion: NotionClient,
    ds_id: str,
    entry: VocabEntry,
) -> dict | None:
    """Word または Term で既存ページを検索する（API 2025-09-03 準拠）。

    Args:
        notion: Notion クライアントインスタンス。
        ds_id: data source ID。
        entry: 検索対象の語彙エントリ。

    Returns:
        既存ページ辞書。見つからない場合は None。
    """
    prop_name = _title_prop_name(entry)
    response = notion.data_sources.query(
        ds_id,
        filter={"property": prop_name, "title": {"equals": entry.word}},
        page_size=1,
    )
    results = response.get("results", [])
    return results[0] if results else None


def has_content_changed(existing_page: dict, entry: VocabEntry) -> bool:
    """既存 Notion ページとエントリの内容を比較する。

    Args:
        existing_page: Notion API から取得した既存ページ辞書。
        entry: 比較対象の語彙エントリ。

    Returns:
        内容に変更がある場合は True。
    """
    props = existing_page.get("properties", {})

    if isinstance(entry, LangVocabEntry):
        return (
            get_text_property(existing_page, "Meaning") != entry.meaning
            or get_text_property(existing_page, "Part of Speech") != entry.pos
            or get_text_property(existing_page, "Example") != entry.example
            or get_text_property(existing_page, "Example Translation") != entry.example_translation
            or get_text_property(existing_page, "Usage") != entry.usage
        )

    # CertVocabEntry
    category = ""
    cat_prop = props.get("Category", {})
    if cat_prop.get("type") == "select" and cat_prop.get("select"):
        category = cat_prop["select"].get("name", "")

    return (
        get_text_property(existing_page, "Definition") != entry.meaning
        or category != entry.category
    )


def create_page(notion: NotionClient, db_id: str, entry: VocabEntry) -> str:
    """Notion に新規ページを作成する。

    Args:
        notion: Notion クライアントインスタンス。
        db_id: 作成先データベース ID。
        entry: 作成する語彙エントリ。

    Returns:
        作成されたページの ID。
    """
    result = notion.pages.create(
        parent={"database_id": db_id},
        properties=build_properties(entry),
    )
    return result["id"]


def update_page_to_updated(
    notion: NotionClient,
    page_id: str,
    entry: VocabEntry,
) -> None:
    """既存ページの内容を更新し、Anki Status を "Updated" にする。

    Args:
        notion: Notion クライアントインスタンス。
        page_id: 更新対象のページ ID。
        entry: 更新内容を持つ語彙エントリ。
    """
    props = {**build_properties(entry), "Anki Status": {"select": {"name": "Updated"}}}
    notion.pages.update(page_id=page_id, properties=props)


def upsert_entry(
    notion: NotionClient,
    db_id: str,
    ds_id: str,
    entry: VocabEntry,
    dry_run: bool = False,
) -> Literal["created", "updated", "skipped"]:
    """エントリを Notion に登録または更新する。

    既存ページが見つからない場合は新規作成、内容が変わっている場合は更新、
    変更がない場合はスキップする。

    Args:
        notion: Notion クライアントインスタンス。
        db_id: 対象データベース ID。
        ds_id: data source ID。
        entry: 登録・更新する語彙エントリ。
        dry_run: True の場合、API への書き込みを行わない。

    Returns:
        実行結果を示す文字列（"created" / "updated" / "skipped"）。
    """
    existing = find_existing_page(notion, ds_id, entry)

    if existing is None:
        if not dry_run:
            create_page(notion, db_id, entry)
        return "created"

    if has_content_changed(existing, entry):
        if not dry_run:
            update_page_to_updated(notion, existing["id"], entry)
        return "updated"

    return "skipped"
