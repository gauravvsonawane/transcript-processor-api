import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.params import Depends
from notion_client import Client
from dotenv import load_dotenv

from app.config import (
    NOTES_DB_ID,
    SUMMARY_DB_ID
)

from app.notion_service import (
    get_page_obj,
    create_notion_page_in_db,
    connect_notion_page_to_row,
    query_data_source,
    mark_row_as_processed
)

from app.ai_service import (
    get_ai_summary,
    get_ai_notes
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

if not NOTION_TOKEN:
    raise ValueError("NOTION_TOKEN not found in environment variables.")

notion = Client(auth=NOTION_TOKEN)
app = FastAPI()


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

def get_unprocessed_rows(all_rows):
    unprocessed_rows = []
    for row in all_rows:
        is_row_processed = row["properties"]["IsProcessed"]["checkbox"]
        if not is_row_processed:
            unprocessed_rows.append(row)

    return unprocessed_rows


def process_a_row(row):
    # extract meta-data and content from row
    # print("Properties")
    # print(row["properties"])
    main_page_id = row["id"]
    transcript_page_id = row["properties"]["Transcript"]["relation"][0]["id"]
    transcript_page_obj = get_page_obj(transcript_page_id)
    transcript_title = transcript_page_obj["properties"]["Title"]
    transcript_content = transcript_page_obj["content"]

    # get processed info from AI
    ai_summary = get_ai_summary(transcript_title + " " + transcript_content)
    ai_notes = get_ai_notes(transcript_title + " " + transcript_content)

    print(ai_summary)
    print('+++++++++++++++++++++++++++++++++++')
    print(ai_notes)

    # create ai_summary and ai_notes page in notion
    new_summary_page_id = create_notion_page_in_db(transcript_title, ai_summary, SUMMARY_DB_ID)
    new_notes_page_id = create_notion_page_in_db(transcript_title, ai_notes, NOTES_DB_ID)

    # connect these new notion pages to the respective row and column
    connect_notion_page_to_row(main_page_id, "Summary", new_summary_page_id)
    connect_notion_page_to_row(main_page_id, "Notes", new_notes_page_id)

    mark_row_as_processed(main_page_id)

# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
def root():
    return {"message": "Notion Transcript API running."}

@app.get("/page/{page_id}")
def get_page(page_id: str):
    try:
        page_obj = get_page_obj(page_id)
        return page_obj

    except Exception as e:
        return {"error": str(e)}



@app.get("/process-transcripts")
def process_transcript(api_key: str = Depends(verify_api_key)):
    """
    1. fetch all the rows from main db
    2. get unprocessed rows from all rows
    3. process rows - iterate over rows and for each row ->
        a. get transcript of a particular row
        b. send transcript to AI and get summary and notes
        c. create notion pages for summary and notes in their respective databases
        d. link the pages in the main db

    :return: number of processed rows
    """

    results = query_data_source()
    unprocessed_rows = get_unprocessed_rows(results)
    for row in unprocessed_rows:
        process_a_row(row)

    return {"processed_rows": len(unprocessed_rows)}