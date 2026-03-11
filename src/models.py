"""VocabEntry データモデル"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LangVocabEntry:
    """言語学習用語彙エントリ（イミュータブル）"""

    word: str
    meaning: str
    deck: str
    file_path: Path
    pos: str = ""
    example: str = ""
    example_translation: str = ""
    usage: str = ""
    lang: str = ""
    sources: list[str] = field(default_factory=list)
    anki_synced: bool | str = False

    def validate(self) -> list[str]:
        """バリデーションエラーのリストを返す（空リスト = 正常）。"""
        errors = []
        if not self.word:
            errors.append("word は必須です")
        if not self.meaning:
            errors.append("meaning は必須です")
        if not self.deck:
            errors.append("deck は必須です")
        return errors


@dataclass(frozen=True)
class CertVocabEntry:
    """資格学習用語彙エントリ（イミュータブル）"""

    word: str
    meaning: str
    deck: str
    file_path: Path
    category: str = ""
    anki_synced: bool | str = False

    def validate(self) -> list[str]:
        """バリデーションエラーのリストを返す（空リスト = 正常）。"""
        errors = []
        if not self.word:
            errors.append("word は必須です")
        if not self.meaning:
            errors.append("meaning は必須です")
        if not self.deck:
            errors.append("deck は必須です")
        return errors


VocabEntry = LangVocabEntry | CertVocabEntry


def is_cert_deck(deck: str, config: dict) -> bool:
    """note_types 設定から資格学習デッキかどうかを判定する。"""
    note_type = config.get("note_types", {}).get(deck, "")
    return note_type == "TermDefinition"


def parse_entry(
    frontmatter: dict,
    file_path: Path,
    sources: list[str],
    config: dict,
) -> VocabEntry | None:
    """frontmatter dict から適切な VocabEntry を生成する。バリデーション失敗時は None。"""
    deck = str(frontmatter.get("deck", ""))
    word = str(frontmatter.get("word", "") or "")
    meaning = str(frontmatter.get("meaning", "") or "")

    if is_cert_deck(deck, config):
        entry: VocabEntry = CertVocabEntry(
            word=word,
            meaning=meaning,
            deck=deck,
            file_path=file_path,
            category=str(frontmatter.get("category", "") or ""),
            anki_synced=frontmatter.get("anki_synced", False),
        )
    else:
        entry = LangVocabEntry(
            word=word,
            meaning=meaning,
            deck=deck,
            file_path=file_path,
            pos=str(frontmatter.get("pos", "") or ""),
            example=str(frontmatter.get("example", "") or ""),
            example_translation=str(frontmatter.get("example_translation", "") or ""),
            usage=str(frontmatter.get("usage", "") or ""),
            lang=str(frontmatter.get("lang", "") or ""),
            sources=list(sources),
            anki_synced=frontmatter.get("anki_synced", False),
        )

    errors = entry.validate()
    if errors:
        return None
    return entry
