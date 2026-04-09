from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import plotly.express as px
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # TODO: needs to be updated in the future for deployment
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChartConfig(BaseModel):
    data: list[dict[str, Any]]
    x: str
    y: str
    color: Optional[str] = None
    chart_type: str = "scatter"
    title: Optional[str] = None
    width: int = 800
    height: int = 500

@app.post("/api/chart")
def get_chart(config: ChartConfig):
    df = pd.DataFrame(config.data)

    fig = px.scatter(df, x=config.x, y=config.y, color=config.color)

    fig.update_layout(
        title=config.title,
        width=config.width,
        height=config.height
    )

    return fig.to_json()