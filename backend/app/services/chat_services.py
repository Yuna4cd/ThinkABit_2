import asyncio
import random
import json
from google import genai
from collections import deque

from google.genai import types
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL, DATABASE_URL
from app.services.metastore_service import MetastoreService
from app.services.upload_service import UploadService


from fastapi.concurrency import run_in_threadpool

rate_limit_lock = asyncio.Lock()        
request_times = deque()
RPM_LIMIT = 10
WINDOW_SECONDS = 60



def _get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing.")
    return genai.Client(api_key=GEMINI_API_KEY)

# --chat helper
def build_history(history: list[dict]) -> str:
    lines = []
    for item in history:
        role = item.get("role","user")
        text = item.get("text","")
        prefix = "Assistant" if role == "assistant" else "User"
        lines.append(f"{prefix}: {text}")
    return "\n".join(lines)

async def rate_limit():
    while True:
        async with rate_limit_lock:
            now = asyncio.get_running_loop().time()
            while request_times and now - request_times[0] > WINDOW_SECONDS:
                request_times.popleft()
            if len(request_times) < RPM_LIMIT:
                request_times.append(now)
                return
            sleep_for = WINDOW_SECONDS - (now - request_times[0])
        await asyncio.sleep(max(sleep_for, 0))


def _generate_chat_reply_sync(message: str, history: list[dict], dataset_id: str | None = None, session_id: str | None = None,) -> str:
    client = _get_client()

    system_prompt="""
You are the AI chatbot assistant for ThinkABit Visualization.

The user may upload a dataset. When uploaded dataset context is provided, you can inspect the user's file through the supplied metadata, schema, and preview rows. Use that context to answer questions about the file, recommend visualizations, identify useful columns, and explain what the visible data suggests.

Dataset context rules:
- Treat the uploaded dataset context as the source of truth for the user's file.
- Use the filename, row count, column count, schema, data types, and preview rows when answering file-specific questions.
- Do not claim to know values, trends, distributions, or data quality issues that are not supported by the schema or preview rows.
- If the preview rows are insufficient, explain what cannot be determined and what additional file information or analysis is needed.
- If no uploaded dataset context is provided, answer generally and ask the user to upload a file or describe their columns when needed.

Your responsibilities:
- Help users understand how to create visualizations.
- Recommend suitable chart types, such as bar, line, scatter, histogram, box, or pie charts.
- Explain why a recommendation fits the user's columns and goal.
- Suggest practical next steps for preparing or visualizing the data.
- Teach the user how to think about visualization choices instead of only giving a final answer.

Behavior rules:
- Be concise, practical, and accurate.
- Ask a follow-up question when the user's goal is vague.
- Keep explanations simple.
- Explain the reasoning behind each recommendation.
""".strip()
    
    dataset_context = None

    if dataset_id:
        dataset_context = inspect_uploaded_dataset(dataset_id, session_id)
    
    dataset_section=""
    if dataset_context:
        dataset_section = f"\nUploaded dataset context:\n{json.dumps(dataset_context, indent=2)}"


    prompt = (
        f"{system_prompt}\n\n"
        f"{dataset_section}\n\n"
        f"Conversation history: {build_history(history)}\n"
        f"User: {message}\n\n"
        "Assistant:"
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return getattr(response, "text", None) or "Nothing is generated."

async def generate_chat_reply (msg: str, history: list[dict], dataset_id: str | None = None, session_id: str  | None = None, max_retries: int=5) -> str:
    for attempt in range(max_retries):
        await rate_limit()

        try:
            return await run_in_threadpool(_generate_chat_reply_sync, msg, history, dataset_id, session_id)
        
        except Exception as e:
            error_text = str(e)
            is_rate_limited = "429" in error_text or "RESOURCE_EXHAUSTED"in error_text

            if not is_rate_limited:
                raise
            if attempt == max_retries - 1:
                raise RuntimeError("Gemini API rate limit exceeded. Please try again later.") from e
            
            backoff = min(2 ** attempt, 30) + random.uniform(0,1)
            
            await asyncio.sleep(backoff)
    
    raise RuntimeError("Gemini API rate limit exceeded. Please try again later.")
    
def inspect_uploaded_dataset(dataset_id: str | None, session_id: str | None) -> dict:
    metastored = MetastoreService(database_url=DATABASE_URL)
    upload_service = UploadService()

    metadata = metastored.get_dataset_metadata(dataset_id)
    if metadata is None:
        raise ValueError("Dataset not found.")
    if session_id is None:
        raise PermissionError("Session id not found")
    if metadata.session_id is not None and metadata.session_id != session_id:
        raise PermissionError("You do not have access to this dataset.")
    
    source = metastored.get_dataset_preview_source(dataset_id)
    if source is None:
        raise ValueError("Dataset storage not found.")
    
    content = upload_service.storage_service.get_object(key=source.storage_key_raw)

    preview_row = upload_service.build_preview_rows(
        content = content,
        extension = source.extension,
        limit = 10,
        offset = 0,
    )

    schema = upload_service.parse_dataset_bytes(
        content=content,
        extension=source.extension
    )

    schema_columns = upload_service._build_schema(schema)

    return {
        "dataset_id": metadata.dataset_id,
        "session_id": metadata.session_id,
        "filename": metadata.original_filename,
        "extension": metadata.extension,
        "rows": metadata.row_count,
        "columns": metadata.column_count,
        "schema": [column.model_dump() for column in schema_columns],
        "preview_rows": preview_row,
    }
