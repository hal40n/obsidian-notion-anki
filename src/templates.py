"""Anki カード CSS + HTML テンプレート（設計書 v4 準拠）"""

SHARED_CSS = """\
/* ============================
   Vocabulary Card Styles
   設計書 v4 準拠
   ============================ */

.card {
  font-family: "Noto Sans JP", "Noto Sans", "Helvetica Neue", sans-serif;
  font-size: 18px;
  text-align: left;
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
  line-height: 1.7;
  color: #2d3748;
  background: #ffffff;
}

/* ── 例文中の対象語 ── */
.hl {
  color: #e53e3e;
  font-weight: bold;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* ── SentenceVocab ── */
.sentence {
  font-size: 21px;
  margin-bottom: 8px;
  line-height: 1.8;
}

.translation {
  font-size: 15px;
  color: #718096;
  margin-bottom: 16px;
  padding-left: 4px;
  line-height: 1.6;
}

.hint {
  font-size: 13px;
  color: #a0aec0;
  margin-top: 24px;
  text-align: center;
  letter-spacing: 0.05em;
}

.word-header {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
  color: #1a202c;
}

.pos {
  font-size: 14px;
  color: #718096;
  margin-bottom: 10px;
}

.meaning {
  font-size: 18px;
  margin-bottom: 14px;
  line-height: 1.6;
}

.usage {
  font-size: 14px;
  color: #4a5568;
  background: #f7fafc;
  padding: 10px 14px;
  border-left: 3px solid #4299e1;
  border-radius: 0 4px 4px 0;
  margin-bottom: 10px;
  line-height: 1.6;
}

.source {
  font-size: 12px;
  color: #a0aec0;
  margin-top: 20px;
}

/* ── TermDefinition ── */
.term {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  color: #1a202c;
  padding: 20px 0;
}

.definition {
  font-size: 18px;
  line-height: 1.7;
}

.category {
  font-size: 12px;
  color: #a0aec0;
  margin-top: 20px;
}

/* ── 共通 ── */
hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 16px 0;
}

/* ── ナイトモード ── */
.nightMode .card {
  background: #1a202c;
  color: #e2e8f0;
}

.nightMode .hl {
  color: #fc8181;
}

.nightMode .word-header,
.nightMode .term {
  color: #f7fafc;
}

.nightMode .translation {
  color: #a0aec0;
}

.nightMode .usage {
  background: #2d3748;
  border-left-color: #63b3ed;
  color: #cbd5e0;
}

.nightMode .pos {
  color: #a0aec0;
}

.nightMode hr {
  border-top-color: #4a5568;
}
"""

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
