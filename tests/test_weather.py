import httpx
import pytest
from pydantic import TypeAdapter

from hkopendata.weather.ocf import OCF, fetch_ocf


@pytest.mark.anyio
async def test_weather_ocf(client: httpx.AsyncClient) -> None:
    station_id = "HKO"
    ocf_data = await fetch_ocf(client, station_id)
    assert ocf_data is not None
    assert ocf_data["StationCode"] == station_id

    adapter = TypeAdapter(OCF)
    validated_data = adapter.validate_python(ocf_data)
    assert validated_data["StationCode"] == station_id
