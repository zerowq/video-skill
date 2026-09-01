# VideoPlan Schema

The public plan is JSON. Unknown fields should be rejected so that provider-specific options do not silently leak into the core contract.

Required fields:

```json
{
  "brief": {
    "goal": "产品概念短片",
    "subject": "产品主体",
    "audience": "目标受众",
    "style": "克制的电影感",
    "duration_seconds": 15,
    "aspect_ratio": "16:9",
    "audio_intent": "生成与画面匹配的音频",
    "user_constraints": []
  },
  "storyboard_strategy": "none",
  "references": [
    {"ordinal": 1, "asset_id": "subject-1", "role": "subject", "label": "主体参考", "url": "https://example.com/subject.png"}
  ],
  "subject_description": "主体外观与关键细节",
  "scene_description": "场景、光线和空间关系",
  "motion_description": "动作和运镜",
  "continuity_constraints": ["保持主体身份一致"],
  "rhythm": "自然、连贯",
  "ending_description": "画面自然收束",
  "negative_constraints": ["不出现额外文字、水印或 Logo"],
  "aspect_ratio": "16:9",
  "duration_seconds": 15,
  "generate_audio": true
}
```

Supported `storyboard_strategy` values are `none`, `reuse_user_storyboard`, and `generate_storyboard_grid`. A reference uses one of `subject`, `accessory`, `scene`, or `storyboard` roles.

The bundled runtime currently enforces a 15-second request, `generate_audio=true`, supported Seedance-style ratios, contiguous reference ordinals, and HTTP(S) reference URLs. Provider-specific duration or resolution policies belong in an adapter or a future versioned profile.
