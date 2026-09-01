from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

from .models import ROLE_LABELS, PlanError, VideoPlan, VideoReference, plan_from_dict
from .adapters import RenderRequest


def normalize_plan(plan: VideoPlan) -> VideoPlan:
    if plan.storyboard_strategy not in {"none", "reuse_user_storyboard", "generate_storyboard_grid"}:
        raise PlanError(f"不支持的 storyboard_strategy: {plan.storyboard_strategy}")
    refs = sorted(plan.references, key=lambda item: item.ordinal)
    if not refs:
        raise PlanError("至少需要一张参考图")
    expected = list(range(1, len(refs) + 1))
    if [item.ordinal for item in refs] != expected:
        raise PlanError("参考图 ordinal 必须按 1..N 连续排列")
    asset_ids = [item.asset_id for item in refs]
    if len(asset_ids) != len(set(asset_ids)):
        raise PlanError("参考图 asset_id 不能重复")
    if plan.duration_seconds != 15 or plan.brief.duration_seconds != 15:
        raise PlanError("当前核心契约固定为 15 秒")
    if plan.generate_audio is not True:
        raise PlanError("当前核心契约要求 generate_audio=true")
    return replace(plan, references=refs, aspect_ratio=plan.aspect_ratio or plan.brief.aspect_ratio, resolution=plan.resolution or "720p")


def validate_plan(raw: dict[str, Any] | VideoPlan) -> VideoPlan:
    plan = raw if isinstance(raw, VideoPlan) else plan_from_dict(raw)
    return normalize_plan(plan)


def idempotency_key(plan: VideoPlan, *, request_id: str = "video-skill") -> str:
    if plan.idempotency_key.strip():
        return plan.idempotency_key.strip()
    payload = {
        "request_id": request_id,
        "goal": plan.brief.goal,
        "references": [(ref.asset_id, ref.url) for ref in plan.references],
        "aspect_ratio": plan.aspect_ratio,
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
    return f"video-{digest}"


def build_prompt(raw: dict[str, Any] | VideoPlan) -> str:
    plan = validate_plan(raw)
    refs = plan.references
    style = plan.brief.style or "统一、克制的电影感视觉风格"
    lines = [
        f"电影级品牌概念短片，时长 15 秒，整体风格为 {style}。",
        "参考素材绑定：",
    ]
    for index, ref in enumerate(refs, 1):
        label = ref.label or ROLE_LABELS[ref.role]
        lines.append(f"参考图 {index}（@图像{index}）作为{label}，保持其相关视觉信息一致。")
    if plan.storyboard_strategy == "none":
        lines.append("本次不使用九宫格或用户分镜；动作和镜头变化以 Video Brief 与动作描述为准。")
    else:
        lines.append("分镜图是静态视觉参考；按阅读顺序压缩为 3 到 5 个连续节拍，不复制网格边框、编号、文字或拼贴布局。")
    lines.extend([
        f"主体设定：{plan.subject_description or plan.brief.subject or '保持核心主体身份、外观和关键细节一致。'}",
        f"配体设定：{plan.accessory_description or '仅使用与视频目标相关的配体，不新增无关物件。'}",
        f"场景和光线：{plan.scene_description or '保持场景、光线和空间关系统一。'}",
        f"动作和运镜：{plan.motion_description or '动作自然连贯，镜头变化服务于主体展示。'}",
        f"镜头节奏与转场：节奏符合 {plan.rhythm}，保持主体身份、外观和空间关系连续。",
        f"音频意图：{plan.brief.audio_intent}。",
        f"结尾收束：{plan.ending_description}。",
    ])
    if plan.continuity_constraints:
        lines.append("连续性约束：" + "；".join(plan.continuity_constraints) + "。")
    if plan.negative_constraints:
        lines.append("负面约束：" + "；".join(plan.negative_constraints) + "。")
    return "\n\n".join(lines)


def to_render_request(raw: dict[str, Any] | VideoPlan, *, request_id: str = "video-skill") -> RenderRequest:
    plan = validate_plan(raw)
    return RenderRequest(
        prompt=build_prompt(plan),
        references=tuple(reference.url for reference in plan.references),
        aspect_ratio=plan.aspect_ratio,
        duration_seconds=plan.duration_seconds,
        generate_audio=plan.generate_audio,
        idempotency_key=idempotency_key(plan, request_id=request_id),
    )
