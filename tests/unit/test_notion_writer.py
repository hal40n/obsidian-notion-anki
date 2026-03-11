"""src/notion_writer.py のユニットテスト"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.models import LangVocabEntry, CertVocabEntry
from src.notion_writer import (
    _rich_text,
    _select,
    _title,
    build_lang_properties,
    build_cert_properties,
    build_properties,
    has_content_changed,
    upsert_entry,
)


@pytest.fixture
def lang_entry(tmp_path):
    return LangVocabEntry(
        word="gehen",
        meaning="行く、歩く",
        deck="Deutsch",
        file_path=tmp_path / "gehen.md",
        pos="Verb",
        example="Ich <<gehe>> in den Park.",
        example_translation="私は公園へ行く。",
        usage="gehen + Richtung",
        lang="de_DE",
        sources=["Deutsch perfekt"],
    )


@pytest.fixture
def cert_entry(tmp_path):
    return CertVocabEntry(
        word="スループット",
        meaning="単位時間あたりに処理できるデータ量。",
        deck="応用情報技術者",
        file_path=tmp_path / "スループット.md",
        category="ネットワーク",
    )


@pytest.fixture
def mock_notion():
    return MagicMock()


# ── _rich_text ───────────────────────────────────────────────────

class TestRichText:
    def test_normal_string(self):
        result = _rich_text("テスト")
        assert result == [{"text": {"content": "テスト"}}]

    def test_empty_string(self):
        result = _rich_text("")
        assert result == [{"text": {"content": ""}}]

    def test_truncates_at_2000_chars(self):
        long_str = "a" * 2100
        result = _rich_text(long_str)
        assert len(result[0]["text"]["content"]) <= 2000


# ── _select ──────────────────────────────────────────────────────

class TestSelect:
    def test_nonempty_value(self):
        result = _select("Verb")
        assert result == {"select": {"name": "Verb"}}

    def test_empty_string_returns_none_select(self):
        result = _select("")
        assert result == {"select": None}


# ── _title ───────────────────────────────────────────────────────

class TestTitle:
    def test_normal_title(self):
        result = _title("gehen")
        assert result == [{"text": {"content": "gehen"}}]


# ── build_lang_properties ────────────────────────────────────────

class TestBuildLangProperties:
    def test_has_required_keys(self, lang_entry):
        props = build_lang_properties(lang_entry)
        assert "Word" in props
        assert "Meaning" in props
        assert "Anki Status" in props
        assert "Example" in props
        assert "Language" in props

    def test_word_is_title(self, lang_entry):
        props = build_lang_properties(lang_entry)
        assert props["Word"]["title"][0]["text"]["content"] == "gehen"

    def test_anki_status_is_new(self, lang_entry):
        props = build_lang_properties(lang_entry)
        assert props["Anki Status"]["select"]["name"] == "New"

    def test_sources_joined(self, lang_entry):
        props = build_lang_properties(lang_entry)
        assert "Deutsch perfekt" in props["Sources"]["rich_text"][0]["text"]["content"]


# ── build_cert_properties ────────────────────────────────────────

class TestBuildCertProperties:
    def test_has_required_keys(self, cert_entry):
        props = build_cert_properties(cert_entry)
        assert "Term" in props
        assert "Definition" in props
        assert "Category" in props
        assert "Anki Status" in props

    def test_term_is_title(self, cert_entry):
        props = build_cert_properties(cert_entry)
        assert props["Term"]["title"][0]["text"]["content"] == "スループット"

    def test_anki_status_is_new(self, cert_entry):
        props = build_cert_properties(cert_entry)
        assert props["Anki Status"]["select"]["name"] == "New"


# ── has_content_changed ──────────────────────────────────────────

def _make_lang_page(meaning="行く、歩く", pos="Verb"):
    """テスト用 Notion ページ dict を作成する。"""
    return {
        "properties": {
            "Meaning": {"type": "rich_text", "rich_text": [{"plain_text": meaning}]},
            "Part of Speech": {"type": "select", "select": {"name": pos} if pos else None},
            "Example": {"type": "rich_text", "rich_text": []},
            "Example Translation": {"type": "rich_text", "rich_text": []},
            "Usage": {"type": "rich_text", "rich_text": []},
        }
    }


def _make_cert_page(meaning="定義", category="ネットワーク"):
    return {
        "properties": {
            "Definition": {"type": "rich_text", "rich_text": [{"plain_text": meaning}]},
            "Category": {"type": "select", "select": {"name": category} if category else None},
        }
    }


class TestHasContentChanged:
    def test_lang_unchanged_returns_false(self, lang_entry, tmp_path):
        entry = LangVocabEntry(
            word="gehen", meaning="行く、歩く", deck="Deutsch",
            file_path=tmp_path / "g.md", pos="Verb",
        )
        page = _make_lang_page(meaning="行く、歩く", pos="Verb")
        assert has_content_changed(page, entry) is False

    def test_lang_meaning_changed_returns_true(self, tmp_path):
        entry = LangVocabEntry(
            word="gehen", meaning="歩く（新しい意味）", deck="Deutsch",
            file_path=tmp_path / "g.md",
        )
        page = _make_lang_page(meaning="行く、歩く")
        assert has_content_changed(page, entry) is True

    def test_cert_unchanged_returns_false(self, cert_entry):
        page = _make_cert_page(meaning="単位時間あたりに処理できるデータ量。", category="ネットワーク")
        assert has_content_changed(page, cert_entry) is False

    def test_cert_meaning_changed_returns_true(self, cert_entry):
        page = _make_cert_page(meaning="古い定義")
        assert has_content_changed(page, cert_entry) is True


# ── upsert_entry ─────────────────────────────────────────────────

class TestUpsertEntry:
    def test_creates_new_page_when_not_exists(self, mock_notion, lang_entry):
        mock_notion.data_sources.query.return_value = {"results": []}
        mock_notion.pages.create.return_value = {"id": "new-page-id"}

        result = upsert_entry(
            mock_notion, "db-id", "ds-id", lang_entry, dry_run=False
        )

        assert result == "created"
        mock_notion.pages.create.assert_called_once()

    def test_updates_when_content_changed(self, mock_notion, tmp_path):
        existing_page = {
            "id": "existing-id",
            **_make_lang_page(meaning="古い意味"),
        }
        mock_notion.data_sources.query.return_value = {"results": [existing_page]}

        entry = LangVocabEntry(
            word="gehen", meaning="新しい意味", deck="Deutsch",
            file_path=tmp_path / "g.md",
        )
        result = upsert_entry(mock_notion, "db-id", "ds-id", entry, dry_run=False)

        assert result == "updated"
        mock_notion.pages.update.assert_called_once()

    def test_skips_when_content_unchanged(self, mock_notion, tmp_path):
        existing_page = {
            "id": "existing-id",
            **_make_lang_page(meaning="行く", pos=""),
        }
        mock_notion.data_sources.query.return_value = {"results": [existing_page]}

        entry = LangVocabEntry(
            word="gehen", meaning="行く", deck="Deutsch",
            file_path=tmp_path / "g.md",
        )
        result = upsert_entry(mock_notion, "db-id", "ds-id", entry, dry_run=False)

        assert result == "skipped"
        mock_notion.pages.create.assert_not_called()
        mock_notion.pages.update.assert_not_called()

    def test_dry_run_does_not_call_api(self, mock_notion, lang_entry):
        mock_notion.data_sources.query.return_value = {"results": []}

        result = upsert_entry(mock_notion, "db-id", "ds-id", lang_entry, dry_run=True)

        assert result == "created"
        mock_notion.pages.create.assert_not_called()
