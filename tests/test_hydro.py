import httpx
import pytest

from hkopendata.hydro.tiles import _OfflineTilesVersion
from hkopendata.hydro.version import Version


@pytest.mark.anyio
async def test_hydro_version(client_http1: httpx.AsyncClient) -> None:
    xml_content = await Version.fetch_raw(client_http1)
    version = Version.from_xml(xml_content)
    assert version.file_version > 0
    assert Version.load() == version


@pytest.mark.anyio
async def test_hydro_tiles(client_http1: httpx.AsyncClient) -> None:
    xml_content = await _OfflineTilesVersion.fetch(client_http1)
    tiles_version = _OfflineTilesVersion.from_xml(xml_content)
    assert tiles_version.file_path.startswith("http")
