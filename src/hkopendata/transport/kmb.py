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
from typing import Annotated, Callable, Generic, Literal, TypeAlias, TypeVar

import httpx
from annotated_types import Gt
from typing_extensions import NotRequired, TypedDict

from ..types import LatitudeDeg, LongitudeDeg
from ..utils import ParseError, Result, _Parser

API_BASE = "https://data.etabus.gov.hk/v1/transport/kmb"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

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
GeneratedTimestamp: TypeAlias = str
"""Envelope timestamp in ISO 8601 with offset, e.g. `2026-03-09T14:03:46+08:00`."""
ApiVersion: TypeAlias = str
"""Top-level API version string, currently `"1.0"`."""
StopId: TypeAlias = str
"""KMB stop identifier, usually 16 uppercase hex-like chars such as
`18492910339410B1`."""

T = TypeVar("T")


class BaseResponse(TypedDict, Generic[T]):
    """Common raw response used by the KMB public API."""

    type: str
    version: ApiVersion
    generated_timestamp: GeneratedTimestamp
    data: T


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
    data_timestamp: NotRequired[str]


class Stop(TypedDict):
    """One stop row from the KMB metadata API."""

    stop: StopId
    name_tc: str
    name_en: str
    name_sc: str
    lat: LatitudeDeg[str]
    long: LongitudeDeg[str]
    data_timestamp: NotRequired[str]


class RouteStop(TypedDict):
    """One stop membership row within a specific route variant."""

    route: str
    bound: Direction
    service_type: ServiceType
    seq: RouteStopSeq
    stop: StopId
    co: NotRequired[CompanyCode]
    dir: NotRequired[Direction]
    data_timestamp: NotRequired[str]


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
    data_timestamp: str
    stop: NotRequired[StopId]


RouteResponse: TypeAlias = BaseResponse[Route | dict[str, object]]
RouteListResponse: TypeAlias = BaseResponse[list[Route]]
StopResponse: TypeAlias = BaseResponse[Stop | dict[str, object]]
StopListResponse: TypeAlias = BaseResponse[list[Stop]]
RouteStopListResponse: TypeAlias = BaseResponse[list[RouteStop]]
RouteEtaResponse: TypeAlias = BaseResponse[list[Eta]]
StopEtaResponse: TypeAlias = BaseResponse[list[Eta]]


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


async def _get_json(
    client: httpx.AsyncClient,
    path: str,
    parser: Callable[[Annotated[httpx.Response, T]], Result[T, ParseError]],
) -> T:
    response = await client.get(f"{API_BASE}{path}", headers=DEFAULT_HEADERS)
    return parser(response).unwrap()


async def fetch_routes(
    client: httpx.AsyncClient,
) -> RouteListResponse:
    """Fetch the raw route-list response.

    The returned object mirrors the public API body exactly, including the
    top-level `type`, `version`, and `generated_timestamp` envelope fields.
    """

    return await _get_json(client, "/route", route_list_parse)


async def fetch_route(
    client: httpx.AsyncClient,
    request: RouteRequest,
) -> RouteResponse:
    """Fetch the raw single-route response."""

    return await _get_json(
        client,
        f"/route/{request.route}/{_direction_path(request.bound)}/{request.service_type}",
        route_parse,
    )


async def fetch_stops(
    client: httpx.AsyncClient,
) -> StopListResponse:
    """Fetch the raw stop-list response."""

    return await _get_json(client, "/stop", stop_list_parse)


async def fetch_stop(
    client: httpx.AsyncClient,
    request: StopRequest,
) -> StopResponse:
    """Fetch the raw single-stop response."""

    return await _get_json(client, f"/stop/{request.stop_id}", stop_parse)


async def fetch_route_stops(
    client: httpx.AsyncClient,
    request: RouteStopsRequest,
) -> RouteStopListResponse:
    """Fetch the raw route-stop-list response."""

    return await _get_json(
        client,
        f"/route-stop/{request.route}/{_direction_path(request.bound)}/{request.service_type}",
        route_stop_list_parse,
    )


async def fetch_route_eta(
    client: httpx.AsyncClient,
    request: RouteEtaRequest,
) -> RouteEtaResponse:
    """Fetch the raw route-ETA response."""

    return await _get_json(
        client,
        f"/route-eta/{request.route}/{request.service_type}",
        route_eta_parse,
    )


async def fetch_stop_eta(
    client: httpx.AsyncClient,
    request: StopEtaRequest,
) -> StopEtaResponse:
    """Fetch the raw stop-ETA response."""

    return await _get_json(
        client,
        f"/stop-eta/{request.stop_id}",
        stop_eta_parse,
    )
