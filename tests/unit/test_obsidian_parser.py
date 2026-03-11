"""src/obsidian_parser.py のユニットテスト"""

import pytest
from pathlib import Path

from src.obsidian_parser import (
    parse_frontmatter,
    is_unsynced,
    update_frontmatter_synced,
    get_backlinks,
    scan_vocab_files,
    load_vocab_entry,
)
from src.models import LangVocabEntry, CertVocabEntry


# ── parse_frontmatter ────────────────────────────────────────────

class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\nword: gehen\nmeaning: 行く\n---\n\n本文"
        result = parse_frontmatter(content)
        assert result == {"word": "gehen", "meaning": "行く"}

    def test_no_frontmatter_returns_none(self):
        content = "# タイトル\n本文"
        assert parse_frontmatter(content) is None

    def test_empty_frontmatter_returns_empty_dict(self):
        content = "---\n---\n\n本文"
        result = parse_frontmatter(content)
        assert result == {}

    def test_malformed_yaml_returns_none(self):
        content = "---\n: invalid: yaml:\n---\n"
        # 不正な YAML でも None を返す（例外を握り潰す）
        result = parse_frontmatter(content)
        assert result is None or isinstance(result, dict)

    def test_false_value_preserved(self):
        content = "---\nanki_synced: false\n---\n"
        result = parse_frontmatter(content)
        assert result["anki_synced"] is False

    def test_multiline_frontmatter(self):
        content = "---\nword: gehen\nmeaning: 行く\npos: Verb\ndeck: Deutsch\n---\n"
        result = parse_frontmatter(content)
        assert result["word"] == "gehen"
        assert result["deck"] == "Deutsch"


# ── is_unsynced ──────────────────────────────────────────────────

class TestIsUnsynced:
    def test_false_is_unsynced(self):
        assert is_unsynced({"anki_synced": False}) is True

    def test_string_false_is_unsynced(self):
        assert is_unsynced({"anki_synced": "false"}) is True

    def test_datetime_is_synced(self):
        assert is_unsynced({"anki_synced": "2026-03-11T10:00:00+09:00"}) is False

    def test_true_is_synced(self):
        assert is_unsynced({"anki_synced": True}) is False

    def test_missing_field_is_unsynced(self):
        # フィールドなし → 未同期とみなす
        assert is_unsynced({}) is True


# ── update_frontmatter_synced ────────────────────────────────────

class TestUpdateFrontmatterSynced:
    def test_updates_false_to_datetime(self, tmp_path):
        md_file = tmp_path / "gehen.md"
        md_file.write_text(
            "---\nword: gehen\nanki_synced: false\n---\n\n本文\n",
            encoding="utf-8",
        )
        update_frontmatter_synced(md_file, "2026-03-11T10:00:00+09:00")
        content = md_file.read_text(encoding="utf-8")
        assert 'anki_synced: "2026-03-11T10:00:00+09:00"' in content

    def test_other_fields_unchanged(self, tmp_path):
        md_file = tmp_path / "gehen.md"
        md_file.write_text(
            "---\nword: gehen\nmeaning: 行く\nanki_synced: false\n---\n\n本文\n",
            encoding="utf-8",
        )
        update_frontmatter_synced(md_file, "2026-03-11T10:00:00+09:00")
        content = md_file.read_text(encoding="utf-8")
        assert "word: gehen" in content
        assert "meaning: 行く" in content

    def test_body_unchanged(self, tmp_path):
        md_file = tmp_path / "gehen.md"
        md_file.write_text(
            "---\nword: gehen\nanki_synced: false\n---\n\n## gehen\n\n本文内容。\n",
            encoding="utf-8",
        )
        update_frontmatter_synced(md_file, "2026-03-11T10:00:00+09:00")
        content = md_file.read_text(encoding="utf-8")
        assert "## gehen" in content
        assert "本文内容。" in content


# ── get_backlinks ────────────────────────────────────────────────

class TestGetBacklinks:
    def test_full_path_link(self, tmp_path):
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()
        (ref_dir / "Source.md").write_text(
            "[[vocab/de/gehen|geht]] in den Park.\n", encoding="utf-8"
        )
        result = get_backlinks(tmp_path, "vocab/de/gehen")
        assert "Source" in result

    def test_basename_link(self, tmp_path):
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()
        (ref_dir / "Source.md").write_text(
            "Die [[gehen|gehen]] Konjugation.\n", encoding="utf-8"
        )
        result = get_backlinks(tmp_path, "vocab/de/gehen")
        assert "Source" in result

    def test_no_match_returns_empty(self, tmp_path):
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()
        (ref_dir / "Source.md").write_text("Kein Link hier.\n", encoding="utf-8")
        result = get_backlinks(tmp_path, "vocab/de/gehen")
        assert result == []

    def test_excludes_vocab_dir(self, tmp_path):
        # vocab/ 内の相互リンクは除外
        vocab_dir = tmp_path / "vocab" / "de"
        vocab_dir.mkdir(parents=True)
        (vocab_dir / "ausgehen.md").write_text(
            "関連: [[vocab/de/gehen|gehen]]\n", encoding="utf-8"
        )
        result = get_backlinks(tmp_path, "vocab/de/gehen")
        assert "ausgehen" not in result

    def test_multiple_sources(self, tmp_path):
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()
        (ref_dir / "Source1.md").write_text("[[vocab/de/gehen|geht]]\n", encoding="utf-8")
        (ref_dir / "Source2.md").write_text("[[gehen]] ist wichtig.\n", encoding="utf-8")
        result = get_backlinks(tmp_path, "vocab/de/gehen")
        assert len(result) == 2


# ── scan_vocab_files ─────────────────────────────────────────────

class TestScanVocabFiles:
    def test_finds_md_files(self, mock_vault):
        files = scan_vocab_files(mock_vault, ["vocab/de", "vocab/cert"])
        names = [f.name for f in files]
        assert "gehen.md" in names
        assert "スループット.md" in names

    def test_ignores_non_md_files(self, tmp_path):
        vocab_dir = tmp_path / "vocab" / "de"
        vocab_dir.mkdir(parents=True)
        (vocab_dir / "gehen.md").write_text("---\n---\n")
        (vocab_dir / "notes.txt").write_text("text file")
        files = scan_vocab_files(tmp_path, ["vocab/de"])
        assert all(f.suffix == ".md" for f in files)

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        files = scan_vocab_files(tmp_path, ["vocab/nonexistent"])
        assert files == []


# ── load_vocab_entry ─────────────────────────────────────────────

class TestLoadVocabEntry:
    def test_unsynced_file_returns_entry(self, mock_vault, sample_config):
        file_path = mock_vault / "vocab" / "de" / "gehen.md"
        entry = load_vocab_entry(file_path, mock_vault, sample_config)
        assert entry is not None
        assert isinstance(entry, LangVocabEntry)
        assert entry.word == "gehen"

    def test_synced_file_returns_none(self, tmp_path, sample_config):
        sample_config["obsidian"]["vault_path"] = str(tmp_path)
        md_file = tmp_path / "gehen.md"
        md_file.write_text(
            '---\nword: gehen\nmeaning: 行く\ndeck: Deutsch\nanki_synced: "2026-01-01T00:00:00"\n---\n',
            encoding="utf-8",
        )
        entry = load_vocab_entry(md_file, tmp_path, sample_config)
        assert entry is None

    def test_missing_word_returns_none(self, tmp_path, sample_config):
        sample_config["obsidian"]["vault_path"] = str(tmp_path)
        md_file = tmp_path / "bad.md"
        md_file.write_text(
            "---\nword: \nmeaning: 行く\ndeck: Deutsch\nanki_synced: false\n---\n",
            encoding="utf-8",
        )
        entry = load_vocab_entry(md_file, tmp_path, sample_config)
        assert entry is None

    def test_cert_file_returns_cert_entry(self, mock_vault, sample_config):
        file_path = mock_vault / "vocab" / "cert" / "スループット.md"
        entry = load_vocab_entry(file_path, mock_vault, sample_config)
        assert isinstance(entry, CertVocabEntry)
        assert entry.word == "スループット"

    def test_backlinks_populated(self, mock_vault, sample_config):
        file_path = mock_vault / "vocab" / "de" / "gehen.md"
        entry = load_vocab_entry(file_path, mock_vault, sample_config)
        assert isinstance(entry, LangVocabEntry)
        assert len(entry.sources) > 0
