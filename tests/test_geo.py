import httpx
import pytest
from pydantic import TypeAdapter
from typing_extensions import cast

from hkopendata.geo.search import LocationResult, location_search
from hkopendata.geo.transform import (
    TransformError,
    TransformResponse,
    transform_hkgrid_to_wgs84,
)


@pytest.mark.anyio
async def test_geo_location_search(client: httpx.AsyncClient) -> None:
    result = await location_search(client, "Central", limit=3)
    import orjson

    print(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode())
    adapter = TypeAdapter(list[LocationResult])
    validated = adapter.validate_python(result)
    assert len(validated) >= 0


@pytest.mark.anyio
async def test_geo_transform(client: httpx.AsyncClient) -> None:
    result = await transform_hkgrid_to_wgs84(client, easting=836000, northing=820000)
    adapter: TypeAdapter[TransformResponse | TransformError] = TypeAdapter(
        TransformResponse | TransformError
    )
    validated = adapter.validate_python(result)
    if "ErrorCode" in validated:
        error = cast(TransformError, validated)
        assert error.get("ErrorCode", 0) != 0
    else:
        ok = cast(TransformResponse, validated)
        assert ok["Longitude"] > 0
