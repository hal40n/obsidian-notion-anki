"""設定読み込み: config.yaml + .env"""

import os
import re
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent.parent


def _expand_env_vars(obj):
    """YAML 値中の ${VAR_NAME} を環境変数で再帰的に展開する。"""
    if isinstance(obj, str):
        return re.sub(
            r"\$\{(\w+)\}",
            lambda m: os.environ.get(m.group(1), m.group(0)),
            obj,
        )
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env_vars(v) for v in obj]
    return obj


def _normalize_db_id(raw: str) -> str:
    """Notion URL からコピーした ID を正規化する。

    '?v=...' を除去し、32桁 hex をハイフン付き UUID に変換する。
    """
    raw = raw.split("?")[0].strip().replace("-", "")
    if len(raw) == 32:
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    return raw


def load_config() -> dict:
    """config.yaml と .env を読み込む。"""
    env_path = SCRIPT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        print("❌ NOTION_API_KEY が設定されていません。")
        print("   .env ファイルに NOTION_API_KEY=ntn_xxxxx を記載してください。")
        sys.exit(1)

    config_path = SCRIPT_DIR / "config.yaml"
    if not config_path.exists():
        print(f"❌ {config_path} が見つかりません。")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config = _expand_env_vars(config)
    config["databases"] = {
        k: _normalize_db_id(v) for k, v in config.get("databases", {}).items()
    }
    config["notion_api_key"] = api_key
    return config
