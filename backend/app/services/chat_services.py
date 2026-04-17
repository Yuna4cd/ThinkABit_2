import asyncio
import random
from google import genai
from collections import deque

from google.genai import types
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL
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


def _generate_chat_reply_sync(message: str, history: list[dict]) -> str:
    client = _get_client()

    system_prompt="""
This website is ThinkABit Visualization, and you are the AI chatbot for assistant.

Your responsiblities:
- help users to understand how to create visualization
- recommend suitable type of chart (e.g. pie, line, bar)
- explain the reason after recommendation
- suggest next steps for visualization
- using tools if needed

Behavior rules:
- be concise, practical, and accurate
- do not provide correct answer everytime, try to teach users how to do visualization
- ask follow-up question if the user's message is vague.
- Provide explaination after every sugestion.
- keep answer simple.

""".strip()
    


    prompt = (
        f"{system_prompt}\n\n"
        f"Conversation history: {build_history(history)}\n"
        f"User: {message}\n\n"
        "Assistant:"
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return getattr(response, "text", None) or "Nothing is generated."

async def generate_chat_reply (msg: str, history: list[dict], max_retries: int=5) -> str:
    for attempt in range(max_retries):
        await rate_limit()

        try:
            return await run_in_threadpool(_generate_chat_reply_sync, msg, history)
        
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
    
