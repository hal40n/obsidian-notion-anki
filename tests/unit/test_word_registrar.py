"""src/word_registrar.py のユニットテスト"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import LangVocabEntry
from src.word_registrar import process_word_files, register_entry


def _make_entry(word: str = "gehen", deck: str = "Deutsch") -> LangVocabEntry:
    return LangVocabEntry(
        word=word,
        meaning="行く",
        deck=deck,
        file_path=Path(f"{word}.md"),
    )


def _write_word_file(word_dir: Path, word: str, deck: str = "Deutsch") -> Path:
    f = word_dir / f"{word}.md"
    f.write_text(
        f"---\nword: {word}\nmeaning: テスト\ndeck: {deck}\n---\n",
        encoding="utf-8",
    )
    return f


class TestRegisterEntry:
    def test_creates_when_no_existing(self) -> None:
        notion = MagicMock()
        entry = _make_entry()

        with (
            patch("src.word_registrar.find_existing_page", return_value=None) as mock_find,
            patch("src.word_registrar.create_page") as mock_create,
        ):
            register_entry(notion, "db_id", "ds_id", entry, dry_run=False)
            mock_find.assert_called_once_with(notion, "ds_id", entry)
            mock_create.assert_called_once_with(notion, "db_id", entry)

    def test_raises_when_existing(self) -> None:
        notion = MagicMock()
        entry = _make_entry()
        existing = {"id": "page_id", "properties": {}}

        with (
            patch("src.word_registrar.find_existing_page", return_value=existing),
            pytest.raises(RuntimeError, match="既に Notion DB に存在します"),
        ):
            register_entry(notion, "db_id", "ds_id", entry)

    def test_dry_run_skips_create(self) -> None:
        notion = MagicMock()
        entry = _make_entry()

        with (
            patch("src.word_registrar.find_existing_page", return_value=None),
            patch("src.word_registrar.create_page") as mock_create,
        ):
            register_entry(notion, "db_id", "ds_id", entry, dry_run=True)
            mock_create.assert_not_called()

    def test_dry_run_still_raises_on_duplicate(self) -> None:
        notion = MagicMock()
        entry = _make_entry()
        existing = {"id": "page_id", "properties": {}}

        with (
            patch("src.word_registrar.find_existing_page", return_value=existing),
            pytest.raises(RuntimeError),
        ):
            register_entry(notion, "db_id", "ds_id", entry, dry_run=True)


class TestProcessWordFiles:
    def test_file_deleted_after_success(self, tmp_path: Path, sample_config: dict) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        f = _write_word_file(word_dir, "gehen")

        with (
            patch("src.word_registrar._get_data_source_id", return_value="ds_id"),
            patch("src.word_registrar.register_entry"),
            patch("src.word_registrar.time.sleep"),
        ):
            stats = process_word_files(MagicMock(), word_dir, sample_config)

        assert stats["created"] == 1
        assert not f.exists()

    def test_file_not_deleted_on_duplicate(self, tmp_path: Path, sample_config: dict) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        f = _write_word_file(word_dir, "gehen")

        with (
            patch("src.word_registrar._get_data_source_id", return_value="ds_id"),
            patch("src.word_registrar.register_entry", side_effect=RuntimeError("既に存在")),
            patch("src.word_registrar.time.sleep"),
        ):
            stats = process_word_files(MagicMock(), word_dir, sample_config)

        assert stats["errors"] == 1
        assert f.exists()

    def test_file_not_deleted_on_dry_run(self, tmp_path: Path, sample_config: dict) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        f = _write_word_file(word_dir, "gehen")

        with (
            patch("src.word_registrar._get_data_source_id", return_value="ds_id"),
            patch("src.word_registrar.register_entry"),
            patch("src.word_registrar.time.sleep"),
        ):
            stats = process_word_files(MagicMock(), word_dir, sample_config, dry_run=True)

        assert stats["created"] == 1
        assert f.exists()

    def test_empty_dir_returns_zero_stats(self, tmp_path: Path, sample_config: dict) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        stats = process_word_files(MagicMock(), word_dir, sample_config)
        assert stats == {"created": 0, "errors": 0}

    def test_missing_db_id_increments_errors(self, tmp_path: Path, sample_config: dict) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        _write_word_file(word_dir, "hello", deck="English")

        stats = process_word_files(MagicMock(), word_dir, sample_config)
        assert stats["errors"] == 1

    def test_deck_filter_skips_other_decks(self, tmp_path: Path, sample_config: dict) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        f_de = _write_word_file(word_dir, "gehen", deck="Deutsch")
        f_en = _write_word_file(word_dir, "hello", deck="English")
        config = {
            **sample_config,
            "databases": {**sample_config["databases"], "English": "en-db-id"},
        }

        with (
            patch("src.word_registrar._get_data_source_id", return_value="ds_id"),
            patch("src.word_registrar.register_entry"),
            patch("src.word_registrar.time.sleep"),
        ):
            stats = process_word_files(MagicMock(), word_dir, config, deck_filter="Deutsch")

        assert stats["created"] == 1
        assert not f_de.exists()
        assert f_en.exists()

    def test_multiple_files_processed(self, tmp_path: Path, sample_config: dict) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        _write_word_file(word_dir, "gehen")
        _write_word_file(word_dir, "singen")

        with (
            patch("src.word_registrar._get_data_source_id", return_value="ds_id"),
            patch("src.word_registrar.register_entry"),
            patch("src.word_registrar.time.sleep"),
        ):
            stats = process_word_files(MagicMock(), word_dir, sample_config)

        assert stats["created"] == 2
