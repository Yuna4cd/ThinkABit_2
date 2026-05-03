from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import plotly.express as px
import pandas as pd

router = APIRouter()

class ChartConfig(BaseModel):
    data: list[dict[str, Any]]
    x: str
    y: str
    color: Optional[str] = None
    chart_type: str = "bar"
    title: Optional[str] = None
    width: int = 800
    height: int = 500

@router.post("/charts/generate")
def generate_chart(config: ChartConfig):
    df = pd.DataFrame(config.data)

    if config.x not in df.columns or config.y not in df.columns:
        raise HTTPException(status_code=400, detail="Invalid x or y column.")

    try:
        if config.chart_type == "bar":
            fig = px.bar(df, x=config.x, y=config.y, color=config.color, title=config.title)
        elif config.chart_type == "line":
            fig = px.line(df, x=config.x, y=config.y, color=config.color, title=config.title)
        elif config.chart_type == "scatter":
            fig = px.scatter(df, x=config.x, y=config.y, color=config.color, title=config.title)
        elif config.chart_type == "pie":
            fig = px.pie(df, names=config.x, values=config.y, title=config.title)
        elif config.chart_type == "histogram":
            fig = px.histogram(df, x=config.x, title=config.title)
        elif config.chart_type == "box":
            fig = px.box(df, x=config.x, y=config.y, title=config.title)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {config.chart_type}")

        fig.update_layout(width=config.width, height=config.height)
        return fig.to_json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))