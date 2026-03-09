"""The Kowloon Motor Bus Company (1933) Limited public metadata / ETA API.

This API is more reliable under HTTP/1 than HTTP/2 in tests.

The only hidden normalization is the URL-path where the live single-route
and route-stop endpoints expect `inbound` / `outbound` in the path while the
payload itself still speaks in `I` / `O`.

Ref: Data Dictionary v1.02 (2021-05-10)
See: <https://data.etabus.gov.hk/datagovhk/kmb_eta_data_dictionary.pdf>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal, TypeAlias

import httpx
from annotated_types import Gt
from typing_extensions import NotRequired, TypedDict

from ..types import (
    ApiResponse,
    DataTimestamp,
    LatitudeDeg,
    LongitudeDeg,
)
from ..utils import (
    DEFAULT_JSON_HEADERS,
    GetJsonError,
    Result,
    _get_json,
    _Parser,
)

API_BASE = "https://data.etabus.gov.hk/v1/transport/kmb"

CompanyCode = Literal["KMB", "LWB"]
Direction = Literal["I", "O"]
"""Payload direction code. `I` means inbound and `O` means outbound."""
DirectionPath = Literal["inbound", "outbound"]
"""Path-only direction segment used by the live `/route/*` and `/route-stop/*` URLs."""
ServiceType: TypeAlias = str
"""Route variant code from metadata endpoints, usually a string like `"1"` or `"2"`."""
EtaServiceType: TypeAlias = Annotated[int, Gt(0)]
"""Route variant code from ETA endpoints, e.g. `1`."""
RouteStopSeq: TypeAlias = str
"""1-based stop order within `/route-stop`, kept as API text like `"1"` or `"12"`."""
EtaStopSeq: TypeAlias = Annotated[int, Gt(0)]
"""1-based stop order within ETA payloads, e.g. `1`."""
EtaSeq: TypeAlias = Annotated[int, Gt(0)]
"""1-based ETA row order for the same stop."""
StopId: TypeAlias = str
"""KMB stop identifier, usually 16 uppercase hex-like chars such as
`18492910339410B1`."""


class Route(TypedDict):
    """One route variant row from the KMB metadata API."""

    route: str
    bound: Direction
    service_type: ServiceType
    orig_en: str
    orig_tc: str
    orig_sc: str
    dest_en: str
    dest_tc: str
    dest_sc: str
    co: NotRequired[CompanyCode]
    data_timestamp: NotRequired[DataTimestamp]


class Stop(TypedDict):
    """One stop row from the KMB metadata API."""

    stop: StopId
    name_tc: str
    name_en: str
    name_sc: str
    lat: LatitudeDeg[str]
    long: LongitudeDeg[str]
    data_timestamp: NotRequired[DataTimestamp]


class RouteStop(TypedDict):
    """One stop membership row within a specific route variant."""

    route: str
    bound: Direction
    service_type: ServiceType
    seq: RouteStopSeq
    stop: StopId
    co: NotRequired[CompanyCode]
    dir: NotRequired[Direction]
    data_timestamp: NotRequired[DataTimestamp]


class Eta(TypedDict):
    """One ETA prediction row from either `/route-eta` or `/stop-eta`."""

    co: CompanyCode
    route: str
    dir: Direction
    service_type: EtaServiceType
    seq: EtaStopSeq
    dest_tc: str
    dest_sc: str
    dest_en: str
    eta_seq: EtaSeq
    eta: str | None
    """Estimated time of arrival (ISO 8601). None if invalid/null."""
    rmk_tc: str
    rmk_sc: str
    rmk_en: str
    data_timestamp: DataTimestamp
    stop: NotRequired[StopId]


RouteResponse: TypeAlias = ApiResponse[Route | dict[str, object]]
RouteListResponse: TypeAlias = ApiResponse[list[Route]]
StopResponse: TypeAlias = ApiResponse[Stop | dict[str, object]]
StopListResponse: TypeAlias = ApiResponse[list[Stop]]
RouteStopListResponse: TypeAlias = ApiResponse[list[RouteStop]]
RouteEtaResponse: TypeAlias = ApiResponse[list[Eta]]
StopEtaResponse: TypeAlias = ApiResponse[list[Eta]]


@dataclass(frozen=True, slots=True)
class RouteRequest:
    """Request the raw `/route/{route}/{direction}/{service_type}` envelope.

    Example: route `1A`, bound `I`, service type `"1"`.
    """

    route: str
    bound: Direction
    service_type: ServiceType = "1"


@dataclass(frozen=True, slots=True)
class StopRequest:
    """Request the raw `/stop/{stop_id}` envelope for one stop.

    Example stop id: `18492910339410B1`.
    """

    stop_id: StopId


@dataclass(frozen=True, slots=True)
class RouteStopsRequest:
    """Request the raw `/route-stop/{route}/{direction}/{service_type}` envelope."""

    route: str
    bound: Direction
    service_type: ServiceType = "1"


@dataclass(frozen=True, slots=True)
class RouteEtaRequest:
    """Request the raw `/route-eta/{route}/{service_type}` envelope."""

    route: str
    service_type: ServiceType = "1"


@dataclass(frozen=True, slots=True)
class StopEtaRequest:
    """Request the raw `/stop-eta/{stop_id}` envelope."""

    stop_id: StopId


route_parse = _Parser[RouteResponse].parse_json
route_list_parse = _Parser[RouteListResponse].parse_json
stop_parse = _Parser[StopResponse].parse_json
stop_list_parse = _Parser[StopListResponse].parse_json
route_stop_list_parse = _Parser[RouteStopListResponse].parse_json
route_eta_parse = _Parser[RouteEtaResponse].parse_json
stop_eta_parse = _Parser[StopEtaResponse].parse_json


def _direction_path(bound: Direction) -> DirectionPath:
    """Map payload direction codes to the path segments expected by the live API."""

    return "inbound" if bound == "I" else "outbound"


async def fetch_routes(
    client: httpx.AsyncClient,
) -> Result[RouteListResponse, GetJsonError]:
    """Fetch the raw route-list response.

    The returned object mirrors the public API body exactly, including the
    top-level `type`, `version`, and `generated_timestamp` envelope fields.
    """

    return await _get_json(
        client,
        f"{API_BASE}/route",
        parse=route_list_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_route(
    client: httpx.AsyncClient,
    request: RouteRequest,
) -> Result[RouteResponse, GetJsonError]:
    """Fetch the raw single-route response."""

    return await _get_json(
        client,
        f"{API_BASE}/route/{request.route}/{_direction_path(request.bound)}/{request.service_type}",
        parse=route_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_stops(
    client: httpx.AsyncClient,
) -> Result[StopListResponse, GetJsonError]:
    """Fetch the raw stop-list response."""

    return await _get_json(
        client,
        f"{API_BASE}/stop",
        parse=stop_list_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_stop(
    client: httpx.AsyncClient,
    request: StopRequest,
) -> Result[StopResponse, GetJsonError]:
    """Fetch the raw single-stop response."""

    return await _get_json(
        client,
        f"{API_BASE}/stop/{request.stop_id}",
        parse=stop_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_route_stops(
    client: httpx.AsyncClient,
    request: RouteStopsRequest,
) -> Result[RouteStopListResponse, GetJsonError]:
    """Fetch the raw route-stop-list response."""

    return await _get_json(
        client,
        f"{API_BASE}/route-stop/{request.route}/{_direction_path(request.bound)}/{request.service_type}",
        parse=route_stop_list_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_route_eta(
    client: httpx.AsyncClient,
    request: RouteEtaRequest,
) -> Result[RouteEtaResponse, GetJsonError]:
    """Fetch the raw route-ETA response."""

    return await _get_json(
        client,
        f"{API_BASE}/route-eta/{request.route}/{request.service_type}",
        parse=route_eta_parse,
        headers=DEFAULT_JSON_HEADERS,
    )


async def fetch_stop_eta(
    client: httpx.AsyncClient,
    request: StopEtaRequest,
) -> Result[StopEtaResponse, GetJsonError]:
    """Fetch the raw stop-ETA response."""

    return await _get_json(
        client,
        f"{API_BASE}/stop-eta/{request.stop_id}",
        parse=stop_eta_parse,
        headers=DEFAULT_JSON_HEADERS,
    )
