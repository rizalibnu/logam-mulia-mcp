"""Unit tests for the Logam Mulia MCP server tools."""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from logam_mulia_mcp.server import (
    PRICE_SOURCES,
    __version__,
    get_all_prices,
    get_all_sources,
    get_client,
    get_news,
    get_news_detail,
    get_price,
    get_price_history,
    list_sources,
    mcp,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the lazy HTTP client between tests so state is clean."""
    import logam_mulia_mcp.server as srv

    srv._client = None
    yield
    srv._client = None


MOCK_PRICE_RESPONSE = {
    "success": True,
    "data": [
        {
            "source": "pegadaian",
            "displayName": "Pegadaian",
            "material": "gold",
            "materialType": "Antam",
            "weight": 1,
            "weightUnit": "gr",
            "sellPrice": 1587000,
            "buybackPrice": 1530000,
            "currency": "IDR",
            "recordedDate": "2026-06-28",
        }
    ],
    "count": 1,
    "timestamp": "2026-06-28T00:00:00.000Z",
    "cached": True,
}

MOCK_HISTORY_RESPONSE = {
    "success": True,
    "data": [
        {
            "source": "pegadaian",
            "materialType": "Antam",
            "weight": 1,
            "weightUnit": "gr",
            "sellPrice": 1587000,
            "buybackPrice": 1530000,
            "recordedDate": "2026-06-28",
        },
        {
            "source": "pegadaian",
            "materialType": "Antam",
            "weight": 1,
            "weightUnit": "gr",
            "sellPrice": 1586000,
            "buybackPrice": 1529000,
            "recordedDate": "2026-06-27",
        },
    ],
    "success": True,
    "timestamp": "2026-06-28T00:00:00.000Z",
}

MOCK_NEWS_RESPONSE = {
    "success": True,
    "data": [
        {
            "title": "Harga Emas Hari Ini Naik",
            "url": "https://investor.id/article/123",
            "publishedAt": "5 jam yang lalu",
            "summary": "Harga emas dunia bergerak naik",
            "category": "Market",
            "displayName": "Investor.id",
        }
    ],
    "source": "investor-id",
    "timestamp": "2026-06-28T00:00:00.000Z",
}

MOCK_NEWS_DETAIL_RESPONSE = {
    "success": True,
    "data": {
        "title": "Harga Emas Hari Ini Naik",
        "author": "John Doe",
        "publishedAt": "28 Juni 2026",
        "content": "Harga emas hari ini mengalami kenaikan...",
        "tags": "#Harga Emas #emas",
    },
    "timestamp": "2026-06-28T00:00:00.000Z",
}


# ── Config & Identity ───────────────────────────────────────────────────────


class TestServerIdentity:
    def test_version(self):
        assert __version__ == "1.1.0"

    def test_fastmcp_name(self):
        assert mcp.name == "logam-mulia"

    def test_website_url(self):
        """FastMCP has website_url in its init signature."""
        import inspect
        sig = inspect.signature(type(mcp).__init__)
        assert "website_url" in sig.parameters


# ── Tools ───────────────────────────────────────────────────────────────────


class TestListSources:
    def test_returns_all_sources(self):
        result = list_sources()
        for s in PRICE_SOURCES:
            assert s["id"] in result
        assert str(len(PRICE_SOURCES)) in result

    def test_returns_base_url(self):
        result = list_sources()
        assert "logam-mulia-api.iamutaki.workers.dev" in result


class TestGetPrice:
    @patch("logam_mulia_mcp.server._api_get")
    async def test_success(self, mock_api_get):
        mock_api_get.return_value = MOCK_PRICE_RESPONSE
        result = await get_price("pegadaian")
        assert "Pegadaian" in result
        assert "Sell" in result
        assert "Buyback" in result
        assert "Rp1,587,000" in result

    @patch("logam_mulia_mcp.server._api_get")
    async def test_refresh_param(self, mock_api_get):
        mock_api_get.return_value = MOCK_PRICE_RESPONSE
        await get_price("pegadaian", refresh=True)
        # params passed as 2nd positional arg
        args = mock_api_get.call_args[0]
        assert "/api/prices/pegadaian" in args[0]
        assert args[1].get("refresh") == "true"

    @patch("logam_mulia_mcp.server._api_get")
    async def test_404_source_not_found(self, mock_api_get):
        from httpx import HTTPStatusError, Request
        request = Request("GET", "http://test.com")
        mock_api_get.side_effect = HTTPStatusError(
            "404", request=request, response=httpx.Response(404, request=request)
        )
        result = await get_price("bogus")
        assert "not found" in result.lower()
        assert "list_sources" in result

    @patch("logam_mulia_mcp.server._api_get")
    async def test_connection_error(self, mock_api_get):
        mock_api_get.side_effect = httpx.RequestError("timeout")
        result = await get_price("pegadaian")
        assert "connection error" in result.lower()

    @patch("logam_mulia_mcp.server._api_get")
    async def test_no_data(self, mock_api_get):
        mock_api_get.return_value = {"success": True, "data": [], "timestamp": "..."}
        result = await get_price("pegadaian")
        assert "no price data" in result.lower()


class TestGetPriceHistory:
    @patch("logam_mulia_mcp.server._api_get")
    async def test_success(self, mock_api_get):
        mock_api_get.return_value = MOCK_HISTORY_RESPONSE
        result = await get_price_history("pegadaian")
        assert "History: pegadaian" in result
        assert "Rp1,587,000" in result

    @patch("logam_mulia_mcp.server._api_get")
    async def test_pagination_params(self, mock_api_get):
        mock_api_get.return_value = MOCK_HISTORY_RESPONSE
        await get_price_history("pegadaian", page=2, length=50)
        params = mock_api_get.call_args[0][1]
        assert params["page"] == 2
        assert params["length"] == 50

    @patch("logam_mulia_mcp.server._api_get")
    async def test_filter_params(self, mock_api_get):
        mock_api_get.return_value = MOCK_HISTORY_RESPONSE
        await get_price_history("galeri24", weight=10, material="gold", material_type="ANTAM")
        params = mock_api_get.call_args[0][1]
        assert params["weight"] == 10
        assert params["material"] == "gold"
        assert params["materialType"] == "ANTAM"

    @patch("logam_mulia_mcp.server._api_get")
    async def test_length_max_1000(self, mock_api_get):
        mock_api_get.return_value = MOCK_HISTORY_RESPONSE
        await get_price_history("pegadaian", length=9999)
        params = mock_api_get.call_args[0][1]
        assert params["length"] == 1000


class TestGetAllPrices:
    @patch("logam_mulia_mcp.server._api_get")
    async def test_includes_all_sources(self, mock_api_get):
        mock_api_get.return_value = MOCK_PRICE_RESPONSE
        result = await get_all_prices()
        for s in PRICE_SOURCES:
            assert s["id"] in result


class TestGetAllSources:
    def test_returns_structured_list(self):
        result = get_all_sources()
        assert isinstance(result, list)
        assert len(result) == len(PRICE_SOURCES)
        assert result[0]["id"] == PRICE_SOURCES[0]["id"]
        assert result[0]["name"] == PRICE_SOURCES[0]["name"]


class TestGetNews:
    @patch("logam_mulia_mcp.server._api_get")
    async def test_success(self, mock_api_get):
        mock_api_get.return_value = MOCK_NEWS_RESPONSE
        result = await get_news()
        assert "Harga Emas Hari Ini Naik" in result
        assert "Market" in result

    @patch("logam_mulia_mcp.server._api_get")
    async def test_no_news(self, mock_api_get):
        mock_api_get.return_value = {"success": True, "data": [], "timestamp": "..."}
        result = await get_news()
        assert "no news" in result.lower()


class TestGetNewsDetail:
    @patch("logam_mulia_mcp.server._api_get")
    async def test_success(self, mock_api_get):
        mock_api_get.return_value = MOCK_NEWS_DETAIL_RESPONSE
        result = await get_news_detail("https://investor.id/article/123")
        assert "Harga Emas Hari Ini Naik" in result
        assert "John Doe" in result


# ── HTTP Client ─────────────────────────────────────────────────────────────


class TestHttpClient:
    def test_get_client_returns_instance(self):
        client = get_client()
        assert isinstance(client, httpx.AsyncClient)

    def test_get_client_is_singleton(self):
        c1 = get_client()
        c2 = get_client()
        assert c1 is c2

    def test_client_base_url(self):
        client = get_client()
        assert "logam-mulia-api" in str(client.base_url)

    def test_client_custom_base_url(self, monkeypatch):
        monkeypatch.setenv("LOGAM_MULIA_BASE_URL", "https://custom.example.com/api")
        import importlib
        import logam_mulia_mcp.server as srv
        importlib.reload(srv)
        client = srv.get_client()
        assert "custom.example.com" in str(client.base_url)


# ── ENV Override ───────────────────────────────────────────────────────────


class TestConfigEnv:
    def test_default_transport(self):
        from logam_mulia_mcp.server import TRANSPORT
        assert TRANSPORT == "stdio"

    def test_default_timeout(self):
        from logam_mulia_mcp.server import HTTP_TIMEOUT
        assert HTTP_TIMEOUT == 30
