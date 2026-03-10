---
name: python-testing
description: pytest によるテスト戦略。TDD・フィクスチャ・モック・パラメタライズ・カバレッジ。本プロジェクト（obsidian-notion-anki）に特化。
origin: ECC
---

# Python テストパターン

本プロジェクト（obsidian-notion-anki）向けの pytest テスト戦略。
パッケージマネージャーは **uv**、タスクランナーは **poethepoet**、Python **3.13** を前提とする。

## 発火条件

- Python コードを新規作成するとき（TDD: 赤 → 緑 → リファクタ）
- テストスイートを設計・レビューするとき
- テストカバレッジを確認するとき
- テスト基盤をセットアップするとき

## TDD ワークフロー

CLAUDE.md の方針に従い、**必ず TDD** で進める。

1. **赤**: 失敗するテストを書く
2. **緑**: テストを通す最小限の実装を書く
3. **リファクタ**: テストが通った状態でコードを改善し、カバレッジ 80% 以上を確認

```python
# 1. 赤 — 失敗するテストを書く
def test_normalize_db_id_strips_view_param():
    assert _normalize_db_id("abc123?v=xyz") == "..."

# 2. 緑 — 最小限の実装
def _normalize_db_id(raw: str) -> str:
    return raw.split("?")[0]

# 3. リファクタ — ハイフン挿入など仕様に合わせて整理
```

### カバレッジ要件

- **目標**: 80% 以上（CLAUDE.md 準拠）
- **クリティカルパス**: 100%（同期ロジック・フィールドマッピング等）

```bash
uv run pytest --cov=. --cov-report=term-missing --cov-report=html
```

## プロジェクト固有のセットアップ

### 依存の追加

```bash
uv add --dev pytest pytest-cov
```

### pyproject.toml に追記

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--cov=.",
    "--cov-report=term-missing",
]
markers = [
    "slow: 低速テスト",
    "integration: 結合テスト（Notion API / AnkiConnect が必要）",
]
```

### poethepoet タスク

```toml
[tool.poe.tasks]
test = { cmd = "pytest", help = "テスト実行" }
test-cov = { cmd = "pytest --cov=. --cov-report=html", help = "カバレッジ付きテスト" }
test-fast = { cmd = "pytest -m 'not slow and not integration'", help = "高速テストのみ" }
```

### ディレクトリ構成

```
tests/
├── conftest.py              # 共通フィクスチャ
├── unit/
│   ├── test_config.py       # load_config, _expand_env_vars, _normalize_db_id
│   ├── test_anki.py         # anki_request, build_fields 等
│   ├── test_notion.py       # fetch_entries, get_text_property 等
│   └── test_sync.py         # sync_deck ロジック
└── integration/
    ├── test_notion_api.py   # 実 Notion API（@pytest.mark.integration）
    └── test_ankiconnect.py  # 実 AnkiConnect（@pytest.mark.integration）
```

## pytest 基本

### テスト構造

```python
import pytest

def test_expand_env_vars_replaces_variable(monkeypatch):
    monkeypatch.setenv("MY_VAR", "hello")
    result = _expand_env_vars("${MY_VAR}")
    assert result == "hello"

def test_expand_env_vars_keeps_unknown():
    result = _expand_env_vars("${NONEXISTENT_VAR}")
    assert result == "${NONEXISTENT_VAR}"
```

### アサーション

```python
# 等値
assert result == expected

# 真偽値
assert result
assert not result
assert result is None

# 包含
assert item in collection
assert item not in collection

# 型チェック
assert isinstance(result, dict)

# 例外
with pytest.raises(ValueError, match="invalid"):
    validate_input("bad")

# 例外の属性
with pytest.raises(RuntimeError) as exc_info:
    anki_request(url, "badAction")
assert "AnkiConnect" in str(exc_info.value)
```

## フィクスチャ

### 基本

```python
@pytest.fixture
def sample_config():
    return {
        "databases": {"Deutsch": "31e33e92-..."},
        "note_types": {"Deutsch": "SentenceVocab_DE"},
        "tts_lang": {"SentenceVocab_DE": "de_DE"},
        "notion_api_key": "ntn_test",
    }
```

### セットアップ / テアダウン

```python
@pytest.fixture
def temp_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("databases:\n  Test: test-uuid\n")
    yield config_file
    # tmp_path は pytest が自動で削除
```

### スコープ

```python
# function（デフォルト）: テストごとに実行
@pytest.fixture
def fresh_data():
    return []

# module: モジュールごとに1回
@pytest.fixture(scope="module")
def expensive_resource():
    resource = setup_resource()
    yield resource
    resource.cleanup()

# session: セッション全体で1回
@pytest.fixture(scope="session")
def shared_db():
    db = create_test_db()
    yield db
    db.close()
```

### conftest.py（共通フィクスチャ）

```python
# tests/conftest.py
import pytest

@pytest.fixture
def mock_notion_response():
    """Notion API のダミーレスポンス。"""
    return {
        "results": [
            {
                "id": "page-id-1",
                "properties": {
                    "Word": {"title": [{"plain_text": "Haus"}]},
                    "Meaning": {"rich_text": [{"plain_text": "家"}]},
                    "Anki Status": {"select": {"name": "New"}},
                    "Anki Note ID": {"rich_text": []},
                },
            }
        ],
        "has_more": False,
        "next_cursor": None,
    }

@pytest.fixture
def mock_anki_response():
    """AnkiConnect のダミーレスポンス。"""
    return {"result": 12345, "error": None}
```

## パラメタライズ

### 基本

```python
@pytest.mark.parametrize("raw,expected", [
    ("abc123", "abc123"),
    ("abc123?v=xyz", "abc123"),
    ("31e33e926b73807cab95ca196f3dfd3b",
     "31e33e92-6b73-807c-ab95-ca196f3dfd3b"),
])
def test_normalize_db_id(raw, expected):
    assert _normalize_db_id(raw) == expected
```

### ID 付き

```python
@pytest.mark.parametrize("status,should_sync", [
    ("New", True),
    ("Updated", True),
    ("Synced", False),
    ("Archived", False),
], ids=["new-sync", "updated-sync", "synced-skip", "archived-skip"])
def test_should_sync_status(status, should_sync):
    assert is_sync_target(status) is should_sync
```

## マーカーとテスト選択

### マーカー定義

```python
@pytest.mark.slow
def test_full_sync_cycle():
    ...

@pytest.mark.integration
def test_notion_api_connection():
    ...
```

### テスト実行コマンド

```bash
# 全テスト
uv run poe test

# 高速テストのみ（結合テスト除外）
uv run pytest -m "not slow and not integration"

# 結合テストのみ
uv run pytest -m integration

# 特定ファイル
uv run pytest tests/unit/test_config.py

# 特定テスト
uv run pytest tests/unit/test_config.py::test_normalize_db_id

# 詳細出力
uv run pytest -v

# 最初の失敗で中断
uv run pytest -x

# 前回失敗したテストのみ
uv run pytest --lf

# パターンで絞り込み
uv run pytest -k "config"
```

## モックとパッチ

### Notion API のモック

```python
from unittest.mock import patch, MagicMock

@patch("notion_to_anki.NotionClient")
def test_fetch_entries(mock_client_cls, sample_config, mock_notion_response):
    mock_client = MagicMock()
    mock_client.data_sources.query.return_value = mock_notion_response
    mock_client_cls.return_value = mock_client

    entries = fetch_entries(mock_client, "test-db-id", "Deutsch", sample_config)

    mock_client.data_sources.query.assert_called_once()
    assert len(entries) == 1
    assert entries[0]["word"] == "Haus"
```

### AnkiConnect のモック

```python
@patch("notion_to_anki.urllib.request.urlopen")
def test_anki_request_success(mock_urlopen, mock_anki_response):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_anki_response).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    result = anki_request("http://localhost:8765", "addNote", note={})
    assert result == 12345
```

### AnkiConnect エラー処理

```python
@patch("notion_to_anki.urllib.request.urlopen")
def test_anki_request_error(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(
        {"result": None, "error": "model not found"}
    ).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp

    with pytest.raises(RuntimeError, match="AnkiConnect"):
        anki_request("http://localhost:8765", "addNote", note={})
```

### 環境変数のモック

```python
def test_load_config_reads_env(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_API_KEY=ntn_test\nDB_ID=abc123\n")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "notion:\n  api_key: ${NOTION_API_KEY}\n"
        "databases:\n  Test: ${DB_ID}\n"
        "note_types:\n  Test: TestType\n"
    )

    monkeypatch.setattr("notion_to_anki.SCRIPT_DIR", tmp_path)
    config = load_config()

    assert config["notion_api_key"] == "ntn_test"
    assert "Test" in config["databases"]
```

### autospec でインターフェース違反を検出

```python
@patch("notion_to_anki.NotionClient", autospec=True)
def test_notion_client_autospec(mock_cls):
    mock_instance = mock_cls.return_value
    mock_instance.data_sources.query.return_value = {"results": [], "has_more": False}
    # 存在しないメソッドを呼ぶと自動で失敗する
```

## 副作用のテスト

### tmp_path でファイル操作

```python
def test_config_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("notion_to_anki.SCRIPT_DIR", tmp_path)
    monkeypatch.setenv("NOTION_API_KEY", "ntn_test")
    # config.yaml が存在しない → sys.exit
    with pytest.raises(SystemExit):
        load_config()
```

### Notion ページの更新モック

```python
@patch("notion_to_anki.NotionClient")
def test_update_page_status(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    update_anki_status(mock_client, "page-id-1", "Synced", note_id=12345)

    mock_client.pages.update.assert_called_once()
    call_kwargs = mock_client.pages.update.call_args[1]
    assert call_kwargs["page_id"] == "page-id-1"
```

## テストクラス

```python
class TestNormalizeDbId:
    def test_strips_view_param(self):
        assert _normalize_db_id("abc?v=xyz") == "abc"

    def test_adds_hyphens_to_32char_hex(self):
        raw = "31e33e926b73807cab95ca196f3dfd3b"
        expected = "31e33e92-6b73-807c-ab95-ca196f3dfd3b"
        assert _normalize_db_id(raw) == expected

    def test_passthrough_already_formatted(self):
        uuid = "31e33e92-6b73-807c-ab95-ca196f3dfd3b"
        assert _normalize_db_id(uuid) == uuid

class TestExpandEnvVars:
    def test_single_var(self, monkeypatch):
        monkeypatch.setenv("FOO", "bar")
        assert _expand_env_vars("${FOO}") == "bar"

    def test_nested_dict(self, monkeypatch):
        monkeypatch.setenv("KEY", "value")
        result = _expand_env_vars({"a": "${KEY}", "b": 42})
        assert result == {"a": "value", "b": 42}

    def test_list(self, monkeypatch):
        monkeypatch.setenv("X", "y")
        assert _expand_env_vars(["${X}", "z"]) == ["y", "z"]
```

## ベストプラクティス

### やるべきこと

- **TDD を守る**: 実装前にテストを書く（赤 → 緑 → リファクタ）
- **1テスト1振る舞い**: テストが検証する内容を1つに絞る
- **命名を明確に**: `test_normalize_db_id_strips_view_param`
- **フィクスチャで重複排除**: 共通データは conftest.py に集約
- **外部依存はモック**: Notion API・AnkiConnect は必ずモック
- **エッジケースを網羅**: 空文字列、None、境界値
- **カバレッジ 80% 以上**: クリティカルパスは 100%
- **テストを高速に**: 遅いテストは `@pytest.mark.slow` で分離

### やってはいけないこと

- **実装の内部をテスト**: 振る舞い（入出力）をテストする
- **テスト内で条件分岐**: テストはシンプルに保つ
- **テスト失敗を放置**: 全テスト通過が前提
- **サードパーティのテスト**: notion-client 自体のテストは不要
- **テスト間の状態共有**: テストは独立させる
- **テスト内で例外をキャッチ**: `pytest.raises` を使う
- **print デバッグ**: アサーションと pytest 出力を使う
- **過剰なモック**: テストが壊れやすくなる

## クイックリファレンス

| パターン | 用途 |
|---------|------|
| `pytest.raises()` | 例外テスト |
| `@pytest.fixture()` | 再利用可能なテストデータ |
| `@pytest.mark.parametrize()` | 複数入力でテスト |
| `@pytest.mark.slow` | 低速テストのマーク |
| `@pytest.mark.integration` | 結合テストのマーク |
| `uv run pytest -m "not slow"` | 高速テストのみ実行 |
| `@patch()` | 関数・クラスのモック |
| `monkeypatch` | 環境変数のモック |
| `tmp_path` | 一時ディレクトリ |
| `uv run pytest --cov` | カバレッジレポート |

## トラブルシューティング

失敗したら次の順で確認する（CLAUDE.md 準拠）:

1. **テストの分離**: 他のテストの影響を受けていないか
2. **モックの検証**: パッチ対象のパスは正しいか（`notion_to_anki.urllib` のように、インポート先でパッチする）
3. **実装の修正**: テストが正しければ実装を直す
