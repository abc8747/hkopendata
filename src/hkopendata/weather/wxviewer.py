"""Wxviewer data access helpers.

- SCCW: South China Coastal Waters forecast products.
- Display bounds are roughly latitudes -5..62 and longitudes 80..185.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator, Literal, TypeAlias, cast

import httpx
from typing_extensions import NotRequired, TypedDict

from ..types import (
    AngleDeg,
    HeightM,
    LatitudeDeg,
    LongitudeDeg,
    PeriodS,
    RelativeHumidity,
    SpeedKmh,
    SpeedKt,
    SpeedMs,
    StaticPressureHPa,
    TemperatureC,
)

JsonValue: TypeAlias = Any

GeoJsonCoordinates: TypeAlias = Any

WxDateTimeStr: TypeAlias = Any
"""Datetime string formatted as YYYYMMDDHH (sometimes embedded in longer strings)."""


LatLonStr: TypeAlias = str
"""String of 'lat,lon' coordinates, e.g. '22.5,114.1'"""


StationId: TypeAlias = str
"""Station identifier.

Examples:

- `45005`: Hong Kong (WMO index)
- `54511`: Beijing (WMO index)
- `ZGGG`: Guangzhou (ICAO code)
- `VDPP`: Phnom Penh (ICAO code)
"""

ForecastModel = Literal["ec", "pangu_ec", "fuxi_ec", "fengwu_ec", "aifs", "aamc"]
ProductCode = Literal["TT", "UV", "GST", "RF", "RH", "DV", "VO", "WH", "SH", "WP", "SC"]
SccwLanguageSuffix = Literal["", "_uc", "_sc"]

WXVIEWER_DATE_FORMAT = "%Y%m%d%H"
WXVIEWER_DEFAULT_BASE_URL = "https://maps.weather.gov.hk/wxviewer"


class CurrentBasetimes(TypedDict, total=False):
    default: WxDateTimeStr
    tc_track: WxDateTimeStr
    TT: WxDateTimeStr
    """Temperature"""
    UV: WxDateTimeStr
    """Wind (Wind Speed derived from U and V components)"""
    GST: WxDateTimeStr
    """Wind Gusts"""
    RF: WxDateTimeStr
    """Rainfall"""
    RH: WxDateTimeStr
    """Relative Humidity"""
    DV: WxDateTimeStr
    """Divergence"""
    VO: WxDateTimeStr
    """Vorticity"""
    WH: WxDateTimeStr
    """Wave Height"""
    SH: WxDateTimeStr
    """Swell Height"""
    WP: WxDateTimeStr
    """Wave Period"""
    SC: WxDateTimeStr
    """Sea Current"""


class GeoJsonGeometry(TypedDict):
    type: Literal[
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
    ]
    coordinates: GeoJsonCoordinates


class GeoJsonFeature(TypedDict):
    type: Literal["Feature"]
    geometry: GeoJsonGeometry | None
    properties: dict[str, JsonValue]


class GeoJsonFeatureCollection(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[GeoJsonFeature]


class TopoJson(TypedDict, total=False):
    type: Literal["Topology"]
    objects: dict[str, JsonValue]
    arcs: JsonValue
    transform: JsonValue


class WorldPlaceProperties(TypedDict, total=False):
    stationid: StationId


WorldPlaces: TypeAlias = GeoJsonFeatureCollection


class TCRangeRings(GeoJsonFeatureCollection):
    pass


class TCTrackDetails(TypedDict, total=False):
    id: str
    name: NotRequired[str]
    name_tc: NotRequired[str]
    name_sc: NotRequired[str]
    basin: NotRequired[str]
    year: NotRequired[int]


class TCTrackPoint(TypedDict, total=False):
    dt: WxDateTimeStr
    lat: LatitudeDeg[float]
    lon: LongitudeDeg[float]
    wind: SpeedKmh[float]
    pressure: StaticPressureHPa[float]
    category: str


class TCTrack(TypedDict, total=False):
    details: TCTrackDetails
    track: list[TCTrackPoint]


class TCTracksResponse(TypedDict, total=False):
    tc: list[TCTrack]


class ForecastDetailOCF(TypedDict, total=False):
    dateTimeUtc: WxDateTimeStr
    dateTimeLocal: WxDateTimeStr
    temperature: TemperatureC[float]
    relativeHumidity: RelativeHumidity[float]
    windDirection: AngleDeg[float]
    windSpeed: SpeedMs[float]
    weatherIconWWIS: NotRequired[str]
    """World Weather Information Service (WWIS) weather icon index."""
    weatherIcon: NotRequired[int]
    """Internal weather icon index."""


class ForecastDetailStation(TypedDict, total=False):
    stationOfficialId: StationId
    ocfs: list[ForecastDetailOCF]
    """List of Operational Consensus Forecast System (OCFS) data points."""


class ForecastDetailResponse(TypedDict, total=False):
    result: list[ForecastDetailStation]


class HKOHourlyForecastItem(TypedDict, total=False):
    ForecastHour: WxDateTimeStr
    ForecastRelativeHumidity: RelativeHumidity[float]
    ForecastTemperature: TemperatureC[float]
    ForecastWindDirection: AngleDeg[float]
    ForecastWindSpeed: SpeedMs[float]
    ForecastWeather: int
    """HKO weather icon index."""


class HKOForecastDetailResponse(TypedDict, total=False):
    LastModified: int
    HourlyWeatherForecast: list[HKOHourlyForecastItem]


class SCCWLocationDetail(TypedDict, total=False):
    location_id: str
    location_name: str
    wind: str
    wx_desc: str
    sea: str


class SCCWDetailResponse(TypedDict, total=False):
    warning_area: str
    general_situation: str
    fourty_eight_hours_outlook: str
    weather_report: str
    bulletin_datetime: str
    location_detail: list[SCCWLocationDetail]


class SeaStateGridDataPoint(TypedDict, total=False):
    dtutc: WxDateTimeStr
    dt: WxDateTimeStr
    wskmh: SpeedKmh[float]
    """Wind speed"""
    wskt: SpeedKt[float]
    """Wind speed"""
    wnd: AngleDeg[float]
    """Wind direction"""
    wh: HeightM[float]
    """Wave height"""
    wp: PeriodS[float]
    """Wave period"""
    wd: AngleDeg[float]
    """Wave direction"""
    sh: HeightM[float]
    """Swell height"""
    sp: PeriodS[float]
    """Swell period"""
    sd: AngleDeg[float]
    """Swell direction"""
    cskmh: NotRequired[SpeedKmh[float]]
    """Current speed"""
    cskt: NotRequired[SpeedKt[float]]
    """Current speed"""
    csms: NotRequired[SpeedMs[float]]
    """Current speed"""
    cnd: NotRequired[AngleDeg[float]]
    """Current direction"""


class SeaCurrentGridDataPoint(TypedDict, total=False):
    dtutc: WxDateTimeStr
    cskmh: SpeedKmh[float]
    cskt: SpeedKt[float]
    csms: SpeedMs[float]
    cnd: AngleDeg[float]


class SeaStateGridForecast(TypedDict, total=False):
    pt: LatLonStr
    """Coordinate point as a 'lat,lon' string."""
    data: list[SeaStateGridDataPoint]


class SeaCurrentGridForecast(TypedDict, total=False):
    pt: LatLonStr
    """Coordinate point as a 'lat,lon' string."""
    data: list[SeaCurrentGridDataPoint]


class SeaStateForecastDetailResponse(TypedDict, total=False):
    result: list[SeaStateGridForecast]


class SeaCurrentForecastDetailResponse(TypedDict, total=False):
    result: list[SeaCurrentGridForecast]


WxviewerAssetPath: TypeAlias = str


async def fetch_current_basetimes(
    client: httpx.AsyncClient,
    forecast_model: ForecastModel | None,
    base_url: str = WXVIEWER_DEFAULT_BASE_URL,
) -> CurrentBasetimes:
    base = base_url.rstrip("/")
    if forecast_model is None:
        candidates = [
            f"{base}/data/current.json",
            f"{base}/data/current_null.json",
        ]
    else:
        candidates = [f"{base}/data/current_{forecast_model}.json"]

    last_response: httpx.Response | None = None
    for url in candidates:
        response = await client.get(url)
        last_response = response
        if response.status_code == httpx.codes.NOT_FOUND:
            continue
        response.raise_for_status()
        return cast(CurrentBasetimes, response.json())

    if last_response is not None:
        last_response.raise_for_status()
    return cast(CurrentBasetimes, {})


async def fetch_world_places(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> WorldPlaces:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/world-places.json")
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "features" in data:
        return cast(WorldPlaces, data)
    if isinstance(data, list):
        return cast(WorldPlaces, {"type": "FeatureCollection", "features": data})
    return cast(WorldPlaces, {"type": "FeatureCollection", "features": []})


async def fetch_coastline(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> TopoJson:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/earth-topo.json")
    response.raise_for_status()
    return cast(TopoJson, response.json())


async def fetch_islands(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> TopoJson:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/i-topo.json")
    response.raise_for_status()
    return cast(TopoJson, response.json())


async def fetch_hko_coastline(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> TopoJson:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/hko-topo.json")
    response.raise_for_status()
    return cast(TopoJson, response.json())


async def fetch_tc_range_rings(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> TCRangeRings:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/range-ring.json")
    response.raise_for_status()
    return cast(TCRangeRings, response.json())


async def fetch_tc_tracks(
    client: httpx.AsyncClient,
    basetime: WxDateTimeStr,
    base_url: str = WXVIEWER_DEFAULT_BASE_URL,
) -> TCTracksResponse:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/tc/{basetime}.json")
    response.raise_for_status()
    return cast(TCTracksResponse, response.json())


async def fetch_forecast_detail(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> ForecastDetailResponse:
    base = base_url.rstrip("/")
    current_resp = await client.get(f"{base}/data/city_forecast/current.txt")
    current_resp.raise_for_status()
    current_id = current_resp.text.strip()
    data_resp = await client.get(f"{base}/data/city_forecast/{current_id}.json")
    data_resp.raise_for_status()
    return cast(ForecastDetailResponse, data_resp.json())


async def fetch_hk_forecast_detail(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> HKOForecastDetailResponse:
    base = base_url.rstrip("/")
    current_resp = await client.get(f"{base}/data/city_forecast/current_hko.txt")
    current_resp.raise_for_status()
    current_id = current_resp.text.strip()
    data_resp = await client.get(f"{base}/data/city_forecast/{current_id}_hko.json")
    data_resp.raise_for_status()
    return cast(HKOForecastDetailResponse, data_resp.json())


async def fetch_mslp_raw(
    client: httpx.AsyncClient,
    folder: str,
    filename: str,
    base_url: str = WXVIEWER_DEFAULT_BASE_URL,
) -> str:
    """Fetch mean sea-level pressure KML as raw text."""
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/weather/{folder}/{filename}.kml")
    response.raise_for_status()
    return response.text


async def fetch_sccw_boundaries_raw(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> str:
    """Fetch SCCW boundary KML as raw text."""
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/sccw.kml")
    response.raise_for_status()
    return response.text


async def fetch_sccw_area(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> GeoJsonFeatureCollection:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/sccw-area.json")
    response.raise_for_status()
    return cast(GeoJsonFeatureCollection, response.json())


async def fetch_sccw_placemarks(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> GeoJsonFeatureCollection:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/sccw-placemarks.json")
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "features" in data:
        return cast(GeoJsonFeatureCollection, data)
    if isinstance(data, list):
        return cast(
            GeoJsonFeatureCollection,
            {"type": "FeatureCollection", "features": data},
        )
    return cast(GeoJsonFeatureCollection, {"type": "FeatureCollection", "features": []})


async def fetch_sccw_detail(
    client: httpx.AsyncClient,
    lang_suffix: SccwLanguageSuffix,
    base_url: str = WXVIEWER_DEFAULT_BASE_URL,
) -> SCCWDetailResponse:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/sccw/sccw_json{lang_suffix}.json")
    response.raise_for_status()
    return cast(SCCWDetailResponse, response.json())


async def fetch_sea_state_lines(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> GeoJsonFeatureCollection:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/sea-state-lines.json")
    response.raise_for_status()
    return cast(GeoJsonFeatureCollection, response.json())


async def fetch_sea_state_grids(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> GeoJsonFeatureCollection:
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/config/sea-state-grids.json")
    response.raise_for_status()
    return cast(GeoJsonFeatureCollection, response.json())


async def fetch_sea_state_forecast_detail(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> SeaStateForecastDetailResponse:
    base = base_url.rstrip("/")
    current_resp = await client.get(f"{base}/data/sccw/current_ss.txt")
    current_resp.raise_for_status()
    current_id = current_resp.text.strip()
    data_resp = await client.get(f"{base}/data/sccw/SS_{current_id}.json")
    data_resp.raise_for_status()
    return cast(SeaStateForecastDetailResponse, data_resp.json())


async def fetch_sea_current_forecast_detail(
    client: httpx.AsyncClient, base_url: str = WXVIEWER_DEFAULT_BASE_URL
) -> SeaCurrentForecastDetailResponse:
    base = base_url.rstrip("/")
    current_resp = await client.get(f"{base}/data/sccw/current_ss.txt")
    current_resp.raise_for_status()
    current_id = current_resp.text.strip()
    data_resp = await client.get(f"{base}/data/sccw/SScurr_{current_id}.json")
    data_resp.raise_for_status()
    return cast(SeaCurrentForecastDetailResponse, data_resp.json())


async def fetch_wxviewer_asset_bytes(
    client: httpx.AsyncClient,
    asset_path: WxviewerAssetPath,
    base_url: str = WXVIEWER_DEFAULT_BASE_URL,
) -> bytes:
    """Fetch raw bytes for any wxviewer asset path.

    :param asset_path: Path relative to the wxviewer root.

    Examples:

    - `data/config/world-places.json`
    - `data/weather/ec/2024010100/TT_000.png`
    """
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/{asset_path.lstrip('/')}")
    response.raise_for_status()
    return response.content


async def fetch_weather_asset_bytes(
    client: httpx.AsyncClient,
    asset_path: WxviewerAssetPath,
    base_url: str = WXVIEWER_DEFAULT_BASE_URL,
) -> bytes:
    """Fetch raw bytes under `data/weather` (tiles/images/KML/PNG).

    :param asset_path: Path relative to `data/weather`.

    Examples:

    - `ec/2024010100/TT_000.png`
    - `ec/2024010100/MSLP_000.kml`
    """
    base = base_url.rstrip("/")
    response = await client.get(f"{base}/data/weather/{asset_path.lstrip('/')}")
    response.raise_for_status()
    return response.content


#
# misc helpers, unstable!
#


@dataclass(frozen=True)
class ForecastDetailWindow:
    start: datetime | None
    end: datetime | None


@dataclass(frozen=True)
class ForecastDetailSelection:
    stations: dict[StationId, ForecastDetailStation]
    window: ForecastDetailWindow


@dataclass(frozen=True)
class SeaStateDetailSelection:
    grids: dict[LatLonStr, SeaStateGridForecast]
    """Dictionary mapping 'lat,lon' grid points to their forecast data."""
    window: ForecastDetailWindow


def _parse_wx_datetime(value: str) -> datetime | None:
    trimmed = value.strip()
    if len(trimmed) >= 10:
        trimmed = trimmed[:10]
    try:
        return datetime.strptime(trimmed, WXVIEWER_DATE_FORMAT).replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def _iter_world_place_station_ids(places: WorldPlaces) -> Iterator[str]:
    for feature in places.get("features", []):
        station_id = feature.get("properties", {}).get("stationid")
        if isinstance(station_id, str) and station_id:
            yield station_id


def extract_world_place_station_ids(places: WorldPlaces) -> Iterator[str]:
    return _iter_world_place_station_ids(places)


def filter_forecast_detail_by_places(
    forecast: ForecastDetailResponse,
    station_ids: Iterable[str],
) -> ForecastDetailSelection:
    station_lookup = set(station_ids)
    stations: dict[str, ForecastDetailStation] = {}
    start_time: datetime | None = None
    end_time: datetime | None = None

    for station in forecast.get("result", []):
        station_id = station.get("stationOfficialId")
        if not station_id or station_id not in station_lookup:
            continue
        stations[station_id] = station

        ocfs = station.get("ocfs", [])
        if ocfs:
            first_dt = ocfs[0].get("dateTimeUtc")
            last_dt = ocfs[-1].get("dateTimeUtc")
            if first_dt:
                parsed = _parse_wx_datetime(str(first_dt))
                if parsed and (start_time is None or parsed < start_time):
                    start_time = parsed
            if last_dt:
                parsed = _parse_wx_datetime(str(last_dt))
                if parsed and (end_time is None or parsed > end_time):
                    end_time = parsed

    window = ForecastDetailWindow(start=start_time, end=end_time)
    return ForecastDetailSelection(stations=stations, window=window)


def _extract_geojson_grid_names(grids: GeoJsonFeatureCollection) -> set[str]:
    names: set[str] = set()
    for feature in grids.get("features", []):
        properties = feature.get("properties", {})
        name = properties.get("name")
        if isinstance(name, str):
            names.add(name)
    return names


def filter_sea_state_forecast_detail(
    forecast: SeaStateForecastDetailResponse,
    sea_state_grids: GeoJsonFeatureCollection,
) -> SeaStateDetailSelection:
    grid_names = _extract_geojson_grid_names(sea_state_grids)
    grids: dict[str, SeaStateGridForecast] = {}
    start_time: datetime | None = None
    end_time: datetime | None = None

    for grid in forecast.get("result", []):
        grid_id = grid.get("pt")
        if not grid_id or grid_id not in grid_names:
            continue
        grids[grid_id] = grid
        data = grid.get("data", [])
        if data:
            first_dt = data[0].get("dtutc")
            last_dt = data[-1].get("dtutc")
            if first_dt:
                parsed = _parse_wx_datetime(str(first_dt))
                if parsed and (start_time is None or parsed < start_time):
                    start_time = parsed
            if last_dt:
                parsed = _parse_wx_datetime(str(last_dt))
                if parsed and (end_time is None or parsed > end_time):
                    end_time = parsed

    window = ForecastDetailWindow(start=start_time, end=end_time)
    return SeaStateDetailSelection(grids=grids, window=window)


def filter_sea_current_forecast_detail(
    forecast: SeaCurrentForecastDetailResponse,
    sea_state_grids: GeoJsonFeatureCollection,
) -> dict[str, SeaCurrentGridForecast]:
    grid_names = _extract_geojson_grid_names(sea_state_grids)
    grids: dict[str, SeaCurrentGridForecast] = {}

    for grid in forecast.get("result", []):
        grid_id = grid.get("pt")
        if not grid_id or grid_id not in grid_names:
            continue
        grids[grid_id] = grid

    return grids


def merge_sea_state_and_current(
    sea_state: SeaStateGridForecast,
    sea_current: SeaCurrentGridForecast | None,
) -> Iterator[SeaStateGridDataPoint]:
    state_data = list(sea_state.get("data", []))
    if not sea_current:
        return iter(state_data)

    current_lookup = {
        point.get("dtutc"): point
        for point in sea_current.get("data", [])
        if point.get("dtutc")
    }

    def _iter_merged() -> Iterator[SeaStateGridDataPoint]:
        for point in state_data:
            dtutc = point.get("dtutc")
            if dtutc and dtutc in current_lookup:
                current_point = current_lookup[dtutc]
                yield {
                    **point,
                    "cskmh": current_point.get("cskmh", -1.0),
                    "cskt": current_point.get("cskt", -1.0),
                    "csms": current_point.get("csms", -1.0),
                    "cnd": current_point.get("cnd", -1.0),
                }
            else:
                yield point

    return _iter_merged()
