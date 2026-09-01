import json
from pathlib import Path

from video_skill.adapters import RenderRequest
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

    renderer = SeedanceRenderer(base_url="https://gateway.example", output_dir=tmp_path, poll_interval_seconds=0, opener=opener)
    artifact = renderer.wait(renderer.create(request()))
    assert artifact.task_id == "seed-1"
    assert artifact.path.read_bytes().startswith(b"....ftyp")
    assert [call[0] for call in calls] == ["POST", "GET", "GET"]
    assert calls[0][2]["content"][1]["image_url"]["url"].endswith("subject.png")
    assert calls[0][3]["Idempotency-key"] == "video-test-key"


def test_seedance_renderer_does_not_accept_missing_task_id():
    def opener(_req, **_kwargs):
        return FakeResponse(b"{}")

    renderer = SeedanceRenderer(opener=opener)
    try:
        renderer.create(request())
    except SeedanceRendererError as exc:
        assert exc.code == "task_id_missing"
    else:
        raise AssertionError("missing task id should fail")
