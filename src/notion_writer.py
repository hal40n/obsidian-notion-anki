"""Notion へのページ作成・更新・重複チェック"""

from typing import Literal

from notion_client import Client as NotionClient

from src.models import CertVocabEntry, LangVocabEntry, VocabEntry
from src.notion_sync import get_text_property


def _rich_text(value: str) -> list[dict]:
    """Rich text プロパティの値を構築する。2000文字超は切り詰める。"""
    return [{"text": {"content": value[:2000]}}]


def _select(value: str) -> dict:
    """Select プロパティの値を構築する。空文字の場合は None を返す。"""
    return {"select": {"name": value} if value else None}


def _title(value: str) -> list[dict]:
    """Title プロパティの値を構築する。"""
    return [{"text": {"content": value}}]


def build_lang_properties(entry: LangVocabEntry) -> dict:
    """言語学習用エントリから Notion properties dict を構築する。"""
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
    """資格学習用エントリから Notion properties dict を構築する。"""
    return {
        "Term": {"title": _title(entry.word)},
        "Definition": {"rich_text": _rich_text(entry.meaning)},
        "Category": _select(entry.category),
        "Anki Status": {"select": {"name": "New"}},
    }


def build_properties(entry: VocabEntry) -> dict:
    """エントリ型に応じた properties dict を返す。"""
    if isinstance(entry, LangVocabEntry):
        return build_lang_properties(entry)
    return build_cert_properties(entry)


def _title_prop_name(entry: VocabEntry) -> str:
    """エントリ型に応じた Title プロパティ名を返す。"""
    return "Word" if isinstance(entry, LangVocabEntry) else "Term"


def find_existing_page(
    notion: NotionClient,
    ds_id: str,
    entry: VocabEntry,
) -> dict | None:
    """Word または Term で既存ページを検索する（API 2025-09-03 準拠）。"""
    prop_name = _title_prop_name(entry)
    response = notion.data_sources.query(
        ds_id,
        filter={"property": prop_name, "title": {"equals": entry.word}},
        page_size=1,
    )
    results = response.get("results", [])
    return results[0] if results else None


def has_content_changed(existing_page: dict, entry: VocabEntry) -> bool:
    """既存 Notion ページとエントリの内容を比較し、変更があれば True を返す。"""
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
    """Notion に新規ページを作成し、作成されたページの ID を返す。"""
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
    """既存ページを更新し、Anki Status を "Updated" にする。"""
    props = {**build_properties(entry), "Anki Status": {"select": {"name": "Updated"}}}
    notion.pages.update(page_id=page_id, properties=props)


def upsert_entry(
    notion: NotionClient,
    db_id: str,
    ds_id: str,
    entry: VocabEntry,
    dry_run: bool = False,
) -> Literal["created", "updated", "skipped"]:
    """エントリを Notion に登録または更新する。"""
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
