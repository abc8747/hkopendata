from __future__ import annotations

import httpx
from typing_extensions import NotRequired, TypedDict

from ..types import Hk80Easting, Hk80Northing, LatitudeDeg, LongitudeDeg


class TransformResponse(TypedDict):
    Easting: Hk80Easting[float]
    Northing: Hk80Northing[float]
    Latitude: LatitudeDeg[float]
    Longitude: LongitudeDeg[float]
    GridSystem: str


class TransformError(TypedDict, total=False):
    ErrorCode: int
    ErrorMessage: NotRequired[str]


async def transform_hkgrid_to_wgs84(
    client: httpx.AsyncClient, *, easting: float, northing: float
) -> TransformResponse | TransformError:
    response = await client.get(
        "https://www.geodetic.gov.hk/transform/v2/",
        params={
            "inSys": "hkgrid",
            "outSys": "wgsgeog",
            "Easting": easting,
            "Northing": northing,
        },
    )
    response.raise_for_status()
    return response.json()  # type: ignore
