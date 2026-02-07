from typing import Annotated, TypeAlias, TypeVar

import isqx
from annotated_types import Gt, Le

_T = TypeVar("_T")

Hk80Easting = Annotated[_T, isqx.M]
Hk80Northing = Annotated[_T, isqx.M]
LatitudeDeg = Annotated[_T, isqx.LATITUDE(isqx.DEG)]
LongitudeDeg = Annotated[_T, isqx.LONGITUDE(isqx.DEG)]
TideM = Annotated[_T, isqx.M]

Year: TypeAlias = int
Month: TypeAlias = Annotated[int, Gt(0), Le(12)]
Day: TypeAlias = Annotated[int, Gt(0), Le(31)]
Hour: TypeAlias = Annotated[int, Gt(0), Le(23)]

HkoStationId: TypeAlias = str
HydroStationId: TypeAlias = str
