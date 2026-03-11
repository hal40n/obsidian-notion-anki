"""src/anki_client.py のユニットテスト"""

import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from src.anki_client import anki_request, DEFAULT_URL


def _mock_response(result=None, error=None):
    """urllib.request.urlopen のモックレスポンスを作る。"""
    data = json.dumps({"result": result, "error": error}).encode()
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = data
    return mock


class TestAnkiRequest:
    def test_returns_result_on_success(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(result=6)):
            result = anki_request("version")
        assert result == 6

    def test_raises_runtime_error_on_anki_error(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(error="duplicate note")):
            with pytest.raises(RuntimeError, match="duplicate note"):
                anki_request("addNote")

    def test_calls_default_url(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(result=[])) as mock_open:
            anki_request("modelNames")
            called_req = mock_open.call_args[0][0]
            assert called_req.full_url == DEFAULT_URL

    def test_calls_custom_url(self):
        custom_url = "http://localhost:9999"
        with patch("urllib.request.urlopen", return_value=_mock_response(result=[])) as mock_open:
            anki_request("modelNames", url=custom_url)
            called_req = mock_open.call_args[0][0]
            assert called_req.full_url == custom_url

    def test_passes_params_in_payload(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(result="ok")) as mock_open:
            anki_request("addNote", note={"deckName": "Deutsch"})
            called_req = mock_open.call_args[0][0]
            payload = json.loads(called_req.data)
            assert payload["action"] == "addNote"
            assert payload["params"]["note"]["deckName"] == "Deutsch"

    def test_exits_on_connection_error(self):
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            with pytest.raises(SystemExit):
                anki_request("version")
