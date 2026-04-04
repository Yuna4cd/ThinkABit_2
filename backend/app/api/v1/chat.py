import requests, os

from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_services import build_history, generate_chat_reply

router = APIRouter()

# --chat routes
@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=200
    )
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Request content is missing.")
    try:
        reply = generate_chat_reply(req.message, req.history)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
