from __future__ import annotations

import httpx
import pytest
from pydantic import TypeAdapter

from hkopendata.weather import wxviewer


@pytest.fixture
async def world_places(client: httpx.AsyncClient) -> wxviewer.WorldPlaces:
    places = await wxviewer.fetch_world_places(client)
    TypeAdapter(wxviewer.WorldPlaces).validate_python(places)
    return places


@pytest.fixture
async def sea_state_grids(
    client: httpx.AsyncClient,
) -> wxviewer.GeoJsonFeatureCollection:
    grids = await wxviewer.fetch_sea_state_grids(client)
    TypeAdapter(wxviewer.GeoJsonFeatureCollection).validate_python(grids)
    return grids


@pytest.mark.anyio
async def test_wxviewer_current_basetimes(client: httpx.AsyncClient) -> None:
    basetimes = await wxviewer.fetch_current_basetimes(client, forecast_model=None)
    validated = TypeAdapter(wxviewer.CurrentBasetimes).validate_python(basetimes)
    assert "default" in validated


@pytest.mark.anyio
async def test_wxviewer_world_places_station_ids(
    world_places: wxviewer.WorldPlaces,
) -> None:
    station_ids = list(wxviewer.extract_world_place_station_ids(world_places))
    assert len(station_ids) > 0


@pytest.mark.anyio
async def test_wxviewer_forecast_detail_filter(
    client: httpx.AsyncClient,
    world_places: wxviewer.WorldPlaces,
) -> None:
    station_ids = wxviewer.extract_world_place_station_ids(world_places)
    forecast = await wxviewer.fetch_forecast_detail(client)
    TypeAdapter(wxviewer.ForecastDetailResponse).validate_python(forecast)
    selection = wxviewer.filter_forecast_detail_by_places(forecast, station_ids)
    assert len(selection.stations) > 0
    assert selection.window.start is not None
    assert selection.window.end is not None


@pytest.mark.anyio
async def test_wxviewer_tc_tracks(client: httpx.AsyncClient) -> None:
    basetimes = await wxviewer.fetch_current_basetimes(client, forecast_model=None)
    tc_basetime = basetimes.get("tc_track")
    if not tc_basetime:
        return
    tracks = await wxviewer.fetch_tc_tracks(client, tc_basetime)
    TypeAdapter(wxviewer.TCTracksResponse).validate_python(tracks)


@pytest.mark.anyio
async def test_wxviewer_sea_state_merge(
    client: httpx.AsyncClient,
    sea_state_grids: wxviewer.GeoJsonFeatureCollection,
) -> None:
    sea_state = await wxviewer.fetch_sea_state_forecast_detail(client)
    sea_current = await wxviewer.fetch_sea_current_forecast_detail(client)
    TypeAdapter(wxviewer.SeaStateForecastDetailResponse).validate_python(sea_state)
    TypeAdapter(wxviewer.SeaCurrentForecastDetailResponse).validate_python(sea_current)
    sea_state_selection = wxviewer.filter_sea_state_forecast_detail(
        sea_state, sea_state_grids
    )
    sea_current_filtered = wxviewer.filter_sea_current_forecast_detail(
        sea_current, sea_state_grids
    )
    assert len(sea_state_selection.grids) > 0
    grid_id = next(iter(sea_state_selection.grids.keys()))
    merged = list(
        wxviewer.merge_sea_state_and_current(
            sea_state_selection.grids[grid_id],
            sea_current_filtered.get(grid_id),
        )
    )
    assert len(merged) > 0


@pytest.mark.anyio
async def test_wxviewer_sccw_detail(client: httpx.AsyncClient) -> None:
    detail = await wxviewer.fetch_sccw_detail(client, lang_suffix="")
    TypeAdapter(wxviewer.SCCWDetailResponse).validate_python(detail)


@pytest.mark.anyio
async def test_wxviewer_asset_bytes(client: httpx.AsyncClient) -> None:
    payload = await wxviewer.fetch_wxviewer_asset_bytes(
        client, "data/config/world-places.json"
    )
    assert payload
    assert b"features" in payload
