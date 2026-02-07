from datetime import datetime, timedelta, timezone

import httpx
import pytest
from pydantic import TypeAdapter

from hkopendata.weather import opendata
from hkopendata.weather.ocf import OCF, fetch_ocf
from hkopendata.weather.opendata import fetch_hko_opendata


@pytest.mark.anyio
async def test_weather_ocf(client: httpx.AsyncClient) -> None:
    station_id = "HKO"
    ocf_data = await fetch_ocf(client, station_id)
    assert ocf_data is not None
    assert ocf_data["StationCode"] == station_id

    validated_data = TypeAdapter(OCF).validate_python(ocf_data)
    assert validated_data["StationCode"] == station_id


@pytest.mark.anyio
async def test_weather_flw(client: httpx.AsyncClient) -> None:
    forecast = await fetch_hko_opendata(client, opendata.LocalForecastRequest())
    TypeAdapter(opendata.LocalForecastResponse).validate_python(forecast)


@pytest.mark.anyio
async def test_weather_fnd(client: httpx.AsyncClient) -> None:
    forecast = await fetch_hko_opendata(client, opendata.ForecastRequest())
    TypeAdapter(opendata.ForecastResponse).validate_python(forecast)


@pytest.mark.anyio
async def test_weather_rhrread(client: httpx.AsyncClient) -> None:
    rhrread = await fetch_hko_opendata(client, opendata.CurrentWeatherReportRequest())
    TypeAdapter(opendata.RhrreadResponse).validate_python(rhrread)


@pytest.mark.anyio
async def test_weather_warning_info(client: httpx.AsyncClient) -> None:
    warnings = await fetch_hko_opendata(client, opendata.WarningInfoRequest())
    TypeAdapter(opendata.WarningInfoResponse).validate_python(warnings)


@pytest.mark.anyio
async def test_weather_warnsum(client: httpx.AsyncClient) -> None:
    warnsum = await fetch_hko_opendata(client, opendata.WarningSummaryRequest())
    TypeAdapter(opendata.WarningSummaryResponse).validate_python(warnsum)


@pytest.mark.anyio
async def test_weather_swt(client: httpx.AsyncClient) -> None:
    swt = await fetch_hko_opendata(client, opendata.SpecialWeatherTipsRequest())
    TypeAdapter(opendata.SpecialWeatherTipsResponse).validate_python(swt)


@pytest.mark.anyio
async def test_weather_sun_moon(client: httpx.AsyncClient) -> None:
    srs = await fetch_hko_opendata(
        client, opendata.SunriseSunsetRequest(year=2024, month=1)
    )
    validated = TypeAdapter(opendata.CsvDataResponse).validate_python(srs)
    assert len(validated["data"]) > 0
    assert isinstance(validated["data"][0], list)


@pytest.mark.anyio
async def test_weather_moonrise(client: httpx.AsyncClient) -> None:
    mrs = await fetch_hko_opendata(
        client, opendata.MoonriseMoonsetRequest(year=2024, month=1)
    )
    validated = TypeAdapter(opendata.CsvDataResponse).validate_python(mrs)
    assert len(validated["data"]) > 0
    assert isinstance(validated["data"][0], list)


@pytest.mark.anyio
async def test_earthquake_qem(client: httpx.AsyncClient) -> None:
    qem = await fetch_hko_opendata(client, opendata.QuickEarthquakeMessagesRequest())
    TypeAdapter(opendata.EarthquakeItem).validate_python(qem)


@pytest.mark.anyio
async def test_feltearthquake(client: httpx.AsyncClient) -> None:
    feltearthquake = await fetch_hko_opendata(
        client, opendata.LocallyFeltEarthTremorRequest()
    )
    TypeAdapter(opendata.FeltEarthquakeItem).validate_python(feltearthquake)


@pytest.mark.anyio
async def test_hourly_rainfall(client: httpx.AsyncClient) -> None:
    rainfall = await fetch_hko_opendata(client, opendata.HourlyRainfallRequest())
    validated = TypeAdapter(opendata.HourlyRainfallResponse).validate_python(rainfall)
    assert "hourlyRainfall" in validated


@pytest.mark.anyio
async def test_lunar_date(client: httpx.AsyncClient) -> None:
    lunar = await fetch_hko_opendata(
        client, opendata.LunarDateRequest(date="2023-01-01")
    )
    validated = TypeAdapter(opendata.LunarDateResponse).validate_python(lunar)
    assert "LunarYear" in validated


@pytest.mark.anyio
async def test_tides(client: httpx.AsyncClient) -> None:
    hhot = await fetch_hko_opendata(
        client, opendata.TidesHourlyRequest(year=2024, station="CLK")
    )
    validated_hhot = TypeAdapter(opendata.CsvDataResponse).validate_python(hhot)
    assert len(validated_hhot["data"]) > 0

    hlt = await fetch_hko_opendata(
        client, opendata.TidesHighLowRequest(year=2024, station="CLK")
    )
    validated_hlt = TypeAdapter(opendata.CsvDataResponse).validate_python(hlt)
    assert len(validated_hlt["data"]) > 0


@pytest.mark.anyio
async def test_lightning_and_visibility(client: httpx.AsyncClient) -> None:
    lhl = await fetch_hko_opendata(client, opendata.LightningRequest())
    TypeAdapter(opendata.CsvDataResponse).validate_python(lhl)

    ltmv = await fetch_hko_opendata(client, opendata.VisibilityRequest())
    TypeAdapter(opendata.CsvDataResponse).validate_python(ltmv)


@pytest.mark.anyio
async def test_clm_temp(client: httpx.AsyncClient) -> None:
    temp = await fetch_hko_opendata(
        client, opendata.DailyMeanTempRequest(station="HKO", year=2023)
    )
    validated = TypeAdapter(opendata.ClimatologicalDataResponse).validate_python(temp)
    assert len(validated["data"]) > 0

    maxt = await fetch_hko_opendata(
        client, opendata.DailyMaxTempRequest(station="HKO", year=2023)
    )
    validated_max = TypeAdapter(opendata.ClimatologicalDataResponse).validate_python(
        maxt
    )
    assert len(validated_max["data"]) > 0


@pytest.mark.anyio
async def test_ryes(client: httpx.AsyncClient) -> None:
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime(
        "%Y%m%d"
    )
    await fetch_hko_opendata(
        client, opendata.WeatherRadiationRequest(station="HKO", date=yesterday)
    )
