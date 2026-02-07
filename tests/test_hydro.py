import httpx
import pytest
from pydantic import TypeAdapter

from hkopendata.hydro.facilities import Facilities, Facility
from hkopendata.hydro.thematic import ThematicLayer, ThematicLayers
from hkopendata.hydro.tide import (
    TideLatestRealtime,
    TideStation,
    fetch_latest_realtime,
    fetch_tide_stations,
)
from hkopendata.hydro.tiles import OfflineTilesVersion
from hkopendata.hydro.version import Version


@pytest.mark.anyio
async def test_hydro_version(client_http1: httpx.AsyncClient) -> None:
    xml_content = await Version.fetch_raw(client_http1)
    version = Version.from_xml(xml_content)
    assert version.file_version > 0
    assert Version.load() == version


@pytest.mark.anyio
async def test_hydro_tiles(client_http1: httpx.AsyncClient) -> None:
    xml_content = await OfflineTilesVersion.fetch(client_http1)
    tiles_version = OfflineTilesVersion.from_xml(xml_content)
    assert tiles_version.file_path.startswith("http")


@pytest.mark.anyio
async def test_hydro_facilities(client_http1: httpx.AsyncClient) -> None:
    facilities = (await Facilities.fetch(client_http1)).facility_list
    assert len(facilities) > 0
    assert isinstance(facilities[0], Facility)


@pytest.mark.anyio
async def test_hydro_thematic_layers(client_http1: httpx.AsyncClient) -> None:
    layers = (await ThematicLayers.fetch(client_http1)).layer_list
    assert len(layers) > 0
    assert isinstance(layers[0], ThematicLayer)


@pytest.mark.anyio
async def test_hydro_tide(client_http1: httpx.AsyncClient) -> None:
    stations = await fetch_tide_stations(client_http1)
    station_adapter = TypeAdapter(list[TideStation])
    validated = station_adapter.validate_python(stations)
    assert len(validated) > 0
    station_id = validated[0]["stationId"]

    latest = await fetch_latest_realtime(client_http1, station_id)
    latest_adapter = TypeAdapter(TideLatestRealtime)
    validated_latest = latest_adapter.validate_python(latest)
    assert validated_latest["dateTime"]
