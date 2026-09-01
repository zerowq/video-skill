import json
from pathlib import Path

import pytest

from video_skill.models import PlanError, plan_from_dict
from video_skill.workflow import build_prompt, idempotency_key, validate_plan


def example_plan() -> dict:
    return json.loads((Path(__file__).parents[1] / "examples/product.json").read_text())


def test_validate_and_build_prompt_freezes_reference_aliases():
    plan = validate_plan(example_plan())
    prompt = build_prompt(plan)
    assert "参考图 1（@图像1）作为主体正视图" in prompt
    assert plan.references[0].ordinal == 1
    assert idempotency_key(plan).startswith("video-")


def test_non_contiguous_references_are_rejected():
    raw = example_plan()
    raw["references"][0]["ordinal"] = 2
    with pytest.raises(PlanError, match="ordinal"):
        validate_plan(raw)


def test_unknown_fields_are_rejected():
    raw = example_plan()
    raw["provider_secret"] = "should-not-be-here"
    with pytest.raises(PlanError, match="未知字段"):
        plan_from_dict(raw)


def test_duration_and_audio_contract_are_enforced():
    raw = example_plan()
    raw["duration_seconds"] = 10
    with pytest.raises(PlanError, match="15 秒"):
        validate_plan(raw)
    raw = example_plan()
    raw["generate_audio"] = False
    with pytest.raises(PlanError, match="generate_audio"):
        validate_plan(raw)
