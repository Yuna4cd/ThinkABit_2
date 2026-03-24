from typing import Literal
from pydantic import BaseModel, Field

# ── Channel type ──────────────────────────────────────────────────────────────
# The four encoding channels a user can customise on any supported chart.
ChannelType = Literal["color", "shape", "size", "position"]

# ── Color schemas ─────────────────────────────────────────────────────────────

class ColorResponse(BaseModel):
    id: int
    name: str
    hex_code: str
    is_active: bool


class ColorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    hex_code: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    is_active: bool = True


# ── PlotType schemas ──────────────────────────────────────────────────────────

class PlotTypeResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str
    supported_channels: list[ChannelType]
    is_active: bool


class PlotTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1)
    supported_channels: list[ChannelType] = Field(..., min_length=1)
    is_active: bool = True