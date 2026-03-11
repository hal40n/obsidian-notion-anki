"""src/config.py のユニットテスト（純粋関数のみ）"""

import pytest
from src.config import _expand_env_vars, _normalize_db_id


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
