from typing import NamedTuple, cast

import httpx
import pytest
from pydantic import TypeAdapter

from hkopendata.transport import gmb
from hkopendata.utils import with_retry

fetch_routes = with_retry(gmb.fetch_routes)
fetch_route = with_retry(gmb.fetch_route)
fetch_stop = with_retry(gmb.fetch_stop)
fetch_route_stops = with_retry(gmb.fetch_route_stops)
fetch_stop_routes = with_retry(gmb.fetch_stop_routes)
fetch_route_stop_eta_by_seq = with_retry(gmb.fetch_route_stop_eta_by_seq)
fetch_route_stop_eta_by_stop = with_retry(gmb.fetch_route_stop_eta_by_stop)
fetch_stop_eta = with_retry(gmb.fetch_stop_eta)
fetch_last_update_routes = with_retry(gmb.fetch_last_update_routes)
fetch_last_update_route = with_retry(gmb.fetch_last_update_route)
fetch_last_update_route_direction = with_retry(gmb.fetch_last_update_route_direction)
fetch_last_update_stops = with_retry(gmb.fetch_last_update_stops)
fetch_last_update_stop = with_retry(gmb.fetch_last_update_stop)
fetch_last_update_route_stops = with_retry(gmb.fetch_last_update_route_stops)
fetch_last_update_route_stop = with_retry(gmb.fetch_last_update_route_stop)


class SampleRouteContext(NamedTuple):
    region: gmb.Region
    route_code: gmb.RouteCode
    variant: gmb.RouteVariant
    first_stop: gmb.RouteStop


@pytest.fixture
async def sample_route_context(
    client: httpx.AsyncClient,
) -> SampleRouteContext:
    region: gmb.Region = "HKI"
    regional_routes_response = (
        await fetch_routes(client, gmb.RouteListRequest(region=region))
    ).unwrap()
    TypeAdapter(gmb.RouteListResponse).validate_python(regional_routes_response)
    regional_routes_data = cast(
        gmb.RoutesRegionalData, regional_routes_response["data"]
    )

    route_code = regional_routes_data["routes"][0]
    route_response = (
        await fetch_route(
            client,
            gmb.RouteByRegionRequest(region=region, route_code=route_code),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteResponse).validate_python(route_response)

    variant = route_response["data"][0]
    direction = variant["directions"][0]
    route_stops_response = (
        await fetch_route_stops(
            client,
            gmb.RouteStopsRequest(variant["route_id"], direction["route_seq"]),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteStopsResponse).validate_python(route_stops_response)

    return SampleRouteContext(
        region=region,
        route_code=route_code,
        variant=variant,
        first_stop=route_stops_response["data"]["route_stops"][0],
    )


@pytest.mark.anyio
async def test_gmb_routes_all_regions(client: httpx.AsyncClient) -> None:
    all_routes_response = (await fetch_routes(client)).unwrap()
    TypeAdapter(gmb.RouteListResponse).validate_python(all_routes_response)
    all_routes_data = cast(gmb.RoutesAllData, all_routes_response["data"])

    assert len(all_routes_data["routes"]["HKI"]) > 0
    assert len(all_routes_data["routes"]["KLN"]) > 0
    assert len(all_routes_data["routes"]["NT"]) > 0


@pytest.mark.anyio
async def test_gmb_routes_by_region(client: httpx.AsyncClient) -> None:
    first_region: gmb.Region = "HKI"
    regional_routes_response = (
        await fetch_routes(client, gmb.RouteListRequest(region=first_region))
    ).unwrap()
    TypeAdapter(gmb.RouteListResponse).validate_python(regional_routes_response)
    regional_routes_data = cast(
        gmb.RoutesRegionalData, regional_routes_response["data"]
    )

    assert len(regional_routes_data["routes"]) > 0


@pytest.mark.anyio
async def test_gmb_route_lookup_by_region(
    sample_route_context: SampleRouteContext,
) -> None:
    region = sample_route_context.region
    route_code = sample_route_context.route_code
    variant = sample_route_context.variant

    assert variant["route_id"] > 0
    assert len(variant["directions"]) > 0
    assert variant.get("region", region) == region
    assert variant.get("route_code", route_code) == route_code


@pytest.mark.anyio
async def test_gmb_route_lookup_by_id_matches_region_lookup(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant

    route_response = (
        await fetch_route(client, gmb.RouteByIdRequest(route_id=variant["route_id"]))
    ).unwrap()
    TypeAdapter(gmb.RouteResponse).validate_python(route_response)

    assert any(
        item["route_id"] == variant["route_id"] for item in route_response["data"]
    )


@pytest.mark.anyio
async def test_gmb_route_stops_are_present(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant
    first_stop = sample_route_context.first_stop

    direction = variant["directions"][0]
    route_id = variant["route_id"]
    route_stops_response = (
        await fetch_route_stops(
            client,
            gmb.RouteStopsRequest(route_id, direction["route_seq"]),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteStopsResponse).validate_python(route_stops_response)

    route_stops = route_stops_response["data"]["route_stops"]
    assert len(route_stops) > 0
    assert route_stops[0]["stop_seq"] == 1
    assert first_stop["stop_id"] > 0


@pytest.mark.anyio
async def test_gmb_stop_lookup(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    first_stop = sample_route_context.first_stop

    stop_id = first_stop["stop_id"]
    stop_response = (await fetch_stop(client, gmb.StopRequest(stop_id))).unwrap()
    TypeAdapter(gmb.StopResponse).validate_python(stop_response)

    assert stop_response["data"]["enabled"] in {True, False}


@pytest.mark.anyio
async def test_gmb_stop_routes_include_sample_route(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant
    first_stop = sample_route_context.first_stop

    direction = variant["directions"][0]
    stop_id = first_stop["stop_id"]
    stop_seq = first_stop["stop_seq"]

    stop_routes_response = (
        await fetch_stop_routes(client, gmb.StopRoutesRequest(stop_id))
    ).unwrap()
    TypeAdapter(gmb.StopRoutesResponse).validate_python(stop_routes_response)

    assert any(
        stop_route["route_id"] == variant["route_id"]
        and stop_route["route_seq"] == direction["route_seq"]
        and stop_route["stop_seq"] == stop_seq
        for stop_route in stop_routes_response["data"]
    )


@pytest.mark.anyio
async def test_gmb_route_stop_eta_by_seq(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant
    first_stop = sample_route_context.first_stop

    route_id = variant["route_id"]
    route_seq = variant["directions"][0]["route_seq"]
    stop_id = first_stop["stop_id"]
    stop_seq = first_stop["stop_seq"]

    route_stop_eta_by_seq_response = (
        await fetch_route_stop_eta_by_seq(
            client,
            gmb.RouteStopEtaBySeqRequest(route_id, route_seq, stop_seq),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteStopEtaBySeqResponse).validate_python(
        route_stop_eta_by_seq_response
    )

    eta_data = route_stop_eta_by_seq_response["data"]
    assert eta_data["stop_id"] == stop_id
    if eta_data["enabled"]:
        assert [eta["eta_seq"] for eta in eta_data["eta"]] == list(
            range(1, len(eta_data["eta"]) + 1)
        )
    else:
        assert eta_data["description_en"] != ""


@pytest.mark.anyio
async def test_gmb_route_stop_eta_by_stop(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant
    first_stop = sample_route_context.first_stop

    route_id = variant["route_id"]
    route_seq = variant["directions"][0]["route_seq"]
    stop_id = first_stop["stop_id"]
    stop_seq = first_stop["stop_seq"]

    route_stop_eta_by_stop_response = (
        await fetch_route_stop_eta_by_stop(
            client,
            gmb.RouteStopEtaByStopRequest(route_id, stop_id),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteStopEtaByStopResponse).validate_python(
        route_stop_eta_by_stop_response
    )

    assert any(
        occurrence["route_seq"] == route_seq and occurrence["stop_seq"] == stop_seq
        for occurrence in route_stop_eta_by_stop_response["data"]
    )


@pytest.mark.anyio
async def test_gmb_stop_eta_contains_sample_route(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant
    first_stop = sample_route_context.first_stop

    route_id = variant["route_id"]
    route_seq = variant["directions"][0]["route_seq"]
    stop_seq = first_stop["stop_seq"]
    stop_id = first_stop["stop_id"]

    stop_eta_response = (
        await fetch_stop_eta(client, gmb.StopEtaRequest(stop_id))
    ).unwrap()
    TypeAdapter(gmb.StopEtaResponse).validate_python(stop_eta_response)

    assert any(
        route_eta["route_id"] == route_id
        and route_eta["route_seq"] == route_seq
        and route_eta["stop_seq"] == stop_seq
        for route_eta in stop_eta_response["data"]
    )


@pytest.mark.anyio
async def test_gmb_last_update_routes(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    region = sample_route_context.region
    route_code = sample_route_context.route_code
    variant = sample_route_context.variant

    route_updates_response = (await fetch_last_update_routes(client)).unwrap()
    TypeAdapter(gmb.RouteLastUpdatesResponse).validate_python(route_updates_response)
    assert len(route_updates_response["data"]) > 0

    regional_updates_result = await fetch_last_update_routes(
        client,
        gmb.RouteLastUpdatesRequest(region=region),
    )
    if regional_updates_result.is_err():
        pytest.skip("live GMB regional last-update endpoint currently returns HTTP 500")

    regional_updates_response = regional_updates_result.unwrap()
    TypeAdapter(gmb.RouteLastUpdatesResponse).validate_python(regional_updates_response)
    assert len(regional_updates_response["data"]) > 0

    route_update_response = (
        await fetch_last_update_route(
            client,
            gmb.RouteLastUpdateByRegionRequest(region=region, route_code=route_code),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteLastUpdatesResponse).validate_python(route_update_response)
    assert any(
        item["route_id"] == variant["route_id"]
        for item in route_update_response["data"]
    )


@pytest.mark.anyio
async def test_gmb_last_update_route_by_id_and_direction(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant

    route_update_response = (
        await fetch_last_update_route(
            client,
            gmb.RouteLastUpdateByIdRequest(route_id=variant["route_id"]),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteLastUpdatesResponse).validate_python(route_update_response)
    assert any(
        item["route_id"] == variant["route_id"]
        for item in route_update_response["data"]
    )

    direction_update_response = (
        await fetch_last_update_route_direction(
            client,
            gmb.RouteDirectionLastUpdateRequest(
                route_id=variant["route_id"],
                route_seq=variant["directions"][0]["route_seq"],
            ),
        )
    ).unwrap()
    TypeAdapter(gmb.RouteDirectionLastUpdateResponse).validate_python(
        direction_update_response
    )
    assert any(
        item["route_id"] == variant["route_id"]
        and item["route_seq"] == variant["directions"][0]["route_seq"]
        for item in direction_update_response["data"]
    )


@pytest.mark.anyio
async def test_gmb_last_update_stops(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    first_stop = sample_route_context.first_stop

    stop_updates_response = (await fetch_last_update_stops(client)).unwrap()
    TypeAdapter(gmb.StopLastUpdatesResponse).validate_python(stop_updates_response)
    assert any(
        item["stop_id"] == first_stop["stop_id"]
        for item in stop_updates_response["data"]
    )

    stop_update_response = (
        await fetch_last_update_stop(
            client,
            gmb.StopLastUpdateRequest(stop_id=first_stop["stop_id"]),
        )
    ).unwrap()
    TypeAdapter(gmb.LastUpdateResponse).validate_python(stop_update_response)
    assert stop_update_response["data"]["last_update_date"] != ""


@pytest.mark.anyio
async def test_gmb_last_update_route_stops(
    client: httpx.AsyncClient,
    sample_route_context: SampleRouteContext,
) -> None:
    variant = sample_route_context.variant

    route_seq = variant["directions"][0]["route_seq"]

    route_stop_updates_response = (await fetch_last_update_route_stops(client)).unwrap()
    TypeAdapter(gmb.RouteStopLastUpdatesResponse).validate_python(
        route_stop_updates_response
    )
    assert any(
        item["route_id"] == variant["route_id"] and item["route_seq"] == route_seq
        for item in route_stop_updates_response["data"]
    )

    route_stop_update_response = (
        await fetch_last_update_route_stop(
            client,
            gmb.RouteStopLastUpdateRequest(
                route_id=variant["route_id"],
                route_seq=route_seq,
            ),
        )
    ).unwrap()
    TypeAdapter(gmb.LastUpdateResponse).validate_python(route_stop_update_response)
    assert route_stop_update_response["data"]["last_update_date"] != ""
