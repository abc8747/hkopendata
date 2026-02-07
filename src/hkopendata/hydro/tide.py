from __future__ import annotations

from typing import cast

import httpx
from typing_extensions import TypedDict

from ..types import HkoStationId, HydroStationId, LatitudeDeg, LongitudeDeg, TideM
from . import TIDE_ENDPOINT, ensure_http1


# TODO: should we convert string fields to int/float so pydantic works?
class TideStation(TypedDict):
    latitude: LatitudeDeg[str]
    longitude: LongitudeDeg[str]
    nameEng: str
    nameSc: str
    nameTc: str
    stationId: HydroStationId
    HKOstationId: HkoStationId
    color: str
    """Hex color code"""


class TideLatestRealtime(TypedDict):
    dateTime: str
    """Example: 2026-02-07 17:13"""
    predData: TideM[str]
    realData: TideM[str]


async def fetch_tide_stations(client: httpx.AsyncClient) -> list[TideStation]:
    ensure_http1(client)
    response = await client.get(f"{TIDE_ENDPOINT}/getLocalStationsData")
    response.raise_for_status()
    return cast(list[TideStation], response.json())


async def fetch_latest_realtime(
    client: httpx.AsyncClient, station_id: HydroStationId
) -> TideLatestRealtime:
    ensure_http1(client)
    response = await client.get(
        f"{TIDE_ENDPOINT}/getLatestRealTime", params={"station": station_id}
    )
    response.raise_for_status()
    return cast(TideLatestRealtime, response.json())
