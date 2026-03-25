"""src/note_builder.py のユニットテスト"""

import pytest

from src.note_builder import build_anki_note, convert_markers


@pytest.fixture
def config():
    return {
        "note_types": {
            "Deutsch": "SentenceVocab_DE",
            "English": "SentenceVocab_EN",
            "応用情報技術者": "TermDefinition",
        }
    }


# ── convert_markers ──────────────────────────────────────────────


class TestConvertMarkers:
    def test_marker_converted_to_span(self):
        result = convert_markers("Ich <<gehe>> in den Park.")
        assert '<span class="hl">gehe</span>' in result

    def test_no_marker_no_word_unchanged(self):
        result = convert_markers("Ich gehe in den Park.")
        assert result == "Ich gehe in den Park."

    def test_fallback_with_word(self):
        result = convert_markers("Ich gehe in den Park.", word="gehe")
        assert '<span class="hl">gehe</span>' in result

    def test_empty_string_returns_empty(self):
        assert convert_markers("") == ""
        assert convert_markers("", word="gehen") == ""

    def test_marker_takes_priority_over_fallback(self):
        result = convert_markers("Ich <<gehe>> gehe.", word="gehe")
        # マーカーで1つだけ変換される
        assert result.count('<span class="hl">') == 1
        assert "<<" not in result

    def test_fallback_replaces_first_occurrence_only(self):
        result = convert_markers("gehe oder gehe", word="gehe")
        assert result.count('<span class="hl">') == 1


# ── build_anki_note ──────────────────────────────────────────────


class TestBuildAnkiNote:
    def _lang_entry(self):
        return {
            "word": "gehen",
            "meaning": "行く",
            "pos": "Verb",
            "example": "Ich <<gehe>> in den Park.",
            "example_translation": "私は公園へ行く。",
            "usage": "gehen + Richtung",
            "sources": "Deutsch perfekt",
            "language": "de_DE",
        }

    def _cert_entry(self):
        return {
            "word": "スループット",
            "meaning": "単位時間あたりのデータ量。",
            "category": "ネットワーク",
        }

    def test_sentence_vocab_de_fields(self, config):
        note = build_anki_note(self._lang_entry(), "Deutsch", config)
        assert note["modelName"] == "SentenceVocab_DE"
        assert note["deckName"] == "Deutsch"
        assert note["fields"]["Word"] == "gehen"
        assert '<span class="hl">gehe</span>' in note["fields"]["Sentence"]

    def test_sentence_vocab_en_fields(self, config):
        entry = {**self._lang_entry(), "sources": "BBC"}
        note = build_anki_note(entry, "English", config)
        assert note["modelName"] == "SentenceVocab_EN"

    def test_term_definition_fields(self, config):
        note = build_anki_note(self._cert_entry(), "応用情報技術者", config)
        assert note["modelName"] == "TermDefinition"
        assert note["fields"]["Term"] == "スループット"
        assert note["fields"]["Definition"] == "単位時間あたりのデータ量。"

    def test_tags_from_sources(self, config):
        entry = {**self._lang_entry(), "sources": "Source A, Source B"}
        note = build_anki_note(entry, "Deutsch", config)
        assert "Source_A" in note["tags"]
        assert "Source_B" in note["tags"]

    def test_term_definition_tags_from_category(self, config):
        note = build_anki_note(self._cert_entry(), "応用情報技術者", config)
        assert "ネットワーク" in note["tags"]

    def test_unknown_note_type_raises(self, config):
        config["note_types"]["Unknown"] = "UnknownType"
        with pytest.raises(ValueError):
            build_anki_note(self._lang_entry(), "Unknown", config)
