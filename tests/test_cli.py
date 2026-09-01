import json
from pathlib import Path

from video_skill import cli
from video_skill.adapters import RenderedVideo, TaskHandle


def test_render_cli_selects_gateway_provider(tmp_path: Path, monkeypatch, capsys):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text((Path(__file__).parents[1] / "examples/product.json").read_text(), encoding="utf-8")
    selected = {}

    class FakeGateway:
        def __init__(self, **kwargs):
            selected.update(kwargs)

        def create(self, _request):
            return TaskHandle(task_id="cli-task")

        def wait(self, _task):
            return RenderedVideo(path=tmp_path / "cli-task.mp4", task_id="cli-task")

    monkeypatch.setattr(cli, "GatewayRenderer", FakeGateway)
    assert cli.main(["render", str(plan_path), "--provider", "gateway", "--base-url", "https://gateway", "--model", "gateway-model", "--output-dir", str(tmp_path)]) == 0
    assert selected == {"base_url": "https://gateway", "model": "gateway-model", "output_dir": str(tmp_path)}
    assert json.loads(capsys.readouterr().out)["task_id"] == "cli-task"


def test_render_cli_defaults_to_seedance_provider(tmp_path: Path, monkeypatch):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text((Path(__file__).parents[1] / "examples/product.json").read_text(), encoding="utf-8")
    selected = []

    class FakeSeedance:
        def __init__(self, **kwargs):
            selected.append(kwargs)

        def create(self, _request):
            return TaskHandle(task_id="seedance-task")

        def wait(self, _task):
            return RenderedVideo(path=tmp_path / "seedance-task.mp4", task_id="seedance-task")

    monkeypatch.setattr(cli, "SeedanceRenderer", FakeSeedance)
    assert cli.main(["render", str(plan_path), "--output-dir", str(tmp_path)]) == 0
    assert selected == [{"base_url": None, "model": None, "output_dir": str(tmp_path)}]
