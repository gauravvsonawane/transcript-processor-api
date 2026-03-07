import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.params import Depends
from notion_client import Client
from dotenv import load_dotenv

from app.config import (
    NOTES_DB_ID,
    SUMMARY_DB_ID,
    STATUS_READY,
    STATUS_NOT_READY,
    STATUS_DONE,
    STATUS_ERROR
)

from app.notion_service import (
    get_page_obj,
    create_notion_page_in_db,
    connect_notion_page_to_row,
    query_data_source,
    update_row_status
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


def get_ready_rows(all_rows):
    ready_rows = []
    for row in all_rows:
        # Safely get status
        status_prop = row["properties"].get("Status")
        print("status_prop")

        if status_prop and status_prop.get("status"):
            status = status_prop["status"].get("name")
            if status == STATUS_READY:
                ready_rows.append(row)
    return ready_rows



def process_a_row(row):
    main_page_id = row["id"]

    try:
        # extract meta-data and content from row
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

        # Mark row as done
        update_row_status(main_page_id, STATUS_DONE)

    except Exception as e:
        print(f"Error processing row {main_page_id}: {str(e)}")
        # Mark row as error
        update_row_status(main_page_id, STATUS_ERROR)
        raise




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
    ready_rows = get_ready_rows(results)
    print(ready_rows)
    for row in ready_rows:
        process_a_row(row)

    return {"processed_rows": len(ready_rows)}
