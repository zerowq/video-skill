import json
from pathlib import Path
from urllib.error import HTTPError
from io import BytesIO

import pytest

from video_skill.adapters import RenderRequest, TaskHandle
from video_skill.renderers.gateway import GatewayRenderer, GatewayRendererError
from video_skill.renderers.seedance import SeedanceRenderer, SeedanceRendererError


class FakeResponse:
    def __init__(self, body=b"", status=200):
        self._body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _size=-1):
        body, self._body = self._body, b""
        return body


def request():
    return RenderRequest(
        prompt="生成连续产品运动",
        references=("https://cdn.example/subject.png",),
        idempotency_key="video-test-key",
    )


def test_seedance_renderer_creates_polls_and_downloads(tmp_path: Path):
    calls = []

    def opener(req, timeout):
        calls.append((req.method, req.full_url, json.loads(req.data) if req.data else None, dict(req.header_items())))
        if req.method == "POST":
            return FakeResponse(json.dumps({"id": "seed-1", "status": "queued"}).encode())
        if req.full_url.endswith("/seed-1"):
            return FakeResponse(json.dumps({"id": "seed-1", "status": "succeeded", "content": {"video_url": "https://cdn.example/video.mp4"}}).encode())
        return FakeResponse(b"....ftypisom....")

    renderer = SeedanceRenderer(
        api_key="seedance-test-key",
        base_url="https://seedance.example/v1/videos/generations",
        output_dir=tmp_path,
        poll_interval_seconds=0,
        opener=opener,
    )
    artifact = renderer.wait(renderer.create(request()))
    assert artifact.task_id == "seed-1"
    assert artifact.path.read_bytes().startswith(b"....ftyp")
    assert [call[0] for call in calls] == ["POST", "GET", "GET"]
    assert calls[0][1] == "https://seedance.example/v1/videos/generations"
    assert calls[0][2]["content"][1]["image_url"]["url"].endswith("subject.png")
    assert calls[0][3]["Authorization"] == "Bearer seedance-test-key"
    assert "Idempotency-key" not in calls[0][3]


def test_gateway_renderer_keeps_compatible_contract(tmp_path: Path):
    calls = []

    def opener(req, timeout):
        calls.append((req.method, req.full_url, dict(req.header_items())))
        if req.method == "POST":
            return FakeResponse(json.dumps({"id": "gateway-1"}).encode())
        if req.full_url.endswith("/gateway-1"):
            return FakeResponse(json.dumps({"status": "completed", "video_url": "https://cdn.example/video.mp4"}).encode())
        return FakeResponse(b"video")

    renderer = GatewayRenderer(base_url="https://gateway.example", output_dir=tmp_path, poll_interval_seconds=0, opener=opener)
    renderer.wait(renderer.create(request()))
    assert calls[0][1] == "https://gateway.example/v1/videos/generations"
    assert calls[0][2]["Idempotency-key"] == "video-test-key"


def test_seedance_renderer_requires_api_key(monkeypatch):
    monkeypatch.delenv("SEEDANCE_API_KEY", raising=False)
    renderer = SeedanceRenderer(opener=lambda *_args, **_kwargs: pytest.fail("must not call network"))
    with pytest.raises(SeedanceRendererError, match="SEEDANCE_API_KEY") as exc_info:
        renderer.create(request())
    assert exc_info.value.code == "not_configured"


def test_renderer_rejects_missing_task_id():
    renderer = SeedanceRenderer(api_key="test", opener=lambda *_args, **_kwargs: FakeResponse(b"{}"))
    with pytest.raises(SeedanceRendererError) as exc_info:
        renderer.create(request())
    assert exc_info.value.code == "task_id_missing"


def test_renderer_surfaces_http_error():
    def opener(_req, **_kwargs):
        raise HTTPError("https://seedance.example", 500, "upstream", {}, BytesIO(b"server exploded"))

    renderer = SeedanceRenderer(api_key="test", opener=opener)
    with pytest.raises(SeedanceRendererError) as exc_info:
        renderer.create(request())
    assert exc_info.value.code == "provider_http_error"
    assert exc_info.value.retryable is True
    assert exc_info.value.status_code == 500


def test_wait_rejects_empty_task_id(tmp_path: Path):
    renderer = GatewayRenderer(output_dir=tmp_path)
    with pytest.raises(GatewayRendererError) as exc_info:
        renderer.wait(TaskHandle(task_id=""))
    assert exc_info.value.code == "task_id_required"
