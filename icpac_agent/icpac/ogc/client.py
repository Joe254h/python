"""Shared async HTTP client for OGC requests.

Adds the three things every OGC call in this agent needs: retry with
backoff (public geoportals are flaky), a small TTL cache (a comparison
across eight counties must not re-fetch the same coverage eight times),
and OGC ServiceException detection - servers return HTTP 200 with an XML
error body, which would otherwise sail through as success.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any
from xml.etree import ElementTree

import httpx

from ..config import Endpoint, settings


class OGCError(RuntimeError):
    """An OGC ServiceException, or a transport failure we could not retry past."""


@dataclass
class _CacheEntry:
    value: tuple[bytes, str]
    expires: float


@dataclass
class OGCClient:
    """One client for the lifetime of a request (or the whole server)."""

    client: httpx.AsyncClient
    _cache: dict[str, _CacheEntry] = field(default_factory=dict)
    _gate: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(settings.concurrency)
    )
    last_call_cached: bool = False

    @classmethod
    def create(cls) -> "OGCClient":
        return cls(
            client=httpx.AsyncClient(
                timeout=settings.timeout,
                follow_redirects=True,
                verify=settings.verify_tls,
                headers={"User-Agent": settings.user_agent},
                limits=httpx.Limits(max_connections=settings.concurrency * 2),
            )
        )

    async def aclose(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "OGCClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    # ------------------------------------------------------------------
    @staticmethod
    def _key(url: str, params: dict[str, Any]) -> str:
        blob = url + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hashlib.sha1(blob.encode()).hexdigest()

    def _cached(self, key: str) -> tuple[bytes, str] | None:
        entry = self._cache.get(key)
        if entry and entry.expires > time.monotonic():
            return entry.value
        if entry:
            self._cache.pop(key, None)
        return None

    def _store(self, key: str, value: tuple[bytes, str], ttl: int) -> None:
        if ttl > 0:
            self._cache[key] = _CacheEntry(value, time.monotonic() + ttl)

    # ------------------------------------------------------------------
    async def get(
        self,
        endpoint: Endpoint,
        params: dict[str, Any],
        *,
        ttl: int | None = None,
        expect: str = "",
    ) -> tuple[bytes, str]:
        """GET an OGC request. Returns (body, content-type).

        ``expect`` is a substring of the content type we want; when the
        server returns something else (typically an XML exception where we
        asked for an image) the body is parsed for a ServiceException and
        raised as :class:`OGCError`.
        """
        params = {k: v for k, v in params.items() if v not in (None, "")}
        key = self._key(endpoint.url, params)
        ttl = settings.data_ttl if ttl is None else ttl

        if (hit := self._cached(key)) is not None:
            self.last_call_cached = True
            return hit
        self.last_call_cached = False

        last: Exception | None = None
        for attempt in range(settings.retries + 1):
            try:
                async with self._gate:
                    resp = await self.client.get(
                        endpoint.url,
                        params=params,
                        auth=endpoint.auth,
                        headers=endpoint.headers or None,
                    )
                if resp.status_code >= 500 and attempt < settings.retries:
                    await asyncio.sleep(2**attempt)
                    continue
                resp.raise_for_status()

                content_type = resp.headers.get("content-type", "").lower()
                body = resp.content

                if exception := service_exception(body, content_type):
                    raise OGCError(exception)
                if expect and expect not in content_type:
                    raise OGCError(
                        f"expected {expect}, server returned {content_type or 'no content-type'}"
                    )

                self._store(key, (body, content_type), ttl)
                return body, content_type

            except OGCError:
                raise
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last = exc
                if attempt < settings.retries:
                    await asyncio.sleep(2**attempt)
                    continue
            except httpx.HTTPStatusError as exc:
                raise OGCError(f"HTTP {exc.response.status_code} from {endpoint.name}") from exc

        raise OGCError(f"{type(last).__name__}: {last}") from last


def service_exception(body: bytes, content_type: str = "") -> str:
    """Return the message of an OGC ServiceException, or '' when there is none."""
    looks_xml = "xml" in content_type or body[:200].lstrip().startswith(b"<")
    if not looks_xml:
        return ""
    head = body[:400].lower()
    if b"exception" not in head and b"error" not in head:
        return ""
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return ""
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"serviceexception", "exceptiontext", "exception"}:
            text = (element.text or "").strip()
            if text:
                return " ".join(text.split())[:400]
            code = element.get("exceptionCode") or element.get("code")
            if code:
                return f"ServiceException: {code}"
    return ""


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
