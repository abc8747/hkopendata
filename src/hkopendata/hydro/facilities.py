from __future__ import annotations

import httpx
from pydantic_xml import BaseXmlModel, element, wrapped

from . import ESEAGO_ENDPOINT, ESEAGO_PARAMS, ensure_http1


class Facility(BaseXmlModel, tag="facility"):
    display_name_tc: str = element()
    display_name_sc: str = element()
    display_name_en: str = element()
    facility_version: int = element()
    facility_type: str = element()
    facility_path: str = element()
    facility_key: str = element()
    facility_seq: int = element()


class Facilities(BaseXmlModel, tag="result"):
    facility_list: list[Facility] = wrapped("facility_list", element(tag="facility"))

    @staticmethod
    async def fetch(client: httpx.AsyncClient) -> Facilities:
        ensure_http1(client)
        response = await client.get(
            f"{ESEAGO_ENDPOINT}/harbour_facilities", params=ESEAGO_PARAMS
        )
        response.raise_for_status()
        return Facilities.from_xml(response.text)
