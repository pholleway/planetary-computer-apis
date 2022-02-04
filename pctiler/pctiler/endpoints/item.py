from dataclasses import dataclass
from urllib.parse import urljoin

from fastapi import Query, Request, Response
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from titiler.core.factory import MultiBaseTilerFactory

from pccommon.render import COLLECTION_RENDER_CONFIG
from pctiler.colormaps import PCColorMapParams
from pctiler.config import get_settings
from pctiler.reader import ItemSTACReader

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(
    directory=str(resources_files(__package__) / "templates")
)  # type: ignore


def ItemPathParams(
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> str:
    return urljoin(
        get_settings().stac_api_url, f"collections/{collection}/items/{item}"
    )


@dataclass
class MapParams:
    collection: str = Query(..., description="STAC Collection ID")
    item: str = Query(..., description="STAC Item ID")


pc_tile_factory = MultiBaseTilerFactory(
    reader=ItemSTACReader,
    path_dependency=ItemPathParams,
    colormap_dependency=PCColorMapParams,
    router_prefix=get_settings().item_endpoint_prefix,
)


@pc_tile_factory.router.get("/map", response_class=HTMLResponse)
def map(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> Response:
    render_config = COLLECTION_RENDER_CONFIG.get(collection)
    if render_config is None:
        return Response(
            status_code=404,
            content=f"No item map available for collection {collection}",
        )

    qs = render_config.get_full_render_qs(collection, item)
    tilejson_url = pc_tile_factory.url_for(request, "tilejson")
    tilejson_url += f"?{qs}"

    item_url = urljoin(
        get_settings().stac_api_href,
        f"collections/{collection}/items/{item}",
    )

    return templates.TemplateResponse(
        "item_preview.html",
        context={
            "request": request,
            "tileJson": tilejson_url,
            "collectionId": collection,
            "itemId": item,
            "itemUrl": item_url,
        },
    )
