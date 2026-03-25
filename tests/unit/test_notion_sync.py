"""src/notion_sync.py のユニットテスト（純粋関数・軽量モック）"""

from unittest.mock import MagicMock

import pytest

from src.notion_sync import (
    _get_data_source_id,
    fetch_entries,
    get_text_property,
    update_notion_page,
)


def _make_page(prop_type: str, prop_name: str, value) -> dict:
    if prop_type == "title":
        return {"properties": {prop_name: {"type": "title", "title": [{"plain_text": value}]}}}
    if prop_type == "rich_text":
        return {
            "properties": {prop_name: {"type": "rich_text", "rich_text": [{"plain_text": value}]}}
        }
    if prop_type == "select":
        return {
            "properties": {
                prop_name: {"type": "select", "select": {"name": value} if value else None}
            }
        }
    if prop_type == "number":
        return {"properties": {prop_name: {"type": "number", "number": value}}}
    return {"properties": {prop_name: {"type": "unknown"}}}


class TestGetTextProperty:
    def test_title_property(self):
        page = _make_page("title", "Word", "gehen")
        assert get_text_property(page, "Word") == "gehen"

    def test_rich_text_property(self):
        page = _make_page("rich_text", "Meaning", "行く")
        assert get_text_property(page, "Meaning") == "行く"

    def test_select_property(self):
        page = _make_page("select", "Part of Speech", "Verb")
        assert get_text_property(page, "Part of Speech") == "Verb"

    def test_select_none_returns_empty(self):
        page = _make_page("select", "Part of Speech", None)
        assert get_text_property(page, "Part of Speech") == ""

    def test_number_property(self):
        page = _make_page("number", "Anki Note ID", 12345)
        assert get_text_property(page, "Anki Note ID") == 12345

    def test_missing_property_returns_empty(self):
        page = {"properties": {}}
        assert get_text_property(page, "Missing") == ""

    def test_unknown_type_returns_empty(self):
        page = _make_page("unknown", "Field", "value")
        assert get_text_property(page, "Field") == ""


class TestGetDataSourceId:
    def test_returns_first_data_source_id(self):
        notion = MagicMock()
        notion.databases.retrieve.return_value = {
            "data_sources": [{"id": "ds-id-123"}, {"id": "ds-id-456"}]
        }
        result = _get_data_source_id(notion, "db-id")
        assert result == "ds-id-123"

    def test_raises_when_no_data_sources(self):
        notion = MagicMock()
        notion.databases.retrieve.return_value = {"data_sources": []}
        with pytest.raises(ValueError, match="data source"):
            _get_data_source_id(notion, "db-id")


class TestUpdateNotionPage:
    def test_calls_pages_update_with_correct_args(self):
        notion = MagicMock()
        update_notion_page(notion, "page-id-123", 9876543)
        notion.pages.update.assert_called_once_with(
            page_id="page-id-123",
            properties={
                "Anki Status": {"select": {"name": "Synced"}},
                "Anki Note ID": {"number": 9876543},
            },
        )


def _make_lang_page(page_id: str, word: str, meaning: str) -> dict:
    return {
        "id": page_id,
        "properties": {
            "Anki Status": {"type": "select", "select": {"name": "New"}},
            "Anki Note ID": {"type": "number", "number": None},
            "Word": {"type": "title", "title": [{"plain_text": word}]},
            "Meaning": {"type": "rich_text", "rich_text": [{"plain_text": meaning}]},
            "Part of Speech": {"type": "select", "select": None},
            "Example": {"type": "rich_text", "rich_text": []},
            "Example Translation": {"type": "rich_text", "rich_text": []},
            "Usage": {"type": "rich_text", "rich_text": []},
            "Sources": {"type": "rich_text", "rich_text": []},
            "Language": {"type": "select", "select": {"name": "de"}},
        },
    }


def _make_cert_page(page_id: str, term: str, definition: str, note_id: int | None = None) -> dict:
    return {
        "id": page_id,
        "properties": {
            "Anki Status": {"type": "select", "select": {"name": "Updated"}},
            "Anki Note ID": {"type": "number", "number": note_id},
            "Term": {"type": "title", "title": [{"plain_text": term}]},
            "Definition": {"type": "rich_text", "rich_text": [{"plain_text": definition}]},
            "Category": {"type": "select", "select": {"name": "ネットワーク"}},
        },
    }


class TestFetchEntries:
    def test_language_entry_mapped_correctly(self):
        notion = MagicMock()
        notion.databases.retrieve.return_value = {"data_sources": [{"id": "ds-id"}]}
        notion.data_sources.query.return_value = {
            "results": [_make_lang_page("p1", "gehen", "行く")],
            "has_more": False,
            "next_cursor": None,
        }
        config = {"note_types": {"Deutsch": "SentenceVocab_DE"}}

        entries = fetch_entries(notion, "db-id", "Deutsch", config)

        assert len(entries) == 1
        assert entries[0]["word"] == "gehen"
        assert entries[0]["meaning"] == "行く"
        assert entries[0]["anki_status"] == "New"
        assert entries[0]["anki_note_id"] is None

    def test_cert_entry_mapped_correctly(self):
        notion = MagicMock()
        notion.databases.retrieve.return_value = {"data_sources": [{"id": "ds-id"}]}
        notion.data_sources.query.return_value = {
            "results": [
                _make_cert_page("p2", "スループット", "単位時間あたりのデータ量", note_id=12345)
            ],
            "has_more": False,
            "next_cursor": None,
        }
        config = {"note_types": {"応用情報技術者": "TermDefinition"}}

        entries = fetch_entries(notion, "db-id", "応用情報技術者", config)

        assert len(entries) == 1
        assert entries[0]["word"] == "スループット"
        assert entries[0]["meaning"] == "単位時間あたりのデータ量"
        assert entries[0]["anki_note_id"] == 12345

    def test_pagination_fetches_all_pages(self):
        notion = MagicMock()
        notion.databases.retrieve.return_value = {"data_sources": [{"id": "ds-id"}]}
        notion.data_sources.query.side_effect = [
            {
                "results": [_make_lang_page("p1", "gehen", "行く")],
                "has_more": True,
                "next_cursor": "cursor-1",
            },
            {
                "results": [_make_lang_page("p2", "kommen", "来る")],
                "has_more": False,
                "next_cursor": None,
            },
        ]
        config = {"note_types": {"Deutsch": "SentenceVocab_DE"}}

        entries = fetch_entries(notion, "db-id", "Deutsch", config)

        assert len(entries) == 2
        assert notion.data_sources.query.call_count == 2

    def test_returns_empty_when_no_results(self):
        notion = MagicMock()
        notion.databases.retrieve.return_value = {"data_sources": [{"id": "ds-id"}]}
        notion.data_sources.query.return_value = {
            "results": [],
            "has_more": False,
            "next_cursor": None,
        }
        config = {"note_types": {"Deutsch": "SentenceVocab_DE"}}

        entries = fetch_entries(notion, "db-id", "Deutsch", config)

        assert entries == []
