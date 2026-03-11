"""AnkiConnect 通信モジュール"""

import json
import sys
import urllib.request

DEFAULT_URL = "http://localhost:8765"


def anki_request(action: str, url: str = DEFAULT_URL, **params):
    """AnkiConnect に JSON リクエストを送信する。"""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read())
    except Exception as e:
        print(f"❌ AnkiConnect に接続できません: {e}")
        sys.exit(1)

    if response.get("error"):
        raise RuntimeError(f"AnkiConnect: {response['error']}")
    return response.get("result")
