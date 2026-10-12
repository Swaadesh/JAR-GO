"""
Thin, shared HTTP client for calling Narendra's real API.

Every tool goes through here so there's exactly one place to fix
auth/headers/error-handling.
"""
import httpx
from app.config import BACKEND_BASE_URL, PARTNER_API_KEY, HTTP_TIMEOUT_SECONDS


def _headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if PARTNER_API_KEY:
        headers["X-API-Key"] = PARTNER_API_KEY
    return headers


async def backend_get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.get(f"{BACKEND_BASE_URL}{path}", params=params, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def backend_post(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(f"{BACKEND_BASE_URL}{path}", json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def backend_patch(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.patch(f"{BACKEND_BASE_URL}{path}", json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()
