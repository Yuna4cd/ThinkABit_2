"""
app/services/visualization_service.py
--------------------------------------
Business logic for the visualization customization resource.

Mirrors the pattern established in upload_service.py:
  - One service class per domain.
  - All data-access is isolated inside this class.
  - Raises APIError (never HTTPException) so the shared error handler in
    errors.py formats every error response consistently.
  - _build_error() is a private helper, identical in signature to the one
    in UploadService and UploadValidator.

DATABASE INTEGRATION
--------------------
Every method contains a clearly marked TODO block showing the exact
SQLAlchemy query to drop in when your database is ready.  The method
signatures and return types will not change — only the body of each TODO
block needs to be replaced.

The in-memory lists (COLORS / PLOT_TYPES) at the bottom of this file are
the only thing that disappears on integration.
"""

from uuid import uuid4

from app.errors import APIError
from app.schemas.visualization import (
    ColorCreate,
    ColorResponse,
    PlotTypeCreate,
    PlotTypeResponse,
)


class VisualizationService:

    # ------------------------------------------------------------------
    # Color operations
    # ------------------------------------------------------------------

    def get_all_colors(self) -> list[ColorResponse]:
        """
        Return every active color.

        TODO (DB):
            rows = db.query(ColorModel).filter(ColorModel.is_active == True).all()
            return [ColorResponse.model_validate(r) for r in rows]
        """
        return [
            ColorResponse(**c) for c in COLORS if c["is_active"]
        ]

    def get_color_by_id(self, color_id: int) -> ColorResponse:
        """
        Return one active color by primary key.

        Raises APIError 404 when not found.

        TODO (DB):
            row = db.query(ColorModel).filter(
                ColorModel.id == color_id, ColorModel.is_active == True
            ).first()
            if row is None:
                raise self._build_error(...)
            return ColorResponse.model_validate(row)
        """
        match = next((c for c in COLORS if c["id"] == color_id and c["is_active"]), None)
        if match is None:
            raise self._build_error(
                code="NOT_FOUND",
                message=f"Color with id={color_id} not found.",
                details={"color_id": color_id},
                status_code=404,
            )
        return ColorResponse(**match)

    def create_color(self, body: ColorCreate) -> ColorResponse:
        """
        Insert a new color record.

        Raises APIError 409 on duplicate name.

        TODO (DB):
            existing = db.query(ColorModel).filter(ColorModel.name == body.name).first()
            if existing:
                raise self._build_error(...)
            row = ColorModel(**body.model_dump())
            db.add(row)
            db.commit()
            db.refresh(row)
            return ColorResponse.model_validate(row)
        """
        if any(c["name"] == body.name for c in COLORS):
            raise self._build_error(
                code="CONFLICT",
                message=f"A color named '{body.name}' already exists.",
                details={"field": "name"},
                status_code=409,
            )
        new_id = max((c["id"] for c in COLORS), default=0) + 1
        record = {"id": new_id, **body.model_dump()}
        COLORS.append(record)
        return ColorResponse(**record)

    # ------------------------------------------------------------------
    # PlotType operations
    # ------------------------------------------------------------------

    def get_all_plot_types(self) -> list[PlotTypeResponse]:
        """
        Return every active plot type.

        TODO (DB):
            rows = db.query(PlotTypeModel).filter(PlotTypeModel.is_active == True).all()
            return [PlotTypeResponse.model_validate(r) for r in rows]
        """
        return [
            PlotTypeResponse(**pt) for pt in PLOT_TYPES if pt["is_active"]
        ]

    def get_plot_type_by_id(self, plot_type_id: int) -> PlotTypeResponse:
        """
        Return one active plot type by primary key.

        Raises APIError 404 when not found.

        TODO (DB):
            row = db.query(PlotTypeModel).filter(
                PlotTypeModel.id == plot_type_id, PlotTypeModel.is_active == True
            ).first()
            if row is None:
                raise self._build_error(...)
            return PlotTypeResponse.model_validate(row)
        """
        match = next(
            (pt for pt in PLOT_TYPES if pt["id"] == plot_type_id and pt["is_active"]), None
        )
        if match is None:
            raise self._build_error(
                code="NOT_FOUND",
                message=f"Plot type with id={plot_type_id} not found.",
                details={"plot_type_id": plot_type_id},
                status_code=404,
            )
        return PlotTypeResponse(**match)

    def get_plot_type_by_name(self, name: str) -> PlotTypeResponse:
        """
        Return one active plot type by machine name (e.g. "bar", "scatter").

        Raises APIError 404 when not found.

        TODO (DB):
            row = db.query(PlotTypeModel).filter(
                PlotTypeModel.name == name, PlotTypeModel.is_active == True
            ).first()
            if row is None:
                raise self._build_error(...)
            return PlotTypeResponse.model_validate(row)
        """
        match = next(
            (pt for pt in PLOT_TYPES if pt["name"] == name and pt["is_active"]), None
        )
        if match is None:
            raise self._build_error(
                code="NOT_FOUND",
                message=f"Plot type '{name}' not found.",
                details={"name": name},
                status_code=404,
            )
        return PlotTypeResponse(**match)

    def create_plot_type(self, body: PlotTypeCreate) -> PlotTypeResponse:
        """
        Insert a new plot type record.

        Raises APIError 409 on duplicate machine name.

        TODO (DB):
            existing = db.query(PlotTypeModel).filter(PlotTypeModel.name == body.name).first()
            if existing:
                raise self._build_error(...)
            row = PlotTypeModel(**body.model_dump())
            db.add(row)
            db.commit()
            db.refresh(row)
            return PlotTypeResponse.model_validate(row)
        """
        if any(pt["name"] == body.name for pt in PLOT_TYPES):
            raise self._build_error(
                code="CONFLICT",
                message=f"A plot type named '{body.name}' already exists.",
                details={"field": "name"},
                status_code=409,
            )
        new_id = max((pt["id"] for pt in PLOT_TYPES), default=0) + 1
        record = {"id": new_id, **body.model_dump()}
        PLOT_TYPES.append(record)
        return PlotTypeResponse(**record)

    # ------------------------------------------------------------------
    # Shared private helper — identical signature to UploadService._build_error
    # ------------------------------------------------------------------

    def _build_error(
        self,
        *,
        code: str,
        message: str,
        details: dict,
        status_code: int,
    ) -> APIError:
        return APIError(
            status_code=status_code,
            code=code,
            message=message,
            details=details,
            request_id=f"req_{uuid4().hex[:8]}",
        )


# =============================================================================
# In-memory placeholder — DELETE when database is connected
# =============================================================================

COLORS: list[dict] = [
    {"id": 1,  "name": "Crimson Red",   "hex_code": "#DC143C", "is_active": True},
    {"id": 2,  "name": "Sky Blue",      "hex_code": "#87CEEB", "is_active": True},
    {"id": 3,  "name": "Forest Green",  "hex_code": "#228B22", "is_active": True},
    {"id": 4,  "name": "Sunflower",     "hex_code": "#FFC300", "is_active": True},
    {"id": 5,  "name": "Grape Purple",  "hex_code": "#6A0DAD", "is_active": True},
    {"id": 6,  "name": "Coral Orange",  "hex_code": "#FF6B6B", "is_active": True},
    {"id": 7,  "name": "Teal",          "hex_code": "#008080", "is_active": True},
    {"id": 8,  "name": "Slate Gray",    "hex_code": "#708090", "is_active": True},
    {"id": 9,  "name": "Hot Pink",      "hex_code": "#FF69B4", "is_active": True},
    {"id": 10, "name": "Midnight Blue", "hex_code": "#191970", "is_active": True},
]

PLOT_TYPES: list[dict] = [
    {
        "id": 1, "name": "bar", "display_name": "Bar Chart", "is_active": True,
        "description": "Compares values across discrete categories using rectangular bars.",
        "supported_channels": ["color", "size", "position"],
    },
    {
        "id": 2, "name": "line", "display_name": "Line Chart", "is_active": True,
        "description": "Displays data points connected by lines to show trends over time.",
        "supported_channels": ["color", "shape", "size", "position"],
    },
    {
        "id": 3, "name": "scatter", "display_name": "Scatter Plot", "is_active": True,
        "description": "Plots individual points on two axes to reveal relationships or clusters.",
        "supported_channels": ["color", "shape", "size", "position"],
    },
    {
        "id": 4, "name": "pie", "display_name": "Pie Chart", "is_active": True,
        "description": "Shows proportional slices of a whole. Best for a small number of categories.",
        "supported_channels": ["color", "size"],
    },
    {
        "id": 5, "name": "histogram", "display_name": "Histogram", "is_active": True,
        "description": "Groups numeric data into bins to show the distribution of a variable.",
        "supported_channels": ["color", "size", "position"],
    },
    {
        "id": 6, "name": "box", "display_name": "Box Plot", "is_active": True,
        "description": "Summarises distribution using quartiles and highlights outliers.",
        "supported_channels": ["color", "size", "position"],
    },
]