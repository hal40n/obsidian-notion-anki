"""word/ ディレクトリのファイルパーサー

word/*.md を読み込み、LangVocabEntry に変換する。
資格学習用デッキ（CertVocabEntry）は対象外。
"""

from pathlib import Path

import yaml

from src.models import LangVocabEntry, parse_entry


def _parse_frontmatter(content: str) -> dict | None:
    """Markdown コンテンツから frontmatter を抽出する。

    Args:
        content: Markdown ファイルの全文。

    Returns:
        frontmatter 辞書。frontmatter がない場合は None。
    """
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None


def scan_word_files(word_dir: Path) -> list[Path]:
    """word/ ディレクトリの .md ファイルを返す。

    Args:
        word_dir: スキャン対象ディレクトリ。

    Returns:
        .md ファイルのパスリスト（ソート済み）。存在しない場合は空リスト。
    """
    if not word_dir.exists():
        return []
    return sorted(word_dir.glob("*.md"))


def parse_word_file(file_path: Path, config: dict) -> LangVocabEntry | None:
    """word/*.md を LangVocabEntry に変換する。

    Args:
        file_path: word/*.md ファイルパス。
        config: アプリケーション設定辞書。

    Returns:
        LangVocabEntry。frontmatter 不正・必須フィールド欠如・
        資格学習デッキの場合は None。
    """
    content = file_path.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(content)
    if frontmatter is None:
        return None

    entry = parse_entry(
        frontmatter=frontmatter,
        file_path=file_path,
        sources=[],
        config=config,
    )
    if not isinstance(entry, LangVocabEntry):
        return None
    return entry
