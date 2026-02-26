#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Residential Proxy Manager for Instagram Scraper
Supports Bright Data, IProyal, Storm Proxies, NetNut, and custom providers.

Usage:
    from proxy_manager import ProxyManager

    # From config file
    pm = ProxyManager.from_config()

    # From environment variables
    pm = ProxyManager.from_env()

    # Get Playwright proxy dict
    proxy = pm.get_playwright_proxy()

    # Get requests/aiohttp proxy dict
    proxies = pm.get_requests_proxy()
"""

import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "scraper_config.json"

# Default host/port per provider
PROVIDER_DEFAULTS: Dict[str, Dict[str, object]] = {
    "brightdata": {"host": "brd.superproxy.io", "port": 22225},
    "iproyal": {"host": "proxy.iproyal.com", "port": 12321},
    "stormproxies": {"host": "rotating.stormproxies.com", "port": 9999},
    "netnut": {"host": "gw-resi.netnut.io", "port": 5959},
}


class ProxyManager:
    """Manages residential proxy configuration and session rotation."""

    def __init__(
        self,
        provider: str = "brightdata",
        host: str = "",
        port: int = 0,
        username: str = "",
        password: str = "",
        country: str = "",
        sticky: bool = True,
        sticky_ttl_minutes: int = 10,
        enabled: bool = True,
    ):
        self.provider = provider.lower().strip()
        self.username = username
        self.password = password
        self.country = country.lower().strip()
        self.sticky = sticky
        self.sticky_ttl_minutes = sticky_ttl_minutes
        self.enabled = enabled

        # Resolve host / port from provider defaults if not supplied
        defaults = PROVIDER_DEFAULTS.get(self.provider, {})
        self.host = host or defaults.get("host", "")
        self.port = port or defaults.get("port", 0)

        # Session ID for sticky sessions
        self._session_id: str = self._generate_session_id()

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls, config_path: Path = None) -> "ProxyManager":
        """Build a ProxyManager from ``config/scraper_config.json``."""
        path = config_path or CONFIG_PATH
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
        except Exception as exc:
            logger.warning("Could not load config (%s): %s – falling back to env", path, exc)
            return cls.from_env()

        proxy_cfg = cfg.get("proxy", {})
        if not proxy_cfg.get("enabled", False):
            return cls(enabled=False)

        return cls(
            provider=proxy_cfg.get("provider", "brightdata"),
            host=proxy_cfg.get("host", ""),
            port=proxy_cfg.get("port", 0),
            username=proxy_cfg.get("username", "") or os.getenv("PROXY_USERNAME", ""),
            password=proxy_cfg.get("password", "") or os.getenv("PROXY_PASSWORD", ""),
            country=proxy_cfg.get("country", "") or os.getenv("PROXY_COUNTRY", ""),
            sticky=proxy_cfg.get("sticky", True),
            sticky_ttl_minutes=proxy_cfg.get("sticky_ttl_minutes", 10),
            enabled=True,
        )

    @classmethod
    def from_env(cls) -> "ProxyManager":
        """Build a ProxyManager purely from environment variables."""
        enabled = os.getenv("PROXY_ENABLED", "false").lower() in ("true", "1", "yes")
        if not enabled:
            return cls(enabled=False)

        return cls(
            provider=os.getenv("PROXY_PROVIDER", "brightdata"),
            host=os.getenv("PROXY_HOST", ""),
            port=int(os.getenv("PROXY_PORT", "0")),
            username=os.getenv("PROXY_USERNAME", ""),
            password=os.getenv("PROXY_PASSWORD", ""),
            country=os.getenv("PROXY_COUNTRY", ""),
            sticky=os.getenv("PROXY_STICKY", "true").lower() in ("true", "1", "yes"),
            sticky_ttl_minutes=int(os.getenv("PROXY_STICKY_TTL", "10")),
            enabled=True,
        )

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_session_id() -> str:
        return uuid.uuid4().hex[:12]

    def rotate_session(self) -> str:
        """Generate a new session ID (forces a new IP on next request)."""
        self._session_id = self._generate_session_id()
        logger.info("Proxy session rotated → %s", self._session_id)
        return self._session_id

    @property
    def session_id(self) -> str:
        return self._session_id

    # ------------------------------------------------------------------
    # Credential building (provider-specific username formats)
    # ------------------------------------------------------------------

    def _build_proxy_username(self) -> str:
        """Return the provider-formatted proxy username string."""
        base = self.username

        if self.provider == "brightdata":
            # Bright Data format: brd-customer-<id>-zone-<zone>-country-<cc>-session-<sid>
            parts = [base]
            if self.country:
                parts.append(f"country-{self.country}")
            if self.sticky:
                parts.append(f"session-{self._session_id}")
            return "-".join(parts)

        if self.provider == "netnut":
            parts = [base]
            if self.country:
                parts.append(f"country-{self.country}")
            if self.sticky:
                parts.append(f"session-{self._session_id}")
            return "-".join(parts)

        if self.provider == "iproyal":
            parts = [base]
            if self.country:
                parts.append(f"country-{self.country}")
            if self.sticky:
                parts.append(f"session-{self._session_id}")
                parts.append(f"sessTime-{self.sticky_ttl_minutes}")
            return "_".join(parts)

        if self.provider == "stormproxies":
            # Storm Proxies typically uses plain user:pass
            return base

        # custom / fallback
        return base

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def get_playwright_proxy(self) -> Optional[Dict]:
        """Return a dict suitable for Playwright's ``proxy`` context option."""
        if not self.enabled or not self.host:
            return None

        return {
            "server": f"http://{self.host}:{self.port}",
            "username": self._build_proxy_username(),
            "password": self.password,
        }

    def get_requests_proxy(self) -> Optional[Dict[str, str]]:
        """Return a dict suitable for ``requests`` / ``aiohttp`` libraries."""
        if not self.enabled or not self.host:
            return None

        user = self._build_proxy_username()
        url = f"http://{user}:{self.password}@{self.host}:{self.port}"
        return {"http": url, "https": url}

    def info(self) -> str:
        """Return a human-readable summary string."""
        if not self.enabled:
            return "<ProxyManager disabled>"
        return (
            f"<ProxyManager provider={self.provider} enabled "
            f"host={self.host}:{self.port} country={self.country or 'any'} "
            f"sticky={self.sticky} session={self._session_id}>"
        )

    def __repr__(self) -> str:
        return self.info()
