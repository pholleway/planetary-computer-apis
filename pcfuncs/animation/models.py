from datetime import datetime
from typing import Any, Callable, Dict, List
from urllib.parse import quote

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field, validator

from .constants import MAX_FRAMES


def _get_render_options(render_params: str) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for p in render_params.split("&"):
        k, v = p.split("=")
        if k not in result:
            result[k] = []
        result[k].append(v)
    return result


_deltas: Dict[str, Callable[[int], relativedelta]] = {
    "mins": lambda step: relativedelta(minutes=step),
    "hours": lambda step: relativedelta(hours=step),
    "days": lambda step: relativedelta(days=step),
    "weeks": lambda step: relativedelta(weeks=step),
    "months": lambda step: relativedelta(months=step),
    "years": lambda step: relativedelta(years=step),
}


class AnimationRequest(BaseModel):
    bbox: List[float]
    zoom: int
    cql: Dict[str, Any]
    render_params: str
    start: datetime
    duration: int
    step: int
    unit: str
    frames: int
    show_branding: bool = Field(default=True, alias="showBranding")
    show_progressbar: bool = Field(default=True, alias="showProgressBar")

    @validator("render_params")
    def _validate_render_params(cls, v: str) -> str:
        try:
            render_options = _get_render_options(v)
        except Exception:
            raise ValueError("Invalid render_params")
        if "collection" not in render_options:
            raise ValueError("Missing collection in render_params")
        if len(render_options["collection"]) != 1:
            raise ValueError("Multiple collections in render_params")
        return v

    @validator("unit")
    def _validate_unit(cls, v: str) -> str:
        if v not in _deltas:
            raise ValueError(
                "Invalid unit. Must be one of: " + ", ".join(_deltas.keys())
            )
        return v

    def get_collection(self) -> str:
        render_options = _get_render_options(self.render_params)
        return render_options["collection"][0]

    def get_encoded_render_params(self) -> str:
        encoded_options = [
            f"{key}={quote(v)}"
            for key, value in _get_render_options(self.render_params).items()
            for v in value
        ]
        encoded_options.append("tile_scale=2")
        return "&".join(encoded_options)

    def get_valid_frames(self) -> int:
        return min(self.frames, MAX_FRAMES)

    def get_relative_delta(self) -> relativedelta:
        return _deltas[self.unit](self.step)


class AnimationResponse(BaseModel):
    url: str
