"""
app/api/v1/visualization_router.py
----------------------------
FastAPI router for visualization customization.

Registered in main.py under the same /api/v1 prefix as the upload router,
so all endpoints live at:

    GET  /api/v1/colors                     All active colors
    GET  /api/v1/colors/{color_id}          Single color by ID
    POST /api/v1/colors                     Add a new color

    GET  /api/v1/plot-types                 All active plot types
    GET  /api/v1/plot-types/by-name/{name}  Single plot type by machine name
    GET  /api/v1/plot-types/{plot_type_id}  Single plot type by ID
    POST /api/v1/plot-types                 Add a new plot type

Errors are raised as APIError inside the service so the shared handler in
errors.py formats every error response in the same envelope used by /upload.
"""

from fastapi import APIRouter

from app.schemas.visualization import (
    ColorCreate,
    ColorResponse,
    PlotTypeCreate,
    PlotTypeResponse,
)
from app.services.visualization_service import VisualizationService

router = APIRouter()
visualization_service = VisualizationService()


# ── Colors ────────────────────────────────────────────────────────────────────

@router.get(
    "/colors",
    response_model=list[ColorResponse],
    status_code=200,
)
def get_colors() -> list[ColorResponse]:
    """
    Return all active colors available for visualization customization.

    The frontend uses `hex_code` when rendering the chart and `name` as
    the human-readable label in the color picker.
    """
    return visualization_service.get_all_colors()


@router.get(
    "/colors/{color_id}",
    response_model=ColorResponse,
    status_code=200,
)
def get_color(color_id: int) -> ColorResponse:
    """
    Return a single color by its ID.

    Raises 404 when the color does not exist or is inactive.
    """
    return visualization_service.get_color_by_id(color_id)


@router.post(
    "/colors",
    response_model=ColorResponse,
    status_code=201,
)
def create_color(body: ColorCreate) -> ColorResponse:
    """
    Add a new color option.

    `hex_code` must be a valid 6-digit CSS hex value (e.g. `#FF5733`).
    Raises 409 if a color with the same name already exists.
    """
    return visualization_service.create_color(body)


# ── Plot types ────────────────────────────────────────────────────────────────

@router.get(
    "/plot-types",
    response_model=list[PlotTypeResponse],
    status_code=200,
)
def get_plot_types() -> list[PlotTypeResponse]:
    """
    Return all active plot types.

    Each object includes `supported_channels` — the list of customization
    channels (`color`, `shape`, `size`, `position`) the frontend should
    enable when the user selects that chart type.
    """
    return visualization_service.get_all_plot_types()


@router.get(
    "/plot-types/by-name/{name}",
    response_model=PlotTypeResponse,
    status_code=200,
)
def get_plot_type_by_name(name: str) -> PlotTypeResponse:
    """
    Return a single plot type by its machine name (e.g. `bar`, `scatter`).

    Use this after the user picks a chart type to retrieve
    `supported_channels` and enable the correct controls in the UI.
    Raises 404 when the name is not found.
    """
    return visualization_service.get_plot_type_by_name(name)


@router.get(
    "/plot-types/{plot_type_id}",
    response_model=PlotTypeResponse,
    status_code=200,
)
def get_plot_type(plot_type_id: int) -> PlotTypeResponse:
    """
    Return a single plot type by its ID.

    Raises 404 when the plot type does not exist or is inactive.
    """
    return visualization_service.get_plot_type_by_id(plot_type_id)


@router.post(
    "/plot-types",
    response_model=PlotTypeResponse,
    status_code=201,
)
def create_plot_type(body: PlotTypeCreate) -> PlotTypeResponse:
    """
    Add a new plot type.

    `supported_channels` must be a non-empty list containing only:
    `color`, `shape`, `size`, `position`.
    Raises 409 if a plot type with the same machine name already exists.
    """
    return visualization_service.create_plot_type(body)