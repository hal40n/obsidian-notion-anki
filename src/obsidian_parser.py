"""Obsidian vault パーサー: frontmatter 読み取り・Backlinks 取得・ファイルスキャン"""

import re
from pathlib import Path

import yaml

from src.models import VocabEntry, parse_entry


def parse_frontmatter(content: str) -> dict | None:
    """Markdown ファイルの先頭 YAML frontmatter をパースする。

    Args:
        content: Markdown ファイルの全文字列。

    Returns:
        パース済みの frontmatter 辞書。frontmatter がない場合や
        YAML パースエラーの場合は None。
    """
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    yaml_str = content[3:end].strip()
    try:
        result = yaml.safe_load(yaml_str)
        return result if isinstance(result, dict) else ({} if result is None else None)
    except yaml.YAMLError:
        return None


def is_unsynced(frontmatter: dict) -> bool:
    """anki_synced フィールドが未同期（false）かどうかを返す。

    Args:
        frontmatter: Obsidianファイルのfrontmatter辞書。

    Returns:
        anki_synced が false または "false" の場合に True。
    """
    value = frontmatter.get("anki_synced", False)
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return value.lower() == "false"
    return False


def update_frontmatter_synced(file_path: Path, iso_datetime: str) -> None:
    """frontmatter の anki_synced フィールドを指定日時に書き換える（最小差分）。

    Args:
        file_path: 更新対象の Markdown ファイルパス。
        iso_datetime: 書き込む ISO 8601 形式の日時文字列。
    """
    content = file_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^(anki_synced:\s*)(false|False|true|True|\"[^\"]*\")(.*)$",
        re.MULTILINE,
    )
    new_content = pattern.sub(
        lambda m: f'{m.group(1)}"{iso_datetime}"{m.group(3)}',
        content,
    )
    file_path.write_text(new_content, encoding="utf-8")


def get_backlinks(vault_path: Path, target_rel_path: str) -> list[str]:
    """Vault 内を検索し、target_rel_path へのリンクを持つノートのファイル名を返す。

    vocab/ ディレクトリ内のファイルは除外する（相互リンクを Sources に含めない）。

    Args:
        vault_path: Obsidian vault のルートパス。
        target_rel_path: 検索対象ノートの vault ルートからの相対パス（拡張子なし）。

    Returns:
        バックリンク元ノートのファイル名（拡張子なし）のリスト。
    """
    basename = Path(target_rel_path).stem
    patterns = [
        re.compile(rf"\[\[{re.escape(target_rel_path)}(\|[^\]]+)?\]\]"),
        re.compile(rf"\[\[{re.escape(basename)}(\|[^\]]+)?\]\]"),
    ]
    backlinks: list[str] = []

    for md_file in vault_path.rglob("*.md"):
        # vocab/ ディレクトリ内は除外
        try:
            rel = md_file.relative_to(vault_path)
        except ValueError:
            continue
        if rel.parts[0] == "vocab":
            continue

        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        for pattern in patterns:
            if pattern.search(text):
                backlinks.append(md_file.stem)
                break

    return backlinks


def scan_vocab_files(vault_path: Path, vocab_dirs: list[str]) -> list[Path]:
    """vocab_dirs 内の .md ファイルを全件収集する。

    Args:
        vault_path: Obsidian vault のルートパス。
        vocab_dirs: スキャン対象のディレクトリ名リスト（vault ルートからの相対パス）。

    Returns:
        収集した .md ファイルのパスリスト。
    """
    files: list[Path] = []
    for vocab_dir in vocab_dirs:
        dir_path = vault_path / vocab_dir
        if not dir_path.exists():
            continue
        files.extend(dir_path.rglob("*.md"))
    return files


def load_vocab_entry(
    file_path: Path,
    vault_path: Path,
    config: dict,
) -> VocabEntry | None:
    """ファイルを読んで VocabEntry を返す。

    以下の場合は None を返す:
    - ファイル読み込みエラー
    - frontmatter が存在しない
    - anki_synced が false でない（同期済み）
    - バリデーション失敗

    Args:
        file_path: 読み込む Markdown ファイルのパス。
        vault_path: Obsidian vault のルートパス（バックリンク取得に使用）。
        config: アプリケーション設定辞書。

    Returns:
        生成した VocabEntry。処理をスキップする場合は None。
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ⚠️  ファイル読み込みエラー: {file_path} — {e}")
        return None

    frontmatter = parse_frontmatter(content)
    if frontmatter is None:
        return None

    if not is_unsynced(frontmatter):
        return None

    # Backlinks（vocab/ からの相対パスを渡す）
    try:
        rel_path = file_path.relative_to(vault_path)
        sources = get_backlinks(vault_path, str(rel_path).replace("\\", "/").removesuffix(".md"))
    except ValueError:
        sources = []

    entry = parse_entry(frontmatter, file_path, sources, config)
    if entry is None:
        print(f"  ⚠️  バリデーションエラー: {file_path.name} をスキップ")
    return entry
