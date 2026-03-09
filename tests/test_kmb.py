import httpx
import pytest
from pydantic import TypeAdapter

from hkopendata.transport import kmb


@pytest.fixture
async def kmb_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(http1=True, http2=False, timeout=30) as client:
        yield client


@pytest.mark.anyio
async def test_kmb_routes(kmb_client: httpx.AsyncClient) -> None:
    routes_response = await kmb.fetch_routes(kmb_client)
    TypeAdapter(kmb.RouteListResponse).validate_python(routes_response)
    assert len(routes_response["data"]) > 0

    first = routes_response["data"][0]
    route_response = await kmb.fetch_route(
        kmb_client,
        kmb.RouteRequest(
            route=first["route"],
            bound=first["bound"],
            service_type=first["service_type"],
        ),
    )
    TypeAdapter(kmb.RouteResponse).validate_python(route_response)
    assert route_response["data"]["route"] == first["route"]


@pytest.mark.anyio
async def test_kmb_stops(kmb_client: httpx.AsyncClient) -> None:
    stops_response = await kmb.fetch_stops(kmb_client)
    TypeAdapter(kmb.StopListResponse).validate_python(stops_response)
    assert len(stops_response["data"]) > 0

    first = stops_response["data"][0]
    stop_response = await kmb.fetch_stop(kmb_client, kmb.StopRequest(first["stop"]))
    TypeAdapter(kmb.StopResponse).validate_python(stop_response)
    assert stop_response["data"]["stop"] == first["stop"]


@pytest.mark.anyio
async def test_kmb_route_stops(kmb_client: httpx.AsyncClient) -> None:
    stops_response = await kmb.fetch_route_stops(
        kmb_client,
        kmb.RouteStopsRequest(route="1A", bound="I", service_type="1"),
    )
    TypeAdapter(kmb.RouteStopListResponse).validate_python(stops_response)
    assert len(stops_response["data"]) > 0


@pytest.mark.anyio
async def test_kmb_eta(kmb_client: httpx.AsyncClient) -> None:
    route_eta_response = await kmb.fetch_route_eta(
        kmb_client,
        kmb.RouteEtaRequest(route="1A", service_type="1"),
    )
    TypeAdapter(kmb.RouteEtaResponse).validate_python(route_eta_response)

    route_stops_response = await kmb.fetch_route_stops(
        kmb_client,
        kmb.RouteStopsRequest(route="1A", bound="I", service_type="1"),
    )
    stop_id = route_stops_response["data"][0]["stop"]

    stop_eta_response = await kmb.fetch_stop_eta(
        kmb_client, kmb.StopEtaRequest(stop_id)
    )
    TypeAdapter(kmb.StopEtaResponse).validate_python(stop_eta_response)
    assert len(stop_eta_response["data"]) > 0
