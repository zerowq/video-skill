from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlparse

AspectRatio = Literal["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"]
ReferenceRole = Literal["subject", "accessory", "scene", "storyboard"]
StoryboardStrategy = Literal["none", "reuse_user_storyboard", "generate_storyboard_grid"]

SUPPORTED_RATIOS = {"16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"}
ROLE_LABELS = {"subject": "主体参考", "accessory": "配体参考", "scene": "场景参考", "storyboard": "分镜参考"}


class PlanError(ValueError):
    """Raised when a public VideoPlan cannot be validated."""


@dataclass(frozen=True)
class VideoBrief:
    goal: str
    subject: str = ""
    audience: str = ""
    style: str = ""
    duration_seconds: int = 15
    aspect_ratio: str = "16:9"
    audio_intent: str = "允许渲染器生成与画面匹配的音频"
    user_constraints: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VideoReference:
    ordinal: int
    asset_id: str
    role: ReferenceRole
    url: str
    label: str = ""


@dataclass(frozen=True)
class VideoPlan:
    brief: VideoBrief
    storyboard_strategy: StoryboardStrategy
    references: list[VideoReference] = field(default_factory=list)
    title: str = ""
    storyboard_source: str | None = None
    duration_seconds: int = 15
    generate_audio: bool = True
    subject_description: str = ""
    accessory_description: str = ""
    scene_description: str = ""
    motion_description: str = ""
    continuity_constraints: list[str] = field(default_factory=list)
    rhythm: str = "自然、连贯"
    ending_description: str = "画面自然收束并保持主体清晰"
    negative_constraints: list[str] = field(default_factory=list)
    aspect_ratio: str = "16:9"
    resolution: str = "720p"
    idempotency_key: str = ""


def _text(value: Any, field_name: str = "field", *, required: bool = False) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise PlanError(f"{field_name} 不能为空")
    return text


def _ratio(value: Any) -> str:
    raw = _text(value, "aspect_ratio") or "16:9"
    aliases = {"横屏": "16:9", "竖屏": "9:16", "方形": "1:1", "自适应": "adaptive"}
    raw = aliases.get(raw, raw.replace("：", ":"))
    if raw not in SUPPORTED_RATIOS:
        return "16:9"
    return raw


def _reference(raw: dict[str, Any]) -> VideoReference:
    try:
        ordinal = int(raw.get("ordinal"))
    except (TypeError, ValueError) as exc:
        raise PlanError("references.ordinal 必须是整数") from exc
    role = _text(raw.get("role"), "references.role", required=True)
    if role not in ROLE_LABELS:
        raise PlanError(f"不支持的参考图角色: {role}")
    url = _text(raw.get("url"), "references.url", required=True)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PlanError(f"参考图 URL 必须是 http(s): {url}")
    return VideoReference(
        ordinal=ordinal,
        asset_id=_text(raw.get("asset_id"), "references.asset_id", required=True),
        role=role, url=url, label=_text(raw.get("label")),
    )


def plan_from_dict(raw: dict[str, Any]) -> VideoPlan:
    if not isinstance(raw, dict):
        raise PlanError("VideoPlan 必须是 JSON 对象")
    allowed = {
        "brief", "title", "storyboard_strategy", "storyboard_source", "references",
        "duration_seconds", "generate_audio", "subject_description", "accessory_description",
        "scene_description", "motion_description", "continuity_constraints", "rhythm",
        "ending_description", "negative_constraints", "aspect_ratio", "resolution", "idempotency_key",
    }
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise PlanError(f"未知字段: {', '.join(unknown)}")
    brief_raw = raw.get("brief") or {}
    if not isinstance(brief_raw, dict):
        raise PlanError("brief 必须是对象")
    brief = VideoBrief(
        goal=_text(brief_raw.get("goal"), "brief.goal", required=True),
        subject=_text(brief_raw.get("subject"), "brief.subject"),
        audience=_text(brief_raw.get("audience"), "brief.audience"),
        style=_text(brief_raw.get("style"), "brief.style"),
        duration_seconds=int(brief_raw.get("duration_seconds", 15)),
        aspect_ratio=_ratio(brief_raw.get("aspect_ratio")),
        audio_intent=_text(brief_raw.get("audio_intent")) or "允许渲染器生成与画面匹配的音频",
        user_constraints=[_text(item, "brief.user_constraints") for item in brief_raw.get("user_constraints", [])],
    )
    refs_raw = raw.get("references", [])
    if not isinstance(refs_raw, list):
        raise PlanError("references 必须是数组")
    references = [_reference(item) for item in refs_raw]
    return VideoPlan(
        brief=brief,
        title=_text(raw.get("title")),
        storyboard_strategy=_text(raw.get("storyboard_strategy"), "storyboard_strategy", required=True),
        storyboard_source=_text(raw.get("storyboard_source")) or None,
        references=references,
        duration_seconds=int(raw.get("duration_seconds", 15)),
        generate_audio=bool(raw.get("generate_audio", True)),
        subject_description=_text(raw.get("subject_description")),
        accessory_description=_text(raw.get("accessory_description")),
        scene_description=_text(raw.get("scene_description")),
        motion_description=_text(raw.get("motion_description")),
        continuity_constraints=[_text(item, "continuity_constraints") for item in raw.get("continuity_constraints", [])],
        rhythm=_text(raw.get("rhythm")) or "自然、连贯",
        ending_description=_text(raw.get("ending_description")) or "画面自然收束并保持主体清晰",
        negative_constraints=[_text(item, "negative_constraints") for item in raw.get("negative_constraints", [])],
        aspect_ratio=_ratio(raw.get("aspect_ratio") or brief.aspect_ratio),
        resolution=_text(raw.get("resolution")) or "720p",
        idempotency_key=_text(raw.get("idempotency_key")),
    )
