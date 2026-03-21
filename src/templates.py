"""Anki カード CSS + HTML テンプレート（設計書 v4 準拠）"""

from pathlib import Path

SHARED_CSS = (Path(__file__).parent / "card.css").read_text(encoding="utf-8")

SENTENCE_VOCAB_FIELDS = [
    "Word",
    "Sentence",
    "ExampleTranslation",
    "Meaning",
    "PartOfSpeech",
    "Usage",
    "Source",
    "Language",
]


def sentence_vocab_front(tts_lang: str) -> str:
    return f"""\
{{{{tts {tts_lang}:Sentence}}}}
<div class="card front">
  <div class="sentence">{{{{Sentence}}}}</div>
  <div class="hint">強調された語の意味と語法は？</div>
</div>"""


def sentence_vocab_back(tts_lang: str) -> str:
    return f"""\
{{{{tts {tts_lang}:Sentence}}}}
<div class="card back">
  <div class="sentence">{{{{Sentence}}}}</div>
  {{{{#ExampleTranslation}}}}
  <div class="translation">{{{{ExampleTranslation}}}}</div>
  {{{{/ExampleTranslation}}}}
  <hr>
  <div class="word-header">{{{{Word}}}}</div>
  {{{{#PartOfSpeech}}}}
  <div class="pos">〔{{{{PartOfSpeech}}}}〕</div>
  {{{{/PartOfSpeech}}}}
  <div class="meaning">{{{{Meaning}}}}</div>
  {{{{#Usage}}}}
  <div class="usage">📝 {{{{Usage}}}}</div>
  {{{{/Usage}}}}
  {{{{#Source}}}}
  <div class="source">📖 {{{{Source}}}}</div>
  {{{{/Source}}}}
</div>"""


TERM_DEFINITION_FIELDS = ["Term", "Definition", "Category"]

TERM_DEFINITION_FRONT = """\
<div class="card front">
  <div class="term">{{Term}}</div>
</div>"""

TERM_DEFINITION_BACK = """\
<div class="card back">
  <div class="term">{{Term}}</div>
  <hr>
  <div class="definition">{{Definition}}</div>
  {{#Category}}
  <div class="category">📁 {{Category}}</div>
  {{/Category}}
</div>"""

NOTE_TYPES = [
    {
        "name": "SentenceVocab_DE",
        "fields": SENTENCE_VOCAB_FIELDS,
        "front": sentence_vocab_front("de_DE"),
        "back": sentence_vocab_back("de_DE"),
        "css": SHARED_CSS,
        "deck": "Deutsch",
        "description": "ドイツ語 例文ベースカード（TTS: de_DE）",
    },
    {
        "name": "SentenceVocab_EN",
        "fields": SENTENCE_VOCAB_FIELDS,
        "front": sentence_vocab_front("en_US"),
        "back": sentence_vocab_back("en_US"),
        "css": SHARED_CSS,
        "deck": "English",
        "description": "英語 例文ベースカード（TTS: en_US）",
    },
    {
        "name": "TermDefinition",
        "fields": TERM_DEFINITION_FIELDS,
        "front": TERM_DEFINITION_FRONT,
        "back": TERM_DEFINITION_BACK,
        "css": SHARED_CSS,
        "deck": "Certifications",
        "description": "資格学習 用語→定義カード",
    },
]
