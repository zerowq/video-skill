from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable
from urllib.request import urlopen

from ._http import HttpTaskRenderer, RendererError


DEFAULT_MODEL = "doubao-seedance-2-5-260628"
DEFAULT_BASE_URL = "http://localhost:29813"


class GatewayRenderer(HttpTaskRenderer):
    """Renderer for the optional Seedance-compatible gateway contract."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        output_dir: str | Path = "./video-output",
        request_timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 5.0,
        max_wait_seconds: float = 900.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        resolved_base_url = (base_url or os.getenv("VIDEO_SKILL_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        resolved_api_key = api_key if api_key is not None else os.getenv("VIDEO_SKILL_API_KEY", "")
        resolved_model = model or os.getenv("VIDEO_SKILL_MODEL") or DEFAULT_MODEL
        super().__init__(
            tasks_url=f"{resolved_base_url}/v1/videos/generations",
            api_key=resolved_api_key,
            model=resolved_model,
            provider_label="视频网关",
            output_dir=output_dir,
            require_api_key=False,
            send_idempotency_headers=True,
            request_timeout_seconds=request_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=max_wait_seconds,
            opener=opener,
        )


GatewayRendererError = RendererError

__all__ = ["DEFAULT_BASE_URL", "DEFAULT_MODEL", "GatewayRenderer", "GatewayRendererError"]
