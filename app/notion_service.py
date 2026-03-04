from app.config import (TRANSCRIPTS_DATA_SOURCE_ID)
from notion_client import Client
from dotenv import load_dotenv
import os

# --------------------------------------------------
# Configuration
# --------------------------------------------------
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")

if not NOTION_TOKEN:
    raise ValueError("NOTION_TOKEN not found in environment variables.")

notion = Client(auth=NOTION_TOKEN,
notion_version="2025-09-03")

def mark_row_as_processed(page_id: str):
    notion.pages.update(
        page_id=page_id,
        properties={
            "IsProcessed": {
                "checkbox": True
            }
        }
    )


def query_data_source():
    """
    Fetch ALL rows from the Notion data source.
    Handles pagination.
    """
    results = []
    next_cursor = None

    while True:
        response = notion.data_sources.query(
            data_source_id=TRANSCRIPTS_DATA_SOURCE_ID,
            start_cursor=next_cursor
        )
        print("1____________________________________")
        print(response)

        results.extend(response["results"])

        if response.get("has_more"):
            next_cursor = response["next_cursor"]
        else:
            break

    return results

def extract_properties(page):
    """Convert Notion properties into clean Python dict."""
    props = page["properties"]
    clean = {}

    for key, value in props.items():
        t = value["type"]

        if t == "title":
            clean[key] = "".join(x["plain_text"] for x in value["title"])

        elif t == "rich_text":
            clean[key] = "".join(x["plain_text"] for x in value["rich_text"])

        elif t == "select":
            clean[key] = value["select"]["name"] if value["select"] else None

        elif t == "multi_select":
            clean[key] = [x["name"] for x in value["multi_select"]]

        elif t == "relation":
            clean[key] = [x["id"] for x in value["relation"]]

        elif t == "number":
            clean[key] = value["number"]

        elif t == "checkbox":
            clean[key] = value["checkbox"]

        elif t == "date":
            clean[key] = value["date"]

        else:
            clean[key] = None

    return clean

def extract_page_content(page_id):
    """
    Fetch full page block content.
    Handles pagination (Notion returns max 100 blocks per call).
    """
    text = []
    next_cursor = None

    while True:
        response = notion.blocks.children.list(
            block_id=page_id,
            start_cursor=next_cursor
        )

        for block in response["results"]:
            block_type = block["type"]

            if block_type in block and "rich_text" in block[block_type]:
                for rt in block[block_type]["rich_text"]:
                    text.append(rt["plain_text"])

        if response.get("has_more"):
            next_cursor = response["next_cursor"]
        else:
            break

    return "\n".join(text)

def get_page_obj(page_id: str):
    # Retrieve page
    page = notion.pages.retrieve(page_id=page_id)

    # Extract properties
    properties = extract_properties(page)

    # Extract content blocks
    content = extract_page_content(page_id)

    return {
        "page_id": page_id,
        "properties": properties,
        "content": content
    }

def create_notion_page_in_db(title: str, markdown_content: str, db_id: str):
    response = notion.request(
        path="pages",
        method="POST",
        body={
            "parent": {"database_id": db_id},
            "properties": {
                "Title": {  # Change to "Name" if your column is named Name
                    "title": [{"text": {"content": title}}]
                }
            },
            # This is the "Markdown" magic
            "markdown": markdown_content
        }
    )


    return response["id"]

def connect_notion_page_to_row(main_page_id: str, relation_column_name: str, relation_page_id: str):
    notion.pages.update(
        page_id=main_page_id,
        properties={
            relation_column_name: {   # <-- EXACT relation column name in Main DB
                "relation": [
                    {"id": relation_page_id}
                ]
            }
        }
    )