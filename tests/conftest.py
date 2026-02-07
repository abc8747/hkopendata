from typing import AsyncGenerator

import httpx
import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(http1=False, http2=True) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
async def client_http1() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(http1=True, http2=False) as client:
        yield client
