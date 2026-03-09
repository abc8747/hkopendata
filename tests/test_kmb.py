import httpx
import pytest
from pydantic import TypeAdapter

from hkopendata.transport import kmb
from hkopendata.utils import with_retry

fetch_routes = with_retry(kmb.fetch_routes)
fetch_route = with_retry(kmb.fetch_route)
fetch_stops = with_retry(kmb.fetch_stops)
fetch_stop = with_retry(kmb.fetch_stop)
fetch_route_stops = with_retry(kmb.fetch_route_stops)
fetch_route_eta = with_retry(kmb.fetch_route_eta)
fetch_stop_eta = with_retry(kmb.fetch_stop_eta)


@pytest.mark.anyio
async def test_kmb_routes(client_http1: httpx.AsyncClient) -> None:
    routes_response = (await fetch_routes(client_http1)).unwrap()
    TypeAdapter(kmb.RouteListResponse).validate_python(routes_response)
    assert len(routes_response["data"]) > 0

    first = routes_response["data"][0]
    route_response = (
        await fetch_route(
            client_http1,
            kmb.RouteRequest(
                route=first["route"],
                bound=first["bound"],
                service_type=first["service_type"],
            ),
        )
    ).unwrap()
    TypeAdapter(kmb.RouteResponse).validate_python(route_response)
    assert route_response["data"]["route"] == first["route"]


@pytest.mark.anyio
async def test_kmb_stops(client_http1: httpx.AsyncClient) -> None:
    stops_response = (await fetch_stops(client_http1)).unwrap()
    TypeAdapter(kmb.StopListResponse).validate_python(stops_response)
    assert len(stops_response["data"]) > 0

    first = stops_response["data"][0]
    stop_response = (
        await fetch_stop(
            client_http1,
            kmb.StopRequest(first["stop"]),
        )
    ).unwrap()
    TypeAdapter(kmb.StopResponse).validate_python(stop_response)
    assert stop_response["data"]["stop"] == first["stop"]


@pytest.mark.anyio
async def test_kmb_route_stops(client_http1: httpx.AsyncClient) -> None:
    stops_response = (
        await fetch_route_stops(
            client_http1,
            kmb.RouteStopsRequest(route="1A", bound="I", service_type="1"),
        )
    ).unwrap()
    TypeAdapter(kmb.RouteStopListResponse).validate_python(stops_response)
    assert len(stops_response["data"]) > 0


@pytest.mark.anyio
async def test_kmb_eta(client_http1: httpx.AsyncClient) -> None:
    route_eta_response = (
        await fetch_route_eta(
            client_http1,
            kmb.RouteEtaRequest(route="1A", service_type="1"),
        )
    ).unwrap()
    TypeAdapter(kmb.RouteEtaResponse).validate_python(route_eta_response)

    route_stops_response = (
        await fetch_route_stops(
            client_http1,
            kmb.RouteStopsRequest(route="1A", bound="I", service_type="1"),
        )
    ).unwrap()
    stop_id = route_stops_response["data"][0]["stop"]

    stop_eta_response = (
        await fetch_stop_eta(
            client_http1,
            kmb.StopEtaRequest(stop_id),
        )
    ).unwrap()
    TypeAdapter(kmb.StopEtaResponse).validate_python(stop_eta_response)
    assert len(stop_eta_response["data"]) > 0
