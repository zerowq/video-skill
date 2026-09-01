# video-skill

一个与具体 Agent 宿主、模型网关和对象存储解耦的 AI 视频生产工作流内核。

它把一次视频请求收敛为：结构化 `VideoPlan` → 输入归一化 → 业务预检 → 确定性 Prompt → Renderer 任务 → 成片交付。

## 当前能力

- 纯标准库实现的 `VideoPlan` 校验、归一化和 Prompt Builder
- 参考图 ordinal 与 `@图像N` 的稳定绑定
- 15 秒、音频开启、画幅和分辨率等请求约束预检
- 单任务幂等键生成
- 不需要 API Key 的 dry-run CLI
- Renderer、ArtifactStore、DeliverySink 的可替换接口
- 可选的 Seedance HTTP Renderer（创建、轮询和 MP4 下载）

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
video-skill validate examples/product.json
video-skill build-prompt examples/product.json
# 配置网关后才会创建真实任务：
VIDEO_SKILL_BASE_URL=https://your-gateway.example \
VIDEO_SKILL_API_KEY=your-key \
video-skill render examples/product.json --output-dir ./video-output
```

`build-prompt` 只执行本地计划校验和 Prompt 构建，不会创建云端视频任务。
`render` 会创建一个真实任务并轮询到成片，请确认网关、模型账号和素材授权后再运行。

## 工作流

```text
VideoPlan
  -> normalize
  -> preflight
  -> build_prompt
  -> renderer.create
  -> renderer.wait
  -> artifact_store.put
  -> delivery.publish
```

仓库中的核心包不包含任何内部服务地址、账号信息、OSS 配置或 Inspark 专用协议。

## 项目状态

当前版本是 `0.1.0` 的可运行核心，适合验证计划、Prompt 和适配器边界。真正调用视频模型需要实现一个 Renderer，并自行处理模型账号、版权和平台规则。

## License

Apache-2.0
