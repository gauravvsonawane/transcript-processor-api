# Transcript Processor API 🚀

An automated pipeline to transform raw transcripts into high-value study materials. This API integrates **FastAPI**, **Notion**, and **OpenAI** to streamline the process of summarizing transcripts and generating structured notes, specifically optimized for AWS certification exams.

## 📖 Overview

The **Transcript Processor API** acts as a bridge between your raw study data in Notion and AI-powered insights. It monitors a "Main" database for rows marked as "Ready", extracts the linked transcript content, uses GPT-4o-mini to generate concise exam facts and detailed notes, and then automatically populates related databases while linking everything back together.

---

## ✨ Key Features

- **Automated Workflow**: Process multiple transcripts in a single API call.
- **AI-Powered Summarization**: Specifically tuned prompts for AWS certification fact extraction.
- **Notion Integration**:
    - Full bidirectional synchronization.
    - Automatic page creation in "Summary" and "Notes" databases.
    - Automatic relational linking in the "Main" database.
- **Status Tracking**: Built-in status management (`ready`, `not_ready`, `done`, `error`).
- **Containerized**: Fully Dockerized for easy deployment.
- **Secure**: Protected by API key authentication.

---

## 🏗 Architecture & Workflow

The following diagram illustrates the end-to-end flow of a transcript processing request, triggered automatically by a daily schedule (via **cron-job.org**):

```text
      +---------------+          +---------------+          +---------------+          +---------------+
      | Cron-Job.org  |          |  FastAPI App  |          |  Notion API   |          |  OpenAI API   |
      | (Daily Trigger)|          |               |          |               |          |               |
      +-------+-------+          +-------+-------+          +-------+-------+          +-------+-------+
              |                          |                          |                          |
       1. GET /process-transcripts       |                          |                          |
              +------------------------->|                          |                          |
              |                          |  2. Query "Ready" Rows   |                          |
              |                          +------------------------->|                          |
              |                          |                          |                          |
              |                          |  3. Return Row Data      |                          |
              |                          |<-------------------------+                          |
              |                          |                          |                          |
              |                    [ LOOP START: For Each Row ]     |                          |
              |                          |                          |                          |
              |                          |  4. Fetch Transcript     |                          |
              |                          +------------------------->|                          |
              |                          |                          |                          |
              |                          |  5. Return Content       |                          |
              |                          |<-------------------------+                          |
              |                          |                          |                          |
              |                          |  6. Send to GPT-4o-mini  |                          |
              |                          +---------------------------------------------------->|
              |                          |                          |                          |
              |                          |  7. Return Facts/Notes   |                          |
              |                          |<----------------------------------------------------+
              |                          |                          |                          |
              |                          |  8. Create New Pages     |                          |
              |                          +------------------------->|                          |
              |                          |                          |                          |
              |                          |  9. Link to Main Row     |                          |
              |                          +------------------------->|                          |
              |                          |                          |                          |
              |                          |  10. Update Status "Done"|                          |
              |                          +------------------------->|                          |
              |                          |                          |                          |
              |                    [  LOOP END  ]                   |                          |
              |                          |                          |                          |
       11. Log Success                   |                          |                          |
              |<-------------------------+                          |                          |
              |                          |                          |                          |
```

---

## ⏰ Automation

The pipeline is fully automated using [cron-job.org](https://cron-job.org/).

- **Schedule**: Every morning (e.g., 9:00 AM).
- **Configuration**:
    - **URL**: `https://your-api-deployment-url.com/process-transcripts`
    - **Method**: `GET`
    - **Headers**: `X-API-Key: your_internal_api_key`

This setup ensures that all transcripts marked as "Ready" during the previous day are automatically processed, summarized, and linked without any manual intervention.

## 🛠 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **AI Model**: [OpenAI GPT-4o-mini](https://openai.com/index/gpt-4o-mini/)
- **Database/UI**: [Notion](https://www.notion.so/)
- **Language**: Python 3.11+
- **Deployment**: Docker & Uvicorn

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- An OpenAI API Key
- A Notion Integration Token (with access to your databases)
- Four Notion Databases (Main, Transcripts, Summaries, Notes)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd transcript-processor-api
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   API_KEY=your_internal_api_key
   NOTION_TOKEN=your_notion_integration_token
   OPENAI_API_KEY=your_openai_api_key

   TRANSCRIPTS_DATA_SOURCE_ID=id_of_transcripts_db
   MAIN_DB_DATASOURCE_ID=id_of_main_db
   SUMMARY_DB_ID=id_of_summary_db
   NOTES_DB_ID=id_of_notes_db
   ```

### Running the API

**Local Development:**
```bash
uvicorn app.main:app --reload
```

**Using Docker:**
```bash
docker build -t transcript-api .
docker run -p 8000:8000 --env-file .env transcript-api
```

---

## 📝 Notion Database Schema

To work correctly, your Notion setup should follow this structure:

1.  **Main DB**: The central hub.
    - `Status`: Status property (`ready`, `not_ready`, `done`, `error`).
    - `Transcript`: Relation to **Transcripts DB**.
    - `Summary`: Relation to **Summary DB**.
    - `Notes`: Relation to **Notes DB**.
2.  **Transcripts DB**: Contains raw transcriptions.
    - `Title`: Name of the session.
    - Page Content: The actual transcript text.
3.  **Summary DB**: AI-generated exam facts.
    - `Title`: (Set by API)
4.  **Notes DB**: AI-generated structured notes.
    - `Title`: (Set by API)

---

## 🛣 API Endpoints

### `GET /`
Health check endpoint.
- **Response**: `{"message": "Notion Transcript API running."}`

### `GET /process-transcripts`
The core processing engine.
- **Header**: `X-API-Key: <your_api_key>`
- **Workflow**:
    1. Fetches "ready" rows from the Main DB.
    2. Extracts transcripts.
    3. Generates AI summaries and notes.
    4. Creates Notion pages and links them.
    5. Updates status to "done".
- **Response**: `{"processed_rows": X}`

### `GET /page/{page_id}`
Utility endpoint to fetch a Notion page's properties and content.

---

## 🧪 AI Prompts

The API uses two distinct prompts optimized for AWS Certification:

- **Summary**: Extracts high-value exam facts as ultra-concise bullet fragments. No filler words, no full sentences.
- **Notes**: Creates structured, detailed notes with headings, definitions, limits, and exam tips.

---
*Created with ❤️ for AWS Certification Students.*
