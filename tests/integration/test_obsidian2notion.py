"""obsidian2notion.py の統合テスト"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call


@pytest.fixture
def mock_notion():
    notion = MagicMock()
    notion.databases.retrieve.return_value = {
        "data_sources": [{"id": "ds-test-id"}]
    }
    notion.data_sources.query.return_value = {"results": []}
    notion.pages.create.return_value = {"id": "new-page-id"}
    return notion


@pytest.fixture
def mock_config(mock_vault):
    return {
        "databases": {
            "Deutsch": "db-deutsch-id",
            "応用情報技術者": "db-cert-id",
        },
        "note_types": {
            "Deutsch": "SentenceVocab_DE",
            "応用情報技術者": "TermDefinition",
        },
        "obsidian": {
            "vault_path": str(mock_vault),
            "vocab_dirs": ["vocab/de", "vocab/cert"],
        },
        "anki": {"url": "http://localhost:8765"},
        "notion_api_key": "ntn_test",
    }


class TestSyncVocabDir:
    def test_creates_new_pages_for_unsynced_entries(
        self, mock_vault, mock_config, mock_notion
    ):
        from obsidian2notion import sync_vocab_dir

        stats = sync_vocab_dir(
            notion=mock_notion,
            vault_path=mock_vault,
            vocab_dir="vocab/de",
            config=mock_config,
            deck_filter=None,
            dry_run=False,
        )

        assert stats["created"] > 0
        assert mock_notion.pages.create.called

    def test_updates_frontmatter_after_sync(self, mock_vault, mock_config, mock_notion):
        from obsidian2notion import sync_vocab_dir

        sync_vocab_dir(
            notion=mock_notion,
            vault_path=mock_vault,
            vocab_dir="vocab/de",
            config=mock_config,
            deck_filter=None,
            dry_run=False,
        )

        gehen_md = (mock_vault / "vocab" / "de" / "gehen.md").read_text(encoding="utf-8")
        assert "anki_synced: false" not in gehen_md
        assert "anki_synced:" in gehen_md

    def test_dry_run_does_not_call_create(self, mock_vault, mock_config, mock_notion):
        from obsidian2notion import sync_vocab_dir

        sync_vocab_dir(
            notion=mock_notion,
            vault_path=mock_vault,
            vocab_dir="vocab/de",
            config=mock_config,
            deck_filter=None,
            dry_run=True,
        )

        mock_notion.pages.create.assert_not_called()

    def test_dry_run_does_not_update_frontmatter(self, mock_vault, mock_config, mock_notion):
        from obsidian2notion import sync_vocab_dir

        sync_vocab_dir(
            notion=mock_notion,
            vault_path=mock_vault,
            vocab_dir="vocab/de",
            config=mock_config,
            deck_filter=None,
            dry_run=True,
        )

        gehen_md = (mock_vault / "vocab" / "de" / "gehen.md").read_text(encoding="utf-8")
        assert "anki_synced: false" in gehen_md

    def test_deck_filter_skips_other_decks(self, mock_vault, mock_config, mock_notion):
        from obsidian2notion import sync_vocab_dir

        stats = sync_vocab_dir(
            notion=mock_notion,
            vault_path=mock_vault,
            vocab_dir="vocab/de",
            config=mock_config,
            deck_filter="English",  # Deutsch には一致しない
            dry_run=False,
        )

        assert stats["created"] == 0
        mock_notion.pages.create.assert_not_called()

    def test_skips_already_synced_entries(self, mock_vault, mock_config, mock_notion):
        from obsidian2notion import sync_vocab_dir

        # gehen.md を同期済みにする
        gehen_md = mock_vault / "vocab" / "de" / "gehen.md"
        content = gehen_md.read_text(encoding="utf-8")
        gehen_md.write_text(
            content.replace("anki_synced: false", 'anki_synced: "2026-01-01T00:00:00"'),
            encoding="utf-8",
        )

        stats = sync_vocab_dir(
            notion=mock_notion,
            vault_path=mock_vault,
            vocab_dir="vocab/de",
            config=mock_config,
            deck_filter=None,
            dry_run=False,
        )

        # Entscheidung のみ処理されるはず
        assert stats["created"] == 1

    def test_updates_page_when_content_changed(self, mock_vault, mock_config, mock_notion):
        from obsidian2notion import sync_vocab_dir

        # 既存ページが存在し、内容が異なる
        mock_notion.data_sources.query.return_value = {
            "results": [
                {
                    "id": "existing-id",
                    "properties": {
                        "Meaning": {"type": "rich_text", "rich_text": [{"plain_text": "古い意味"}]},
                        "Part of Speech": {"type": "select", "select": None},
                        "Example": {"type": "rich_text", "rich_text": []},
                        "Example Translation": {"type": "rich_text", "rich_text": []},
                        "Usage": {"type": "rich_text", "rich_text": []},
                    },
                }
            ]
        }

        stats = sync_vocab_dir(
            notion=mock_notion,
            vault_path=mock_vault,
            vocab_dir="vocab/de",
            config=mock_config,
            deck_filter="Deutsch",
            dry_run=False,
        )

        assert stats["updated"] > 0
        mock_notion.pages.update.assert_called()
