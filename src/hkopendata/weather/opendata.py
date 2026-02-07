"""Hong Kong Observatory Open Data

- Version: 1.13 (Sep 2025)
- Source: <https://data.weather.gov.hk/weatherAPI/doc/HKO_Open_Data_API_Documentation.pdf>
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol, TypeAlias, overload

import httpx
from typing_extensions import NotRequired, TypedDict

from ..types import Day, Hour, LatitudeDeg, LongitudeDeg, Month, Year

WEATHER_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
OPENDATA_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
EARTHQUAKE_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/earthquake.php"
HOURLY_RAINFALL_API_URL = (
    "https://data.weather.gov.hk/weatherAPI/opendata/hourlyRainfall.php"
)
LUNAR_DATE_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/lunardate.php"

Lang = Literal["en", "tc", "sc"]
DateStr: TypeAlias = str
"""Date in YYYYMMDD format"""
IsoDateStr: TypeAlias = str
"""Date in YYYY-MM-DD format"""
DateTimeStr: TypeAlias = str
"""Date and time in ISO8601 format, e.g. 2024-09-10T14:00:00+08:00"""

# TODO: convert these types into StrEnums (but we have to support introspection + static
# type checking)
TideStationCode = Literal[
    "CCH",  # Cheung Chau
    "CLK",  # Chek Lap Kok
    "CMW",  # Chi Ma Wan
    "KCT",  # Kwai Chung
    "KLW",  # Ko Lau Wan
    "LOP",  # Lok On Pai
    "MWC",  # Ma Wan
    "QUB",  # Quarry Bay
    "SPW",  # Shek Pik
    "TAO",  # Tai O
    "TBT",  # Tsim Bei Tsui
    "TMW",  # Tai Miu Wan
    "TPK",  # Tai Po Kau
    "WAG",  # Waglan Island
]
ClimatologicalStationCode = Literal[
    "CCH",  # Cheung Chau
    "CWB",  # Clear Water Bay
    "HKA",  # Hong Kong International Airport
    "HKO",  # Hong Kong Observatory
    "HKP",  # Hong Kong Park
    "HKS",  # Wong Chuk Hang
    "HPV",  # Happy Valley
    "JKB",  # Tseung Kwan O
    "KLT",  # Kowloon City
    "KP",  # King's Park
    "KSC",  # Kau Sai Chau
    "KTG",  # Kwun Tong
    "LFS",  # Lau Fau Shan
    "NGP",  # Ngong Ping
    "PEN",  # Peng Chau
    "PLC",  # Tai Mei Tuk
    "SE1",  # Kai Tak Runway Park
    "SEK",  # Shek Kong
    "SHA",  # Sha Tin
    "SKG",  # Sai Kung
    "SKW",  # Shau Kei Wan
    "SSH",  # Sheung Shui
    "SSP",  # Sham Shui Po
    "STY",  # Stanley
    "TC",  # Tate's Cairn
    "TKL",  # Ta Kwu Ling
    "TMS",  # Tai Mo Shan
    "TPO",  # Tai Po (Conservation Studies Centre)
    "TU1",  # Tuen Mun Children and Juvenile Home
    "TW",  # Tsuen Wan Shing Mun Valley
    "TWN",  # Tsuen Wan
    "TY1",  # New Tsing Yi Station
    "TYW",  # Pak Tam Chung (Tsak Yue Wu)
    "VP1",  # The Peak
    "WGL",  # Waglan Island
    "WLP",  # Wetland Park
    "WTS",  # Wong Tai Sin
    "YCT",  # Tai Po (Yuan Chau Tsai Park)
    "YLP",  # Yuen Long Park
]
WeatherRadiationStationCode = Literal[
    "CLK",  # Chek Lap Kok
    "CCH",  # Cheung Chau
    "HKO",  # Hong Kong Observatory
    "HPV",  # Happy Valley
    "HKP",  # Hong Kong Park
    "SE1",  # Kai Tak Runway Park
    "KAT",  # Kat O
    "KP",  # Kings Park
    "KLT",  # Kowloon City
    "KTG",  # Kwun Tong
    "LFS",  # Lau Fau Shan
    "EPC",  # Ping Chau
    "SKG",  # Sai Kung
    "SWH",  # Sai Wan Ho
    "STK",  # Sha Tau Kok
    "SHA",  # Sha Tin
    "SSP",  # Sham Shui Po
]

Psr = Literal["High", "Medium High", "Medium", "Medium Low", "Low"]
"""Probability of Significant Rain"""

WarningActionCode = Literal["ISSUE", "REISSUE", "CANCEL", "EXTEND", "UPDATE"]
WarningStatementCode = Literal[
    "WFIRE",  # Fire Danger Warning
    "WFROST",  # Frost Warning
    "WHOT",  # Hot Weather Warning
    "WCOLD",  # Cold Weather Warning
    "WMSGNL",  # Strong Monsoon Signal
    "WRAIN",  # Rainstorm Warning Signal
    "WFNTSA",  # Special Announcement on Flooding in the northern New Territories
    "WL",  # Landslip Warning
    "WTCSGNL",  # Tropical Cyclone Warning Signal
    "WTMW",  # Tsunami Warning
    "WTS",  # Thunderstorm Warning
    "WTCPRE8",  # Pre-no.8 Special Announcement
]
WarningSubtype = Literal[
    "WFIREY",  # Yellow Fire
    "WFIRER",  # Red Fire
    "WRAINA",  # Amber
    "WRAINR",  # Red
    "WRAINB",  # Black
    "TC1",  # No. 1
    "TC3",  # No. 3
    "TC8NE",  # No. 8 North East
    "TC8SE",  # No. 8 South East
    "TC8NW",  # No. 8 North West
    "TC8SW",  # No. 8 South West
    "TC9",  # No. 9
    "TC10",  # No. 10
    "CANCEL",  # Cancel All Signals
]


class HasApiUrl(Protocol):
    api_url: str


class UnitValue(TypedDict):
    value: int | float
    unit: str


class DepthValue(TypedDict):
    value: int | float
    unit: str


class SeaTempItem(UnitValue):
    place: str
    recordTime: DateTimeStr


class SoilTempItem(UnitValue):
    place: str
    recordTime: DateTimeStr
    depth: DepthValue


class ForecastItem(TypedDict):
    """9-day weather forecast item."""

    forecastDate: DateStr
    forecastWeather: str
    forecastMaxtemp: UnitValue
    forecastMintemp: UnitValue
    week: str
    """Day of the week (e.g. 'Monday')."""
    forecastWind: str
    forecastMaxrh: UnitValue
    forecastMinrh: UnitValue
    ForecastIcon: int
    """Icon ID. See <https://www.hko.gov.hk/textonly/v2/explain/wxicon_e.htm>"""
    PSR: Psr


class ForecastResponse(TypedDict, total=False):
    generalSituation: str
    weatherForecast: list[ForecastItem]
    """List of forecast data for the next 9 days."""
    updateTime: DateTimeStr
    seaTemp: SeaTempItem | list[SeaTempItem]
    soilTemp: list[SoilTempItem]


class LocalForecastResponse(TypedDict, total=False):
    generalSituation: str
    tcInfo: str
    """Tropical Cyclone Information."""
    fireDangerWarning: str
    forecastPeriod: str
    forecastDesc: str
    outlook: str
    updateTime: DateTimeStr


class TemperatureData(UnitValue):
    place: str


class TemperatureResponse(TypedDict):
    """Temperature data from Current Weather Report."""

    data: list[TemperatureData]
    recordTime: DateTimeStr


class HumidityData(UnitValue):
    place: str


class HumidityResponse(TypedDict):
    data: list[HumidityData]
    recordTime: DateTimeStr


class RainfallData(TypedDict):
    unit: str
    place: str
    max: NotRequired[int | float]
    min: NotRequired[int | float]
    main: Literal["TRUE", "FALSE"]
    """Maintenance flag."""


class RainfallResponse(TypedDict):
    data: list[RainfallData]
    startTime: DateTimeStr
    endTime: DateTimeStr


class LightningData(TypedDict):
    place: str
    occur: Literal["true"]
    """Whether lightning occurred (always 'true' if present)."""


class LightningResponse(TypedDict):
    data: list[LightningData]
    startTime: DateTimeStr
    endTime: DateTimeStr


class UVIndexData(TypedDict, total=False):
    place: str
    value: int | float
    """UV Index value."""
    desc: str
    """Exposure level description (e.g. 'Low', 'Moderate')."""
    message: str


class UVIndexResponse(TypedDict):
    data: list[UVIndexData]
    recordDesc: str
    recordTime: NotRequired[DateTimeStr]


class RhrreadResponse(TypedDict, total=False):
    icon: list[int]
    """List of weather icon IDs."""
    iconUpdateTime: DateTimeStr
    uvindex: UVIndexResponse | Literal[""]
    updateTime: DateTimeStr
    warningMessage: list[str] | Literal[""]
    rainstormReminder: str | Literal[""]
    specialWxTips: list[str] | Literal[""]
    """List of special weather tips, or empty string."""
    tcmessage: list[str] | Literal[""]
    mintempFrom00To09: UnitValue | Literal[""]
    """Minimum temperature from midnight to 9am."""
    rainfallFrom00To12: UnitValue | Literal[""]
    """Accumulated rainfall from midnight to noon."""
    rainfallLastMonth: UnitValue | Literal[""]
    rainfallJanuaryToLastMonth: UnitValue | Literal[""]
    temperature: TemperatureResponse
    humidity: HumidityResponse
    lightning: LightningResponse
    rainfall: RainfallResponse


class WarningInfoDetails(TypedDict, total=False):
    contents: list[str]
    """List of text lines describing the warning content."""
    warningStatementCode: WarningStatementCode
    updateTime: DateTimeStr
    subtype: WarningSubtype


class WarningInfoResponse(TypedDict, total=False):
    details: list[WarningInfoDetails]


class WarningSummaryItem(TypedDict, total=False):
    name: str
    """Name of the warning (e.g. 'Strong Monsoon Signal')."""
    code: WarningStatementCode | WarningSubtype  # is this correct?
    type: str
    """Type/Category description (e.g. 'Red', 'Strong Wind Signal No. 3')."""
    actionCode: WarningActionCode
    issueTime: DateTimeStr
    expireTime: DateTimeStr
    updateTime: DateTimeStr


WarningSummaryResponse: TypeAlias = dict[WarningStatementCode, WarningSummaryItem]


class SpecialWeatherTipsItem(TypedDict):
    desc: str
    """Content of the tip."""
    updateTime: DateTimeStr


class SpecialWeatherTipsResponse(TypedDict):
    swt: list[SpecialWeatherTipsItem]


class EarthquakeItem(TypedDict):
    lat: LatitudeDeg[float]
    lon: LongitudeDeg[float]
    mag: float
    """Richter magnitude scale."""
    region: str
    ptime: DateTimeStr
    updateTime: DateTimeStr


class FeltEarthquakeItem(TypedDict, total=False):
    updateTime: DateTimeStr
    mag: float
    """Richter magnitude scale."""
    region: str
    intensity: str
    lat: LatitudeDeg[float]
    lon: LongitudeDeg[float]
    details: str
    ptime: DateTimeStr


class HourlyRainfallData(TypedDict):
    automaticWeatherStation: str
    automaticWeatherStationID: str
    value: str | Literal["M"]
    """Rainfall amount in the past hour."""
    unit: str
    """Unit of measurement (usually 'mm')."""


class HourlyRainfallResponse(TypedDict):
    obsTime: DateTimeStr
    hourlyRainfall: list[HourlyRainfallData]


class LunarDateResponse(TypedDict):
    LunarYear: str
    """Gan-Zhi and Zodiac in traditional Chinese only, e.g. '癸卯年，兔'."""  # noqa: RUF001
    LunarDate: str
    """In traditional Chinese only, e.g. '二月初十'."""


class CsvDataResponse(TypedDict):
    """Response format for CSV-based datasets (Tides, Solar, Lunar, Lightning,
    Visibility)."""

    fields: list[str]
    """List of column headers."""
    data: list[list[str]]
    """List of rows, where each row is a list of string values corresponding to
    `fields`."""


class ClimatologicalDataResponse(TypedDict):
    type: list[str]
    """Description of the data type."""
    fields: list[str]
    """Column headers."""
    data: list[list[str]]
    """Data rows."""
    legend: list[str]
    """Legend or notes."""


WeatherRadiationResponse: TypeAlias = dict[str, Any]
"""Response for Weather and Radiation Level Report (`RYES`).

A dynamic dictionary where keys are constructed as `{Station}{Attribute}`.

Stations: [`hkopendata.weather.opendata.ClimatologicalStationCode`][]

Attributes:
- `MaxTemp`, `MinTemp`: Max/Min air temperature (Celsius)
- `ReadingsMaxTemp`, `ReadingsMinTemp`: Max/Min air temp readings
- `ReadingsMaxRH`, `ReadingsMinRH`: Max/Min relative humidity (%)
- `ReadingsAvgRainfall`: Average rainfall (mm)
- `ReadingsAccumRainfall`: Total rainfall since 1st Jan (mm)
- `ReadingsRainfall`: Rainfall (mm)
- `Microsieverts`: Average ambient gamma radiation dose rate (microsievert/hour)
- `ReadingsMaxUVIndex`, `ReadingsMeanUVIndex`: Max/Mean UV index
- `ReadingsMinGrassTemp`: Grass minimum temperature (Celsius)
- `ReadingsSunShine`: Duration of sunshine (Hours)

Metadata Keys:
- `BulletinDate`, `BulletinTime`: Report date/time
- `HongKongDesc`: Radiation description
- `NoteDesc`, `NoteDesc1`, `NoteDesc2`, `NoteDesc3`: Notes
- `ReportTimeInfoDate`: Info date
"""


@dataclass
class LocalForecastRequest(HasApiUrl):
    api_url: str = WEATHER_API_URL
    dataType: Literal["flw"] = field(default="flw", init=False)
    lang: Lang = "en"


@dataclass
class ForecastRequest(HasApiUrl):
    api_url: str = WEATHER_API_URL
    dataType: Literal["fnd"] = field(default="fnd", init=False)
    lang: Lang = "en"


@dataclass
class CurrentWeatherReportRequest(HasApiUrl):
    api_url: str = WEATHER_API_URL
    dataType: Literal["rhrread"] = field(default="rhrread", init=False)
    lang: Lang = "en"


@dataclass
class WarningInfoRequest(HasApiUrl):
    api_url: str = WEATHER_API_URL
    dataType: Literal["warningInfo"] = field(default="warningInfo", init=False)
    lang: Lang = "en"


@dataclass
class WarningSummaryRequest(HasApiUrl):
    api_url: str = WEATHER_API_URL
    dataType: Literal["warnsum"] = field(default="warnsum", init=False)
    lang: Lang = "en"


@dataclass
class SpecialWeatherTipsRequest(HasApiUrl):
    api_url: str = WEATHER_API_URL
    dataType: Literal["swt"] = field(default="swt", init=False)
    lang: Lang = "en"


@dataclass
class QuickEarthquakeMessagesRequest(HasApiUrl):
    api_url: str = EARTHQUAKE_API_URL
    dataType: Literal["qem"] = field(default="qem", init=False)
    lang: Lang = "en"


@dataclass
class LocallyFeltEarthTremorRequest(HasApiUrl):
    api_url: str = EARTHQUAKE_API_URL
    dataType: Literal["feltearthquake"] = field(default="feltearthquake", init=False)
    lang: Lang = "en"


@dataclass
class HourlyRainfallRequest(HasApiUrl):
    api_url: str = HOURLY_RAINFALL_API_URL
    lang: Lang = "en"


@dataclass
class LunarDateRequest(HasApiUrl):
    date: IsoDateStr
    api_url: str = LUNAR_DATE_API_URL


@dataclass
class SunriseSunsetRequest(HasApiUrl):
    year: Year
    month: Month
    api_url: str = OPENDATA_API_URL
    dataType: Literal["SRS"] = field(default="SRS", init=False)
    rformat: Literal["json"] = field(default="json", init=False)


@dataclass
class MoonriseMoonsetRequest(HasApiUrl):
    year: Year
    month: Month
    api_url: str = OPENDATA_API_URL
    dataType: Literal["MRS"] = field(default="MRS", init=False)
    rformat: Literal["json"] = field(default="json", init=False)


@dataclass
class TidesHourlyRequest(HasApiUrl):
    year: Year
    station: TideStationCode
    month: Month | None = None
    day: Day | None = None
    hour: Hour | None = None
    api_url: str = OPENDATA_API_URL
    dataType: Literal["HHOT"] = field(default="HHOT", init=False)
    rformat: Literal["json"] = field(default="json", init=False)


@dataclass
class TidesHighLowRequest(HasApiUrl):
    year: Year
    station: TideStationCode
    month: Month | None = None
    api_url: str = OPENDATA_API_URL
    dataType: Literal["HLT"] = field(default="HLT", init=False)
    rformat: Literal["json"] = field(default="json", init=False)


@dataclass
class LightningRequest(HasApiUrl):
    api_url: str = OPENDATA_API_URL
    dataType: Literal["LHL"] = field(default="LHL", init=False)
    rformat: Literal["json"] = field(default="json", init=False)
    lang: Lang = "en"


@dataclass
class VisibilityRequest(HasApiUrl):
    api_url: str = OPENDATA_API_URL
    dataType: Literal["LTMV"] = field(default="LTMV", init=False)
    rformat: Literal["json"] = field(default="json", init=False)
    lang: Lang = "en"


@dataclass
class DailyMeanTempRequest(HasApiUrl):
    station: ClimatologicalStationCode
    year: Year | None = None
    month: Month | None = None
    api_url: str = OPENDATA_API_URL
    dataType: Literal["CLMTEMP"] = field(default="CLMTEMP", init=False)
    rformat: Literal["json"] = field(default="json", init=False)


@dataclass
class DailyMaxTempRequest(HasApiUrl):
    station: ClimatologicalStationCode
    year: Year | None = None
    month: Month | None = None
    api_url: str = OPENDATA_API_URL
    dataType: Literal["CLMMAXT"] = field(default="CLMMAXT", init=False)
    rformat: Literal["json"] = field(default="json", init=False)


@dataclass
class DailyMinTempRequest(HasApiUrl):
    station: ClimatologicalStationCode
    year: Year | None = None
    month: Month | None = None
    api_url: str = OPENDATA_API_URL
    dataType: Literal["CLMMINT"] = field(default="CLMMINT", init=False)
    rformat: Literal["json"] = field(default="json", init=False)


@dataclass
class WeatherRadiationRequest(HasApiUrl):
    date: DateStr
    """Date in YYYYMMDD format. Valid for past dates only."""
    station: WeatherRadiationStationCode | None = None
    api_url: str = OPENDATA_API_URL
    dataType: Literal["RYES"] = field(default="RYES", init=False)
    lang: Lang = "en"


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: LocalForecastRequest
) -> LocalForecastResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: ForecastRequest
) -> ForecastResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: CurrentWeatherReportRequest
) -> RhrreadResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: WarningInfoRequest
) -> WarningInfoResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: WarningSummaryRequest
) -> WarningSummaryResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: SpecialWeatherTipsRequest
) -> SpecialWeatherTipsResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: QuickEarthquakeMessagesRequest
) -> EarthquakeItem: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: LocallyFeltEarthTremorRequest
) -> FeltEarthquakeItem: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: HourlyRainfallRequest
) -> HourlyRainfallResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: LunarDateRequest
) -> LunarDateResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient,
    request: SunriseSunsetRequest
    | MoonriseMoonsetRequest
    | TidesHourlyRequest
    | TidesHighLowRequest
    | LightningRequest
    | VisibilityRequest,
) -> CsvDataResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient,
    request: DailyMeanTempRequest | DailyMaxTempRequest | DailyMinTempRequest,
) -> ClimatologicalDataResponse: ...


@overload
async def fetch_hko_opendata(
    client: httpx.AsyncClient, request: WeatherRadiationRequest
) -> WeatherRadiationResponse: ...


async def fetch_hko_opendata(client: httpx.AsyncClient, request: HasApiUrl) -> Any:
    params = asdict(request)  # type: ignore
    url = params.pop("api_url")
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json()
