from typing import Annotated, TypeAlias, TypeVar

import isqx
from annotated_types import Gt, Le
from isqx import usc

_T = TypeVar("_T")

Hk80Easting = Annotated[_T, isqx.M]
Hk80Northing = Annotated[_T, isqx.M]
LatitudeDeg = Annotated[_T, isqx.LATITUDE(isqx.DEG)]
LongitudeDeg = Annotated[_T, isqx.LONGITUDE(isqx.DEG)]
TideM = Annotated[_T, isqx.M]

StaticPressureHPa = Annotated[_T, isqx.STATIC_PRESSURE(isqx.HECTO * isqx.PA)]
TemperatureC = Annotated[_T, isqx.TEMPERATURE(isqx.CELSIUS)]
RelativeHumidity = Annotated[_T, isqx.RELATIVE_HUMIDITY]

SpeedKmh = Annotated[_T, isqx.SPEED(isqx.KILO * isqx.M / isqx.HOUR)]
SpeedKt = Annotated[_T, isqx.SPEED(usc.KNOT)]
SpeedMs = Annotated[_T, isqx.SPEED(isqx.M_PERS)]

AngleDeg = Annotated[_T, isqx.ANGLE(isqx.DEG)]
HeightM = Annotated[_T, isqx.HEIGHT(isqx.M)]
PeriodS = Annotated[_T, isqx.PERIOD(isqx.S)]

Year: TypeAlias = int
Month: TypeAlias = Annotated[int, Gt(0), Le(12)]
Day: TypeAlias = Annotated[int, Gt(0), Le(31)]
Hour: TypeAlias = Annotated[int, Gt(0), Le(23)]

HkoStationId: TypeAlias = str
HydroStationId: TypeAlias = str
