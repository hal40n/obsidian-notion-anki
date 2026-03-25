"""src/config.py のユニットテスト（純粋関数のみ）"""

from pathlib import Path

import pytest
import yaml

from src.config import _expand_env_vars, _normalize_db_id, load_config


class TestExpandEnvVars:
    def test_expands_env_var(self, monkeypatch):
        monkeypatch.setenv("MY_DB_ID", "abc123")
        result = _expand_env_vars("${MY_DB_ID}")
        assert result == "abc123"

    def test_leaves_unset_var_as_is(self, monkeypatch):
        monkeypatch.delenv("UNSET_VAR", raising=False)
        result = _expand_env_vars("${UNSET_VAR}")
        assert result == "${UNSET_VAR}"

    def test_expands_in_dict(self, monkeypatch):
        monkeypatch.setenv("DB", "db-id")
        result = _expand_env_vars({"key": "${DB}"})
        assert result == {"key": "db-id"}

    def test_expands_in_list(self, monkeypatch):
        monkeypatch.setenv("DB", "db-id")
        result = _expand_env_vars(["${DB}", "plain"])
        assert result == ["db-id", "plain"]

    def test_non_string_passthrough(self):
        assert _expand_env_vars(42) == 42
        assert _expand_env_vars(None) is None


class TestNormalizeDbId:
    def test_32_hex_to_uuid(self):
        raw = "31e33e926b73807cab95ca196f3dfd3b"
        result = _normalize_db_id(raw)
        assert result == "31e33e92-6b73-807c-ab95-ca196f3dfd3b"

    def test_already_hyphenated_passthrough(self):
        uuid = "31e33e92-6b73-807c-ab95-ca196f3dfd3b"
        result = _normalize_db_id(uuid)
        assert result == uuid

    def test_strips_query_string(self):
        raw = "31e33e926b73807cab95ca196f3dfd3b?v=xxx"
        result = _normalize_db_id(raw)
        assert result == "31e33e92-6b73-807c-ab95-ca196f3dfd3b"

    def test_strips_whitespace(self):
        raw = "  31e33e926b73807cab95ca196f3dfd3b  "
        result = _normalize_db_id(raw)
        assert result == "31e33e92-6b73-807c-ab95-ca196f3dfd3b"

    def test_short_id_returned_as_is(self):
        raw = "short-id"
        result = _normalize_db_id(raw)
        assert result == "shortid"


class TestLoadConfig:
    def _setup(self, tmp_path: Path, content: dict, monkeypatch) -> None:
        """SCRIPT_DIR を tmp_path に向け、config.yaml を書き込む。"""
        monkeypatch.setattr("src.config.SCRIPT_DIR", tmp_path)
        cfg = tmp_path / "config.yaml"
        cfg.write_text(yaml.dump(content), encoding="utf-8")

    def test_exits_when_api_key_missing(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        monkeypatch.setattr("src.config.SCRIPT_DIR", tmp_path)
        monkeypatch.setattr("src.config.load_dotenv", lambda *a, **kw: None)
        (tmp_path / "config.yaml").write_text(yaml.dump({"databases": {}}), encoding="utf-8")

        with pytest.raises(SystemExit):
            load_config()

    def test_exits_when_config_yaml_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "ntn_test")
        monkeypatch.setattr("src.config.SCRIPT_DIR", tmp_path)
        # config.yaml を作成しない

        with pytest.raises(SystemExit):
            load_config()

    def test_loads_valid_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "ntn_test")
        monkeypatch.setenv("DEUTSCH_DB", "31e33e926b73807cab95ca196f3dfd3b")
        self._setup(
            tmp_path,
            {
                "databases": {"Deutsch": "${DEUTSCH_DB}"},
                "note_types": {"Deutsch": "SentenceVocab_DE"},
                "obsidian": {"vault_path": str(tmp_path), "vocab_dirs": ["vocab/de"]},
            },
            monkeypatch,
        )

        config = load_config()

        assert config["notion_api_key"] == "ntn_test"
        assert config["databases"]["Deutsch"] == "31e33e92-6b73-807c-ab95-ca196f3dfd3b"
