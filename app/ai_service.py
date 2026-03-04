import os
from idlelib.pyparse import trans

import openai
from dotenv import load_dotenv
from openai import api_key

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_ai_summary(transcript: str):
    print("inside ai summ fun")
    client = openai.OpenAI(api_key=openai.api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # fast + cheap
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AWS certification exam fact extractor. "
                    "Extract ONLY high-value exam facts. "
                    "Output ultra-concise bullet fragments for Notion notes"
                    "No full sentences. "
                    "No explanations. "
                    "No filler words. "
                    "Do not miss any important limits, numbers, definitions, or comparisons."
                )
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
        temperature=0.1,  # VERY important
        max_tokens=200  # keeps it compressed
    )

    return response.choices[0].message.content


def get_ai_notes(transcript: str):
    client = openai.OpenAI(api_key=openai.api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AWS certification exam note generator. "
                    "Create structured, detailed notes from the transcript for Notion notes"
                    "Use clear headings for main topics. "
                    "Use bullet points under each heading. "
                    "1–2 short sentences per bullet maximum. "
                    "Include definitions, limits, comparisons, and exam tips. "
                    "Do not add unnecessary explanations or filler text."
                )
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
        temperature=0.3,
        max_tokens=900  # more space for structured notes
    )

    return response.choices[0].message.content
