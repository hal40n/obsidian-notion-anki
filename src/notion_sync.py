"""Notion DB からのデータ取得・更新"""

from notion_client import Client as NotionClient


def get_text_property(page: dict, prop_name: str) -> str:
    """Notion ページのテキスト系プロパティを文字列として取得する。

    title / rich_text / select / number 型に対応する。

    Args:
        page: Notion API から取得したページ辞書。
        prop_name: 取得するプロパティ名。

    Returns:
        プロパティの文字列値。プロパティが存在しない・未対応型の場合は空文字。
    """
    prop = page["properties"].get(prop_name)
    if not prop:
        return ""

    prop_type = prop["type"]

    if prop_type == "title":
        return "".join(t["plain_text"] for t in prop.get("title", []))
    if prop_type == "rich_text":
        return "".join(t["plain_text"] for t in prop.get("rich_text", []))
    if prop_type == "select":
        sel = prop.get("select")
        return sel["name"] if sel else ""
    if prop_type == "number":
        return prop.get("number") or ""
    return ""


def _get_data_source_id(notion: NotionClient, db_id: str) -> str:
    """DB から data source ID を取得する（API 2025-09-03: DB ID ≠ data source ID）。

    Args:
        notion: Notion クライアントインスタンス。
        db_id: Notion データベース ID。

    Returns:
        data source ID 文字列。

    Raises:
        ValueError: data source が見つからない場合。
    """
    db_info = notion.databases.retrieve(db_id)
    data_sources = db_info.get("data_sources", [])
    if not data_sources:
        raise ValueError(f"DB {db_id} に data source が見つかりません")
    return data_sources[0]["id"]


def _map_language_entry(page: dict) -> dict:
    """Notion ページを言語学習用エントリ辞書にマッピングする。

    Args:
        page: Notion API から取得したページ辞書。

    Returns:
        言語学習用エントリの辞書。
    """
    anki_status = get_text_property(page, "Anki Status")
    anki_note_id = get_text_property(page, "Anki Note ID")
    return {
        "page_id": page["id"],
        "anki_status": anki_status,
        "anki_note_id": int(anki_note_id) if anki_note_id else None,
        "word": get_text_property(page, "Word"),
        "meaning": get_text_property(page, "Meaning"),
        "pos": get_text_property(page, "Part of Speech"),
        "example": get_text_property(page, "Example"),
        "example_translation": get_text_property(page, "Example Translation"),
        "usage": get_text_property(page, "Usage"),
        "sources": get_text_property(page, "Sources"),
        "language": get_text_property(page, "Language"),
    }


def _map_cert_entry(page: dict) -> dict:
    """Notion ページを資格学習用エントリ辞書にマッピングする。

    Args:
        page: Notion API から取得したページ辞書。

    Returns:
        資格学習用エントリの辞書。
    """
    anki_status = get_text_property(page, "Anki Status")
    anki_note_id = get_text_property(page, "Anki Note ID")
    return {
        "page_id": page["id"],
        "anki_status": anki_status,
        "anki_note_id": int(anki_note_id) if anki_note_id else None,
        "word": get_text_property(page, "Term"),
        "meaning": get_text_property(page, "Definition"),
        "category": get_text_property(page, "Category"),
    }


def fetch_entries(notion: NotionClient, db_id: str, deck: str, config: dict) -> list[dict]:
    """Notion DB から Anki Status = "New" または "Updated" のエントリを全件取得する。

    ページネーションを自動処理する。

    Args:
        notion: Notion クライアントインスタンス。
        db_id: Notion データベース ID。
        deck: デッキ名（config の note_types キーと一致）。
        config: アプリケーション設定辞書。

    Returns:
        エントリ辞書のリスト。
    """
    note_type = config["note_types"][deck]
    is_language = note_type.startswith("SentenceVocab")
    ds_id = _get_data_source_id(notion, db_id)

    results = []
    has_more = True
    start_cursor = None

    while has_more:
        body = {
            "filter": {
                "or": [
                    {"property": "Anki Status", "select": {"equals": "New"}},
                    {"property": "Anki Status", "select": {"equals": "Updated"}},
                ]
            },
            "page_size": 100,
        }
        if start_cursor:
            body["start_cursor"] = start_cursor

        response = notion.data_sources.query(ds_id, **body)
        results.extend(response["results"])
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")

    mapper = _map_language_entry if is_language else _map_cert_entry
    return [mapper(page) for page in results]


def update_notion_page(notion: NotionClient, page_id: str, anki_note_id: int) -> None:
    """Anki 同期完了後に Notion ページのステータスとノート ID を更新する。

    Anki Status を "Synced" に、Anki Note ID を設定する。

    Args:
        notion: Notion クライアントインスタンス。
        page_id: 更新対象の Notion ページ ID。
        anki_note_id: 同期済み Anki ノートの ID。
    """
    notion.pages.update(
        page_id=page_id,
        properties={
            "Anki Status": {"select": {"name": "Synced"}},
            "Anki Note ID": {"number": anki_note_id},
        },
    )
