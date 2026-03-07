import os
from dotenv import load_dotenv

load_dotenv()

# Your Notion DATA SOURCE ID
TRANSCRIPTS_DATA_SOURCE_ID = os.getenv("TRANSCRIPTS_DATA_SOURCE_ID")
MAIN_DB_DATASOURCE_ID = os.getenv("MAIN_DB_DATASOURCE_ID")

# ai output databases
SUMMARY_DB_ID = os.getenv("SUMMARY_DB_ID")
NOTES_DB_ID = os.getenv("NOTES_DB_ID")


if not all([TRANSCRIPTS_DATA_SOURCE_ID, MAIN_DB_DATASOURCE_ID, SUMMARY_DB_ID, NOTES_DB_ID]):
    raise ValueError("Missing required environment variables.")

STATUS_READY="ready"
STATUS_NOT_READY="not_ready"
STATUS_DONE="done"
STATUS_ERROR="error"