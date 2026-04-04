from pydantic import BaseModel, Field

# --chat request props
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str