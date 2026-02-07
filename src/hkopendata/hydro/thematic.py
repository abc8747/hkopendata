from __future__ import annotations

import httpx
from pydantic_xml import BaseXmlModel, element, wrapped

from . import ESEAGO_ENDPOINT, ESEAGO_PARAMS, ensure_http1


class ThematicLayer(BaseXmlModel, tag="layer"):
    display_name_tc: str = element()
    display_name_sc: str = element()
    display_name_en: str = element()
    layer_version: int = element()
    layer_type: str = element()
    layer_path: str = element()
    layer_key: str = element()
    layer_seq: int = element()


class ThematicLayers(BaseXmlModel, tag="result"):
    layer_list: list[ThematicLayer] = wrapped("layer_list")

    @staticmethod
    async def fetch(client: httpx.AsyncClient) -> ThematicLayers:
        ensure_http1(client)
        response = await client.get(
            f"{ESEAGO_ENDPOINT}/thematic_layers", params=ESEAGO_PARAMS
        )
        response.raise_for_status()
        return ThematicLayers.from_xml(response.text)
