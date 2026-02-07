from __future__ import annotations

from typing import Any

import httpx
from typing_extensions import TypedDict

from ..types import Hk80Easting, Hk80Northing


class LocationResult(TypedDict):
    addressZH: str
    nameZH: str
    districtZH: str
    x: Hk80Easting[float]
    y: Hk80Northing[float]
    nameEN: str
    addressEN: str
    districtEN: str


async def location_search(
    client: httpx.AsyncClient, query: str, *, limit: int | None = None
) -> list[LocationResult]:
    params: dict[str, Any] = {"q": query}
    if limit is not None:
        params["limit"] = str(limit)

    response = await client.get(
        "https://geodata.gov.hk/gs/api/v1.0.0/locationSearch",
        params=params,
    )
    response.raise_for_status()
    return response.json()  # type: ignore
