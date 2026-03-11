"""src/models.py のユニットテスト"""

import pytest
from pathlib import Path

from src.models import LangVocabEntry, CertVocabEntry, parse_entry, is_cert_deck


@pytest.fixture
def lang_path(tmp_path):
    return tmp_path / "gehen.md"


@pytest.fixture
def cert_path(tmp_path):
    return tmp_path / "スループット.md"


@pytest.fixture
def config():
    return {
        "note_types": {
            "Deutsch": "SentenceVocab_DE",
            "English": "SentenceVocab_EN",
            "応用情報技術者": "TermDefinition",
        }
    }


# ── LangVocabEntry ──────────────────────────────────────────────

class TestLangVocabEntry:
    def test_valid_entry_has_no_errors(self, lang_path):
        entry = LangVocabEntry(word="gehen", meaning="行く", deck="Deutsch", file_path=lang_path)
        assert entry.validate() == []

    def test_missing_word_returns_error(self, lang_path):
        entry = LangVocabEntry(word="", meaning="行く", deck="Deutsch", file_path=lang_path)
        errors = entry.validate()
        assert any("word" in e for e in errors)

    def test_missing_meaning_returns_error(self, lang_path):
        entry = LangVocabEntry(word="gehen", meaning="", deck="Deutsch", file_path=lang_path)
        errors = entry.validate()
        assert any("meaning" in e for e in errors)

    def test_missing_deck_returns_error(self, lang_path):
        entry = LangVocabEntry(word="gehen", meaning="行く", deck="", file_path=lang_path)
        errors = entry.validate()
        assert any("deck" in e for e in errors)

    def test_optional_fields_default_to_empty(self, lang_path):
        entry = LangVocabEntry(word="gehen", meaning="行く", deck="Deutsch", file_path=lang_path)
        assert entry.pos == ""
        assert entry.example == ""
        assert entry.sources == []

    def test_is_frozen(self, lang_path):
        entry = LangVocabEntry(word="gehen", meaning="行く", deck="Deutsch", file_path=lang_path)
        with pytest.raises((AttributeError, TypeError)):
            entry.word = "changed"  # type: ignore


# ── CertVocabEntry ──────────────────────────────────────────────

class TestCertVocabEntry:
    def test_valid_entry_has_no_errors(self, cert_path):
        entry = CertVocabEntry(word="スループット", meaning="定義", deck="応用情報技術者", file_path=cert_path)
        assert entry.validate() == []

    def test_missing_word_returns_error(self, cert_path):
        entry = CertVocabEntry(word="", meaning="定義", deck="応用情報技術者", file_path=cert_path)
        errors = entry.validate()
        assert any("word" in e for e in errors)

    def test_missing_meaning_returns_error(self, cert_path):
        entry = CertVocabEntry(word="スループット", meaning="", deck="応用情報技術者", file_path=cert_path)
        errors = entry.validate()
        assert any("meaning" in e for e in errors)

    def test_missing_deck_returns_error(self, cert_path):
        entry = CertVocabEntry(word="スループット", meaning="定義", deck="", file_path=cert_path)
        errors = entry.validate()
        assert any("deck" in e for e in errors)

    def test_is_frozen(self, cert_path):
        entry = CertVocabEntry(word="スループット", meaning="定義", deck="応用情報技術者", file_path=cert_path)
        with pytest.raises((AttributeError, TypeError)):
            entry.word = "changed"  # type: ignore


# ── is_cert_deck ────────────────────────────────────────────────

class TestIsCertDeck:
    def test_sentence_vocab_is_not_cert(self, config):
        assert is_cert_deck("Deutsch", config) is False

    def test_term_definition_is_cert(self, config):
        assert is_cert_deck("応用情報技術者", config) is True

    def test_unknown_deck_returns_false(self, config):
        assert is_cert_deck("Unknown", config) is False


# ── parse_entry ─────────────────────────────────────────────────

class TestParseEntry:
    def test_lang_frontmatter_returns_lang_entry(self, lang_path, config):
        fm = {
            "word": "gehen",
            "meaning": "行く",
            "deck": "Deutsch",
            "lang": "de",
        }
        entry = parse_entry(fm, lang_path, ["source1"], config)
        assert isinstance(entry, LangVocabEntry)
        assert entry.word == "gehen"
        assert entry.sources == ["source1"]

    def test_cert_frontmatter_returns_cert_entry(self, cert_path, config):
        fm = {
            "word": "スループット",
            "meaning": "定義",
            "deck": "応用情報技術者",
            "category": "ネットワーク",
        }
        entry = parse_entry(fm, cert_path, [], config)
        assert isinstance(entry, CertVocabEntry)
        assert entry.category == "ネットワーク"

    def test_missing_word_returns_none(self, lang_path, config):
        fm = {"word": "", "meaning": "行く", "deck": "Deutsch"}
        assert parse_entry(fm, lang_path, [], config) is None

    def test_missing_deck_returns_none(self, lang_path, config):
        fm = {"word": "gehen", "meaning": "行く", "deck": ""}
        assert parse_entry(fm, lang_path, [], config) is None
