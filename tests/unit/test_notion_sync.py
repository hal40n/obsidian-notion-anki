"""src/notion_sync.py のユニットテスト（純粋関数・軽量モック）"""

import pytest
from unittest.mock import MagicMock

from src.notion_sync import get_text_property, _get_data_source_id, update_notion_page


def _make_page(prop_type: str, prop_name: str, value) -> dict:
    if prop_type == "title":
        return {"properties": {prop_name: {"type": "title", "title": [{"plain_text": value}]}}}
    if prop_type == "rich_text":
        return {"properties": {prop_name: {"type": "rich_text", "rich_text": [{"plain_text": value}]}}}
    if prop_type == "select":
        return {"properties": {prop_name: {"type": "select", "select": {"name": value} if value else None}}}
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
