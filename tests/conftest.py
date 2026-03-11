"""pytest 共通フィクスチャ"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_lang_frontmatter() -> dict:
    return {
        "word": "gehen",
        "meaning": "行く、歩く",
        "pos": "Verb (unregelmäßig)",
        "example": "Ich <<gehe>> jeden Morgen in den Park.",
        "example_translation": "私は毎朝公園へ行く。",
        "usage": "gehen + Richtung",
        "deck": "Deutsch",
        "lang": "de",
        "anki_synced": False,
    }


@pytest.fixture
def sample_cert_frontmatter() -> dict:
    return {
        "word": "スループット",
        "meaning": "単位時間あたりに処理できるデータ量。",
        "category": "ネットワーク",
        "deck": "応用情報技術者",
        "anki_synced": False,
    }


@pytest.fixture
def sample_config(mock_vault) -> dict:
    return {
        "databases": {
            "Deutsch": "31e33e92-6b73-807c-ab95-ca196f3dfd3b",
            "応用情報技術者": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        },
        "note_types": {
            "Deutsch": "SentenceVocab_DE",
            "応用情報技術者": "TermDefinition",
        },
        "obsidian": {
            "vault_path": str(mock_vault),
            "vocab_dirs": ["vocab/de", "vocab/cert"],
        },
        "notion_api_key": "ntn_test_key",
    }


@pytest.fixture
def mock_vault(tmp_path: Path) -> Path:
    """仮想 Vault 構造を作成する。"""
    # vocab/de/gehen.md
    de_dir = tmp_path / "vocab" / "de"
    de_dir.mkdir(parents=True)
    (de_dir / "gehen.md").write_text(
        "---\n"
        "word: gehen\n"
        "meaning: 行く、歩く\n"
        "pos: Verb (unregelmäßig)\n"
        "example: Ich <<gehe>> jeden Morgen in den Park.\n"
        "example_translation: 私は毎朝公園へ行く。\n"
        "usage: gehen + Richtung\n"
        "deck: Deutsch\n"
        "lang: de\n"
        "anki_synced: false\n"
        "---\n\n"
        "## gehen\n\n"
        "本文内容。\n",
        encoding="utf-8",
    )
    (de_dir / "Entscheidung.md").write_text(
        "---\n"
        "word: Entscheidung\n"
        "meaning: 決断\n"
        "deck: Deutsch\n"
        "anki_synced: false\n"
        "---\n\n"
        "## Entscheidung\n",
        encoding="utf-8",
    )
    # vocab/cert/スループット.md
    cert_dir = tmp_path / "vocab" / "cert"
    cert_dir.mkdir(parents=True)
    (cert_dir / "スループット.md").write_text(
        "---\n"
        "word: スループット\n"
        "meaning: 単位時間あたりに処理できるデータ量。\n"
        "category: ネットワーク\n"
        "deck: 応用情報技術者\n"
        "anki_synced: false\n"
        "---\n\n"
        "## スループット\n",
        encoding="utf-8",
    )
    # reference/sample.md（gehen へのバックリンクあり）
    ref_dir = tmp_path / "reference"
    ref_dir.mkdir()
    (ref_dir / "Deutsch perfekt März 2026.md").write_text(
        "---\ntitle: test\n---\n\n"
        "Er [[vocab/de/gehen|geht]] in den Park.\n"
        "Die [[Entscheidung]] war wichtig.\n",
        encoding="utf-8",
    )
    return tmp_path
