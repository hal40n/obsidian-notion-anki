"""VocabEntry データモデル"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LangVocabEntry:
    """言語学習用語彙エントリ（イミュータブル）。

    Attributes:
        word: 単語。
        meaning: 意味・訳。
        deck: Ankiデッキ名 / Notion DB キー。
        file_path: 元Obsidianファイルのパス。
        pos: 品詞。
        example: 例文（<<word>>マーカー付き）。
        example_translation: 例文の日本語訳。
        usage: 語法・コロケーション。
        lang: 言語コード（de, en）。
        sources: 出典ノート名のリスト。
        anki_synced: 同期状態。False=未同期、ISO日時文字列=同期済み。
    """

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
        """バリデーションを実行し、エラーメッセージのリストを返す。

        Returns:
            エラーメッセージのリスト。空リストの場合は正常。
        """
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
    """資格学習用語彙エントリ（イミュータブル）。

    Attributes:
        word: 用語名。
        meaning: 定義・説明。
        deck: Ankiデッキ名 / Notion DB キー。
        file_path: 元Obsidianファイルのパス。
        category: 分野カテゴリ（例: ネットワーク）。
        anki_synced: 同期状態。False=未同期、ISO日時文字列=同期済み。
    """

    word: str
    meaning: str
    deck: str
    file_path: Path
    category: str = ""
    anki_synced: bool | str = False

    def validate(self) -> list[str]:
        """バリデーションを実行し、エラーメッセージのリストを返す。

        Returns:
            エラーメッセージのリスト。空リストの場合は正常。
        """
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
    """note_types 設定から資格学習デッキかどうかを判定する。

    Args:
        deck: デッキ名。
        config: アプリケーション設定辞書。

    Returns:
        TermDefinition ノートタイプのデッキであれば True。
    """
    note_type = config.get("note_types", {}).get(deck, "")
    return note_type == "TermDefinition"


def parse_entry(
    frontmatter: dict,
    file_path: Path,
    sources: list[str],
    config: dict,
) -> VocabEntry | None:
    """frontmatter dict から適切な VocabEntry を生成する。

    Args:
        frontmatter: Obsidianファイルのfrontmatter辞書。
        file_path: 元Obsidianファイルのパス。
        sources: バックリンク元のノート名リスト。
        config: アプリケーション設定辞書。

    Returns:
        生成した VocabEntry。バリデーション失敗時は None。
    """
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
