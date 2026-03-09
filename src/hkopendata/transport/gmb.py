"""Hong Kong Green Minibus (GMB) public API client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal, TypeAlias

import httpx
from annotated_types import Gt
from typing_extensions import NotRequired, TypedDict

from ..types import ApiResponse, DataTimestamp
from ..utils import DEFAULT_JSON_HEADERS, GetJsonError, Result, _get_json, _Parser

API_BASE = "https://data.etagmb.gov.hk"

Region = Literal["HKI", "KLN", "NT"]
"""GMB region code."""
RouteCode: TypeAlias = str
"""Route designator unique within a region, e.g. `69`, `12A`, or `11M`."""
RouteId: TypeAlias = Annotated[int, Gt(0)]
"""Route identifier, e.g. `2000410`."""
RouteSeq: TypeAlias = Annotated[int, Gt(0)]
"""Direction selector within a route.

Usually `1` or `2`; circular routes usually use `1`.
"""
StopId: TypeAlias = Annotated[int, Gt(0)]
"""Stop identifier, e.g. `20003337`."""
StopSeq: TypeAlias = Annotated[int, Gt(0)]
"""1-based stop order within a route sequence, e.g. `1`."""
EtaSeq: TypeAlias = Annotated[int, Gt(0)]
"""1-based ETA row order within a route-stop response."""
Timestamp: TypeAlias = DataTimestamp
"""ISO 8601 timestamp used by the GMB API, e.g. `2020-12-28T15:20:00.000+08:00`."""
LastUpdateDate: TypeAlias = Timestamp
"""Last-update timestamp returned by the `/last-update/*` endpoints."""


class RoutesByRegion(TypedDict):
    HKI: list[RouteCode]
    KLN: list[RouteCode]
    NT: list[RouteCode]


class RoutesAllData(TypedDict):
    """Payload for `GET /route`."""

    routes: RoutesByRegion
    data_timestamp: Timestamp


class RoutesRegionalData(TypedDict):
    """Payload for `GET /route/{region}`."""

    routes: list[RouteCode]
    data_timestamp: Timestamp


class Headway(TypedDict):
    weekdays: list[bool]
    public_holiday: bool
    headway_seq: int
    start_time: str
    end_time: str | None
    frequency: int | None
    frequency_upper: int | None


class Direction(TypedDict):
    route_seq: RouteSeq
    orig_tc: str
    orig_sc: str
    orig_en: str
    dest_tc: str
    dest_sc: str
    dest_en: str
    remarks_tc: str | None
    remarks_sc: str | None
    remarks_en: str | None
    headways: list[Headway]
    data_timestamp: Timestamp


class RouteVariant(TypedDict):
    """One route variant under a route code."""

    region: NotRequired[Region]
    route_code: NotRequired[RouteCode]
    route_id: RouteId
    description_tc: str
    description_sc: str
    description_en: str
    directions: list[Direction]
    data_timestamp: Timestamp


class StopCoordinates(TypedDict):
    latitude: float
    longitude: float


class StopCoordinateSystems(TypedDict):
    wgs84: StopCoordinates
    hk80: StopCoordinates


class StopData(TypedDict):
    """GMB stop details."""

    coordinates: StopCoordinateSystems
    enabled: bool
    remarks_tc: str | None
    remarks_sc: str | None
    remarks_en: str | None
    data_timestamp: Timestamp


class RouteStop(TypedDict):
    stop_seq: StopSeq
    stop_id: StopId
    name_tc: str
    name_sc: str
    name_en: str


class RouteStopsData(TypedDict):
    route_stops: list[RouteStop]
    data_timestamp: Timestamp


class StopRoute(TypedDict):
    route_id: RouteId
    route_seq: RouteSeq
    stop_seq: StopSeq
    name_tc: str
    name_sc: str
    name_en: str


class EtaEntry(TypedDict):
    eta_seq: EtaSeq
    diff: int
    timestamp: Timestamp
    remarks_tc: str | None
    remarks_sc: str | None
    remarks_en: str | None


class RouteStopEtaBySeqEnabled(TypedDict):
    enabled: Literal[True]
    stop_id: StopId
    eta: list[EtaEntry]


class RouteStopEtaBySeqDisabled(TypedDict):
    enabled: Literal[False]
    stop_id: StopId
    description_tc: str
    description_sc: str
    description_en: str


class RouteStopEtaOccurrenceEnabled(TypedDict):
    enabled: Literal[True]
    route_seq: RouteSeq
    stop_seq: StopSeq
    eta: list[EtaEntry]


class RouteStopEtaOccurrenceDisabled(TypedDict):
    enabled: Literal[False]
    route_seq: RouteSeq
    stop_seq: StopSeq
    description_tc: str
    description_sc: str
    description_en: str


class StopEtaRouteEnabled(TypedDict):
    enabled: Literal[True]
    route_id: RouteId
    route_seq: RouteSeq
    stop_seq: StopSeq
    eta: list[EtaEntry]


class StopEtaRouteDisabled(TypedDict):
    enabled: Literal[False]
    route_id: RouteId
    route_seq: RouteSeq
    stop_seq: StopSeq
    description_tc: str
    description_sc: str
    description_en: str


class RouteLastUpdate(TypedDict):
    route_id: RouteId
    last_update_date: LastUpdateDate


class StopLastUpdate(TypedDict):
    stop_id: StopId
    last_update_date: LastUpdateDate


class RouteStopLastUpdate(TypedDict):
    route_id: RouteId
    route_seq: RouteSeq
    last_update_date: LastUpdateDate


class LastUpdateData(TypedDict):
    last_update_date: LastUpdateDate


RouteListResponse: TypeAlias = ApiResponse[RoutesAllData | RoutesRegionalData]
RouteResponse: TypeAlias = ApiResponse[list[RouteVariant]]
StopResponse: TypeAlias = ApiResponse[StopData]
RouteStopsResponse: TypeAlias = ApiResponse[RouteStopsData]
StopRoutesResponse: TypeAlias = ApiResponse[list[StopRoute]]
RouteStopEtaBySeqResponse: TypeAlias = ApiResponse[
    RouteStopEtaBySeqEnabled | RouteStopEtaBySeqDisabled
]
RouteStopEtaByStopResponse: TypeAlias = ApiResponse[
    list[RouteStopEtaOccurrenceEnabled | RouteStopEtaOccurrenceDisabled]
]
StopEtaResponse: TypeAlias = ApiResponse[
    list[StopEtaRouteEnabled | StopEtaRouteDisabled]
]
RouteLastUpdatesResponse: TypeAlias = ApiResponse[list[RouteLastUpdate]]
StopLastUpdatesResponse: TypeAlias = ApiResponse[list[StopLastUpdate]]
RouteStopLastUpdatesResponse: TypeAlias = ApiResponse[list[RouteStopLastUpdate]]
RouteDirectionLastUpdateResponse: TypeAlias = ApiResponse[list[RouteStopLastUpdate]]
LastUpdateResponse: TypeAlias = ApiResponse[LastUpdateData]


@dataclass(frozen=True, slots=True)
class RouteListRequest:
    region: Region | None = None


@dataclass(frozen=True, slots=True)
class RouteByRegionRequest:
    region: Region
    route_code: RouteCode


@dataclass(frozen=True, slots=True)
class RouteByIdRequest:
    route_id: RouteId


@dataclass(frozen=True, slots=True)
class StopRequest:
    stop_id: StopId


@dataclass(frozen=True, slots=True)
class RouteStopsRequest:
    route_id: RouteId
    route_seq: RouteSeq


@dataclass(frozen=True, slots=True)
class StopRoutesRequest:
    stop_id: StopId


@dataclass(frozen=True, slots=True)
class RouteStopEtaBySeqRequest:
    """Route-stop ETA request by `(route_id, route_seq, stop_seq)`."""

    route_id: RouteId
    route_seq: RouteSeq
    stop_seq: StopSeq


@dataclass(frozen=True, slots=True)
class RouteStopEtaByStopRequest:
    """Route-stop ETA request by `(route_id, stop_id)`."""

    route_id: RouteId
    stop_id: StopId


@dataclass(frozen=True, slots=True)
class StopEtaRequest:
    stop_id: StopId


@dataclass(frozen=True, slots=True)
class RouteLastUpdatesRequest:
    region: Region | None = None


@dataclass(frozen=True, slots=True)
class RouteLastUpdateByRegionRequest:
    region: Region
    route_code: RouteCode


@dataclass(frozen=True, slots=True)
class RouteLastUpdateByIdRequest:
    route_id: RouteId


@dataclass(frozen=True, slots=True)
class RouteDirectionLastUpdateRequest:
    route_id: RouteId
    route_seq: RouteSeq


@dataclass(frozen=True, slots=True)
class StopLastUpdateRequest:
    stop_id: StopId


@dataclass(frozen=True, slots=True)
class RouteStopLastUpdateRequest:
    route_id: RouteId
    route_seq: RouteSeq


route_list_parse = _Parser[RouteListResponse].parse_json
route_parse = _Parser[RouteResponse].parse_json
stop_parse = _Parser[StopResponse].parse_json
route_stops_parse = _Parser[RouteStopsResponse].parse_json
stop_routes_parse = _Parser[StopRoutesResponse].parse_json
route_stop_eta_by_seq_parse = _Parser[RouteStopEtaBySeqResponse].parse_json
route_stop_eta_by_stop_parse = _Parser[RouteStopEtaByStopResponse].parse_json
stop_eta_parse = _Parser[StopEtaResponse].parse_json
route_last_updates_parse = _Parser[RouteLastUpdatesResponse].parse_json
stop_last_updates_parse = _Parser[StopLastUpdatesResponse].parse_json
route_stop_last_updates_parse = _Parser[RouteStopLastUpdatesResponse].parse_json
route_direction_last_update_parse = _Parser[RouteDirectionLastUpdateResponse].parse_json
last_update_parse = _Parser[LastUpdateResponse].parse_json


async def fetch_routes(
    client: httpx.AsyncClient,
    request: RouteListRequest = RouteListRequest(),
) -> Result[RouteListResponse, GetJsonError]:
    endpoint = (
        f"{API_BASE}/route"
        if request.region is None
        else f"{API_BASE}/route/{request.region}"
    )
    return await _get_json(
        client,
        endpoint,
        parse=route_list_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_route(
    client: httpx.AsyncClient,
    request: RouteByRegionRequest | RouteByIdRequest,
) -> Result[RouteResponse, GetJsonError]:
    if isinstance(request, RouteByRegionRequest):
        endpoint = f"{API_BASE}/route/{request.region}/{request.route_code}"
    else:
        endpoint = f"{API_BASE}/route/{request.route_id}"

    return await _get_json(
        client,
        endpoint,
        parse=route_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_stop(
    client: httpx.AsyncClient,
    request: StopRequest,
) -> Result[StopResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/stop/{request.stop_id}",
        parse=stop_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_route_stops(
    client: httpx.AsyncClient,
    request: RouteStopsRequest,
) -> Result[RouteStopsResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/route-stop/{request.route_id}/{request.route_seq}",
        parse=route_stops_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_stop_routes(
    client: httpx.AsyncClient,
    request: StopRoutesRequest,
) -> Result[StopRoutesResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/stop-route/{request.stop_id}",
        parse=stop_routes_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_route_stop_eta_by_seq(
    client: httpx.AsyncClient,
    request: RouteStopEtaBySeqRequest,
) -> Result[RouteStopEtaBySeqResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/eta/route-stop/{request.route_id}/{request.route_seq}/{request.stop_seq}",
        parse=route_stop_eta_by_seq_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_route_stop_eta_by_stop(
    client: httpx.AsyncClient,
    request: RouteStopEtaByStopRequest,
) -> Result[RouteStopEtaByStopResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/eta/route-stop/{request.route_id}/{request.stop_id}",
        parse=route_stop_eta_by_stop_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_stop_eta(
    client: httpx.AsyncClient,
    request: StopEtaRequest,
) -> Result[StopEtaResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/eta/stop/{request.stop_id}",
        parse=stop_eta_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_last_update_routes(
    client: httpx.AsyncClient,
    request: RouteLastUpdatesRequest = RouteLastUpdatesRequest(),
) -> Result[RouteLastUpdatesResponse, GetJsonError]:
    endpoint = (
        f"{API_BASE}/last-update/route"
        if request.region is None
        else f"{API_BASE}/last-update/route/{request.region}"
    )
    return await _get_json(
        client,
        endpoint,
        parse=route_last_updates_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_last_update_route(
    client: httpx.AsyncClient,
    request: RouteLastUpdateByRegionRequest | RouteLastUpdateByIdRequest,
) -> Result[RouteLastUpdatesResponse, GetJsonError]:
    if isinstance(request, RouteLastUpdateByRegionRequest):
        endpoint = f"{API_BASE}/last-update/route/{request.region}/{request.route_code}"
    else:
        endpoint = f"{API_BASE}/last-update/route/{request.route_id}"

    return await _get_json(
        client,
        endpoint,
        parse=route_last_updates_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_last_update_route_direction(
    client: httpx.AsyncClient,
    request: RouteDirectionLastUpdateRequest,
) -> Result[RouteDirectionLastUpdateResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/last-update/route/{request.route_id}/{request.route_seq}",
        parse=route_direction_last_update_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_last_update_stops(
    client: httpx.AsyncClient,
) -> Result[StopLastUpdatesResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/last-update/stop",
        parse=stop_last_updates_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_last_update_stop(
    client: httpx.AsyncClient,
    request: StopLastUpdateRequest,
) -> Result[LastUpdateResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/last-update/stop/{request.stop_id}",
        parse=last_update_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_last_update_route_stops(
    client: httpx.AsyncClient,
) -> Result[RouteStopLastUpdatesResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/last-update/route-stop",
        parse=route_stop_last_updates_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_last_update_route_stop(
    client: httpx.AsyncClient,
    request: RouteStopLastUpdateRequest,
) -> Result[LastUpdateResponse, GetJsonError]:
    return await _get_json(
        client,
        f"{API_BASE}/last-update/route-stop/{request.route_id}/{request.route_seq}",
        parse=last_update_parse,
        headers=DEFAULT_JSON_HEADERS,
    )
