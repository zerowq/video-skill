from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable
from urllib.request import urlopen

from ._http import HttpTaskRenderer, RendererError


DEFAULT_MODEL = "doubao-seedance-2-5-260628"
DEFAULT_TASKS_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"


class SeedanceOfficialRenderer(HttpTaskRenderer):
    """Direct adapter for the official Volcengine Ark Seedance task API."""

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
        resolved_url = base_url or os.getenv("SEEDANCE_BASE_URL") or DEFAULT_TASKS_URL
        resolved_api_key = api_key
        if resolved_api_key is None:
            resolved_api_key = os.getenv("ARK_API_KEY") or os.getenv("VOLCENGINE_API_KEY", "")
        resolved_model = model or os.getenv("SEEDANCE_MODEL") or DEFAULT_MODEL
        super().__init__(
            tasks_url=resolved_url,
            api_key=resolved_api_key,
            model=resolved_model,
            provider_label="Seedance 官方 API",
            output_dir=output_dir,
            require_api_key=True,
            send_idempotency_headers=False,
            request_timeout_seconds=request_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=max_wait_seconds,
            opener=opener,
        )


SeedanceOfficialRendererError = RendererError

__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_TASKS_URL",
    "SeedanceOfficialRenderer",
    "SeedanceOfficialRendererError",
]
