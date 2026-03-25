"""src/word_file_parser.py のユニットテスト"""

from pathlib import Path

from src.word_file_parser import parse_word_file, scan_word_files


class TestScanWordFiles:
    def test_returns_md_files(self, tmp_path: Path) -> None:
        (tmp_path / "gehen.md").write_text("---\n---\n", encoding="utf-8")
        (tmp_path / "singen.md").write_text("---\n---\n", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("not md", encoding="utf-8")
        result = scan_word_files(tmp_path)
        assert len(result) == 2
        assert all(p.suffix == ".md" for p in result)

    def test_returns_empty_for_nonexistent_dir(self, tmp_path: Path) -> None:
        result = scan_word_files(tmp_path / "nonexistent")
        assert result == []

    def test_returns_empty_for_empty_dir(self, tmp_path: Path) -> None:
        result = scan_word_files(tmp_path)
        assert result == []


class TestParseWordFile:
    def _write(self, tmp_path: Path, name: str, content: str) -> Path:
        f = tmp_path / name
        f.write_text(content, encoding="utf-8")
        return f

    def test_valid_frontmatter_returns_lang_entry(
        self, tmp_path: Path, sample_config: dict
    ) -> None:
        f = self._write(
            tmp_path,
            "gehen.md",
            "---\nword: gehen\nmeaning: 行く\ndeck: Deutsch\nlang: de\n---\n",
        )
        entry = parse_word_file(f, sample_config)
        assert entry is not None
        assert entry.word == "gehen"
        assert entry.meaning == "行く"
        assert entry.deck == "Deutsch"
        assert entry.lang == "de"

    def test_optional_fields_parsed(self, tmp_path: Path, sample_config: dict) -> None:
        f = self._write(
            tmp_path,
            "singen.md",
            (
                "---\n"
                "word: singen\n"
                "meaning: 歌う\n"
                "deck: Deutsch\n"
                "pos: Verb\n"
                "example: Er <<singt>> laut.\n"
                "example_translation: 彼は大声で歌う。\n"
                "usage: singen + Lied\n"
                "---\n"
            ),
        )
        entry = parse_word_file(f, sample_config)
        assert entry is not None
        assert entry.pos == "Verb"
        assert entry.example == "Er <<singt>> laut."
        assert entry.example_translation == "彼は大声で歌う。"
        assert entry.usage == "singen + Lied"

    def test_sources_always_empty(self, tmp_path: Path, sample_config: dict) -> None:
        f = self._write(
            tmp_path,
            "gehen.md",
            "---\nword: gehen\nmeaning: 行く\ndeck: Deutsch\n---\n",
        )
        entry = parse_word_file(f, sample_config)
        assert entry is not None
        assert entry.sources == []

    def test_missing_word_returns_none(self, tmp_path: Path, sample_config: dict) -> None:
        f = self._write(tmp_path, "x.md", "---\nmeaning: 行く\ndeck: Deutsch\n---\n")
        assert parse_word_file(f, sample_config) is None

    def test_missing_meaning_returns_none(self, tmp_path: Path, sample_config: dict) -> None:
        f = self._write(tmp_path, "x.md", "---\nword: gehen\ndeck: Deutsch\n---\n")
        assert parse_word_file(f, sample_config) is None

    def test_missing_deck_returns_none(self, tmp_path: Path, sample_config: dict) -> None:
        f = self._write(tmp_path, "x.md", "---\nword: gehen\nmeaning: 行く\n---\n")
        assert parse_word_file(f, sample_config) is None

    def test_no_frontmatter_returns_none(self, tmp_path: Path, sample_config: dict) -> None:
        f = self._write(tmp_path, "x.md", "# gehen\n\n意味: 行く\n")
        assert parse_word_file(f, sample_config) is None

    def test_cert_deck_returns_none(self, tmp_path: Path, sample_config: dict) -> None:
        """資格学習用デッキは LangVocabEntry に変換しない。"""
        f = self._write(
            tmp_path,
            "x.md",
            (
                "---\n"
                "word: スループット\n"
                "meaning: 単位時間あたりに処理できるデータ量。\n"
                "deck: 応用情報技術者\n"
                "---\n"
            ),
        )
        assert parse_word_file(f, sample_config) is None
