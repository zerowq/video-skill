from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..adapters import RenderRequest, RenderedVideo, Renderer, TaskHandle


DEFAULT_MODEL = "doubao-seedance-2-5-260628"
DEFAULT_BASE_URL = "http://localhost:29813"
TERMINAL_SUCCESS = {"completed", "complete", "completed_success", "succeeded", "success", "done"}
TERMINAL_FAILURE = {"failed", "error", "canceled", "cancelled", "rejected"}


class SeedanceRendererError(RuntimeError):
    """A provider request, task, or download failed."""

    def __init__(self, code: str, message: str, *, retryable: bool = False, status_code: int | None = None):
        self.code = code
        self.retryable = retryable
        self.status_code = status_code
        super().__init__(message)


def _status(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in TERMINAL_SUCCESS:
        return "completed"
    if raw in TERMINAL_FAILURE:
        return "failed"
    if raw in {"running", "processing", "in_progress"}:
        return "running"
    return "accepted"


def _body_payload(body: dict[str, Any]) -> dict[str, Any]:
    data = body.get("data")
    return data if isinstance(data, dict) else body


def _task_id(body: dict[str, Any]) -> str:
    payload = _body_payload(body)
    return str(payload.get("id") or payload.get("task_id") or payload.get("taskId") or "").strip()


def _video_url(body: dict[str, Any]) -> str:
    payload = _body_payload(body)
    content = payload.get("content")
    if isinstance(content, dict):
        value = content.get("video_url") or content.get("videoUrl") or content.get("url")
        if value:
            return str(value).strip()
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"video", "video_url"}:
                value = item.get("url") or item.get("video_url")
                if value:
                    return str(value).strip()
    return str(payload.get("video_url") or payload.get("videoUrl") or payload.get("url") or "").strip()


class SeedanceRenderer(Renderer):
    """HTTP renderer for a Seedance-compatible task gateway.

    The gateway contract is intentionally small: POST ``/v1/videos/generations``
    creates a task and GET the same path plus ``/{task_id}`` polls it. The
    renderer never creates a second task while polling.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        output_dir: str | Path = "./video-output",
        request_timeout_seconds: float = 60.0,
        poll_interval_seconds: float = 5.0,
        max_wait_seconds: float = 900.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.base_url = (base_url or os.getenv("VIDEO_SKILL_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("VIDEO_SKILL_API_KEY", "")
        self.model = model
        self.output_dir = Path(output_dir)
        self.request_timeout_seconds = max(0.1, float(request_timeout_seconds))
        self.poll_interval_seconds = max(0.0, float(poll_interval_seconds))
        self.max_wait_seconds = max(0.1, float(max_wait_seconds))
        self._opener = opener

    def _headers(self, request: RenderRequest | None = None) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if request and request.idempotency_key:
            headers["Idempotency-Key"] = request.idempotency_key
            headers["X-Request-Id"] = request.idempotency_key
        return headers

    def _json_request(self, method: str, url: str, *, payload: dict[str, Any] | None = None, request: RenderRequest | None = None) -> dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        http_request = Request(url, data=data, headers=self._headers(request), method=method)
        try:
            with self._opener(http_request, timeout=self.request_timeout_seconds) as response:
                raw = response.read()
                status_code = int(getattr(response, "status", 200))
        except HTTPError as exc:
            raw = exc.read()
            message = raw.decode("utf-8", errors="replace")[:500]
            raise SeedanceRendererError("provider_http_error", message or str(exc), retryable=exc.code >= 500, status_code=exc.code) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise SeedanceRendererError("provider_network_error", str(exc), retryable=True) from exc
        if not 200 <= status_code < 300:
            raise SeedanceRendererError("provider_http_error", raw.decode("utf-8", errors="replace")[:500], retryable=status_code >= 500, status_code=status_code)
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SeedanceRendererError("provider_invalid_json", "视频网关返回了无法解析的 JSON") from exc
        if not isinstance(body, dict):
            raise SeedanceRendererError("provider_invalid_response", "视频网关返回结构不是对象")
        return body

    def create(self, request: RenderRequest) -> TaskHandle:
        if not request.prompt.strip():
            raise SeedanceRendererError("prompt_required", "视频 Prompt 不能为空")
        if len(request.references) < 1:
            raise SeedanceRendererError("reference_required", "至少需要一张参考图")
        content = [{"type": "text", "text": request.prompt}]
        content.extend(
            {"type": "image_url", "role": "reference_image", "image_url": {"url": url}}
            for url in request.references
        )
        payload = {
            "model": self.model,
            "content": content,
            "duration": request.duration_seconds,
            "generate_audio": request.generate_audio,
            "ratio": request.aspect_ratio,
            "resolution": "720p",
            "return_last_frame": True,
        }
        body = self._json_request("POST", f"{self.base_url}/v1/videos/generations", payload=payload, request=request)
        task_id = _task_id(body)
        if not task_id:
            raise SeedanceRendererError("task_id_missing", "视频网关创建响应缺少任务 ID")
        return TaskHandle(task_id=task_id)

    def wait(self, task: TaskHandle) -> RenderedVideo:
        task_id = str(task.task_id or "").strip()
        if not task_id:
            raise SeedanceRendererError("task_id_required", "轮询视频任务必须提供 task_id")
        deadline = time.monotonic() + self.max_wait_seconds
        latest: dict[str, Any] = {}
        while time.monotonic() <= deadline:
            latest = self._json_request("GET", f"{self.base_url}/v1/videos/generations/{task_id}")
            state = _status(_body_payload(latest).get("status"))
            if state == "failed":
                message = str(_body_payload(latest).get("error") or "视频任务失败")[:500]
                raise SeedanceRendererError("task_failed", message)
            if state == "completed":
                url = _video_url(latest)
                if not url:
                    raise SeedanceRendererError("video_url_missing", "视频任务完成但响应缺少视频 URL")
                return self._download(task_id, url)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(self.poll_interval_seconds, remaining))
        raise SeedanceRendererError("poll_timeout", f"视频任务 {task_id} 轮询超时", retryable=True)

    def _download(self, task_id: str, url: str) -> RenderedVideo:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        target = self.output_dir / f"{task_id}.mp4"
        partial = target.with_suffix(".mp4.part")
        request = Request(url, headers={"Accept": "video/mp4"}, method="GET")
        try:
            with self._opener(request, timeout=self.request_timeout_seconds) as response:
                status_code = int(getattr(response, "status", 200))
                if not 200 <= status_code < 300:
                    raise SeedanceRendererError("download_http_error", f"视频下载返回 HTTP {status_code}", retryable=status_code >= 500, status_code=status_code)
                with partial.open("wb") as stream:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        stream.write(chunk)
        except SeedanceRendererError:
            partial.unlink(missing_ok=True)
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            partial.unlink(missing_ok=True)
            raise SeedanceRendererError("download_failed", str(exc), retryable=True) from exc
        if not partial.exists() or partial.stat().st_size == 0:
            partial.unlink(missing_ok=True)
            raise SeedanceRendererError("empty_video", "视频下载结果为空")
        partial.replace(target)
        return RenderedVideo(path=target, task_id=task_id)


__all__ = ["DEFAULT_MODEL", "SeedanceRenderer", "SeedanceRendererError"]
