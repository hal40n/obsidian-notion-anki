"""Anki ノート構築・マーカー変換"""

import re


def convert_markers(example: str, word: str = "") -> str:
    """例文中の <<word>> マーカーを HTML highlight に変換する。

    マーカーがない場合、word で部分一致を試みる（フォールバック）。
    """
    if not example:
        return ""

    if "<<" in example and ">>" in example:
        return re.sub(r"<<(.+?)>>", r'<span class="hl">\1</span>', example)

    if word:
        pattern = re.compile(re.escape(word))
        if pattern.search(example):
            return pattern.sub(f'<span class="hl">{word}</span>', example, count=1)

    return example


def _build_sentence_vocab_note(entry: dict, deck: str, note_type: str) -> dict:
    sentence_html = convert_markers(entry.get("example", ""), entry.get("word", ""))
    return {
        "deckName": deck,
        "modelName": note_type,
        "fields": {
            "Word": entry.get("word", ""),
            "Sentence": sentence_html,
            "ExampleTranslation": entry.get("example_translation", ""),
            "Meaning": entry.get("meaning", ""),
            "PartOfSpeech": entry.get("pos", ""),
            "Usage": entry.get("usage", ""),
            "Source": entry.get("sources", ""),
            "Language": entry.get("language", ""),
        },
        "tags": [
            s.strip().replace(" ", "_")
            for s in entry.get("sources", "").split(",")
            if s.strip()
        ],
    }


def _build_term_definition_note(entry: dict, deck: str) -> dict:
    return {
        "deckName": deck,
        "modelName": "TermDefinition",
        "fields": {
            "Term": entry.get("word", ""),
            "Definition": entry.get("meaning", ""),
            "Category": entry.get("category", ""),
        },
        "tags": [entry.get("category", "").replace(" ", "_")],
    }


def build_anki_note(entry: dict, deck: str, config: dict) -> dict:
    """エントリから AnkiConnect 用の note dict を構築する。"""
    note_type = config["note_types"][deck]

    if note_type.startswith("SentenceVocab"):
        return _build_sentence_vocab_note(entry, deck, note_type)
    if note_type == "TermDefinition":
        return _build_term_definition_note(entry, deck)

    raise ValueError(f"未知のノートタイプ: {note_type}")
