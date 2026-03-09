from typing import AsyncGenerator

import httpx
import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.AsyncHTTPTransport(http1=False, http2=True, retries=3)
    async with httpx.AsyncClient(transport=transport) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
async def client_http1() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.AsyncHTTPTransport(http1=True, http2=False, retries=3)
    async with httpx.AsyncClient(transport=transport) as client:
        yield client
