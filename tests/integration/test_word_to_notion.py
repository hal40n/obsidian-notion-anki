"""word_to_notion.py の統合テスト"""

from pathlib import Path
from unittest.mock import patch

import pytest


def _write_word_file(word_dir: Path, word: str, deck: str = "Deutsch") -> Path:
    f = word_dir / f"{word}.md"
    f.write_text(
        f"---\nword: {word}\nmeaning: テスト\ndeck: {deck}\n---\n",
        encoding="utf-8",
    )
    return f


def _base_config(word_dir: Path) -> dict:
    return {
        "databases": {"Deutsch": "db-deutsch-id"},
        "note_types": {"Deutsch": "SentenceVocab_DE"},
        "notion_api_key": "ntn_test",
        "word_dir": str(word_dir),
    }


class TestMain:
    def test_registers_word_files(self, tmp_path: Path, monkeypatch) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        _write_word_file(word_dir, "gehen")
        config = _base_config(word_dir)

        monkeypatch.setattr("word_to_notion.load_config", lambda: config)
        monkeypatch.setattr("sys.argv", ["word_to_notion.py"])

        with (
            patch("word_to_notion.NotionClient"),
            patch(
                "word_to_notion.process_word_files",
                return_value={"created": 1, "errors": 0},
            ) as mock_process,
        ):
            import word_to_notion

            word_to_notion.main()
            mock_process.assert_called_once()

    def test_dry_run_passes_flag(self, tmp_path: Path, monkeypatch) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        config = _base_config(word_dir)

        monkeypatch.setattr("word_to_notion.load_config", lambda: config)
        monkeypatch.setattr("sys.argv", ["word_to_notion.py", "--dry-run"])

        with (
            patch("word_to_notion.NotionClient"),
            patch(
                "word_to_notion.process_word_files",
                return_value={"created": 0, "errors": 0},
            ) as mock_process,
        ):
            import word_to_notion

            word_to_notion.main()
            _, kwargs = mock_process.call_args
            assert kwargs.get("dry_run") is True

    def test_exits_when_word_dir_not_configured(self, tmp_path: Path, monkeypatch) -> None:
        config = {
            "databases": {"Deutsch": "db-id"},
            "note_types": {},
            "notion_api_key": "ntn_test",
            # word_dir キーなし
        }
        monkeypatch.setattr("word_to_notion.load_config", lambda: config)
        monkeypatch.setattr("sys.argv", ["word_to_notion.py"])

        import word_to_notion

        with pytest.raises(SystemExit):
            word_to_notion.main()

    def test_deck_filter_passed_to_process(self, tmp_path: Path, monkeypatch) -> None:
        word_dir = tmp_path / "word"
        word_dir.mkdir()
        config = _base_config(word_dir)

        monkeypatch.setattr("word_to_notion.load_config", lambda: config)
        monkeypatch.setattr("sys.argv", ["word_to_notion.py", "--deck", "Deutsch"])

        with (
            patch("word_to_notion.NotionClient"),
            patch(
                "word_to_notion.process_word_files",
                return_value={"created": 0, "errors": 0},
            ) as mock_process,
        ):
            import word_to_notion

            word_to_notion.main()
            _, kwargs = mock_process.call_args
            assert kwargs.get("deck_filter") == "Deutsch"
