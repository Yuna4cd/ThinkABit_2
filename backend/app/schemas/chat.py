from pydantic import BaseModel, Field

# --chat request props
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    
    dataset_id: str | None = None
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str