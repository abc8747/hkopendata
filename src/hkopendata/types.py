from typing import Annotated, TypeAlias, TypeVar

import isqx

_T = TypeVar("_T")

Hk80Easting = Annotated[_T, isqx.M]
Hk80Northing = Annotated[_T, isqx.M]
LatitudeDeg = Annotated[_T, isqx.LATITUDE(isqx.DEG)]
LongitudeDeg = Annotated[_T, isqx.LONGITUDE(isqx.DEG)]
TideM = Annotated[_T, isqx.M]

HkoStationId: TypeAlias = str
HydroStationId: TypeAlias = str
