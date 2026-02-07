from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient

# govhk.mardep.eseago.BuildConfig
ESEAGO_ENDPOINT = "https://eseago.hydro.gov.hk/v2"
VERSION = "3.0.28"
# govhk.mardep.eseago.eSeaGoApp$Companion.initialize
ESEAGO_PARAMS = {"token": "eseago", "app_version": VERSION, "os": "android"}
TIDE_ENDPOINT = "https://tide1.hydro.gov.hk/api"

DATA_DIR = Path(__file__).parent / "data"


def ensure_http1(client: AsyncClient) -> None:
    if getattr(client._transport, "_http2", False):
        raise ValueError(
            "The server (eseago.hydro.gov.hk) does not support HTTP/2 and will "
            "disconnect. Please configure the client with `http2=False`."
        )
