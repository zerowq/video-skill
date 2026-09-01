---
name: video-skill
description: Build and run a structured AI video production workflow from a VideoPlan, including reference binding, deterministic prompt construction, preflight validation, renderer execution, and artifact delivery. Use when a user asks to generate a video from text, product images, or a storyboard and the host has a compatible renderer.
---

# Video Skill

Use this skill to turn a video request into a validated, reproducible production job.

## Workflow

1. Understand the user's goal, audience, subject, style, aspect ratio, duration, audio intent, and constraints.
2. Build a `VideoPlan`. Keep creative decisions in the plan; do not hide them in free-form provider prompts.
3. Normalize the plan and references. Reference ordinals must be contiguous (`1..N`) and stable.
4. Run plan preflight before any provider call.
5. Build the provider prompt deterministically. Bind `@图像1`, `@图像2`, ... to the exact ordered reference array.
6. Run request preflight and create one renderer task for one user request unless the selected renderer explicitly documents another contract.
7. Poll the original task, then download, validate, store, and publish the resulting video artifact.

## Core invariants

- Do not create a task when plan or request preflight fails.
- Do not let a Prompt Builder invent new creative content.
- Do not treat a 3x3 storyboard as nine video tasks. It is one static reference unless the renderer contract says otherwise.
- Do not report success merely because a provider returned a URL; the artifact must be playable and accessible through the delivery sink.
- Keep provider credentials, private URLs, internal routing, user assets, and host-specific event protocols outside this skill.

## Repository runtime

The bundled `video_skill` package is host-independent and provides the plan model, normalizer, preflight checks, prompt builder, adapter protocols, and an optional Seedance HTTP renderer. Use `video-skill validate <file>` or `video-skill build-prompt <file>` for local dry runs. Use `VIDEO_SKILL_BASE_URL=... VIDEO_SKILL_API_KEY=... video-skill render <file>` only when you intend to create a provider task.

For a real render, implement or install a renderer adapter and configure its credentials outside the plan file. Read `references/adapter-contract.md` before adding a provider integration.

## References

- Read [references/plan-schema.md](references/plan-schema.md) when constructing or validating a plan.
- Read [references/adapter-contract.md](references/adapter-contract.md) when implementing a renderer, storage, or delivery adapter.
