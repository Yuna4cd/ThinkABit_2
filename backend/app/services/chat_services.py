from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL


if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=GEMINI_API_KEY)

# --chat helper
def build_history(history: list[dict]) -> str:
    lines = []
    for item in history:
        role = item.get("role","user")
        text = item.get("text","")
        prefix = "Assistant" if role == "assistant" else "User"
        lines.append(f"{prefix}: {text}")
    return "\n".join(lines)


def generate_chat_reply(message: str, history: list[dict]) -> str:
    prompt = (
        "You are a helpful AI chatbot for a website.\n\n"
        f"{build_history(history)}\n"
        f"User: {message}\n\n"
        "Assistant:"
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="low")
        ),
    )

    return getattr(response, "text", None) or "Nothing is generated."