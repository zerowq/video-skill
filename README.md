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
- 官方 Seedance（火山方舟 Ark）HTTP Renderer，创建、轮询和 MP4 下载
- 可选的 Seedance 兼容网关 Renderer，保留内部部署路径

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
video-skill validate examples/product.json
video-skill build-prompt examples/product.json
# 默认直连官方 Seedance；API Key 不要写入 plan JSON：
ARK_API_KEY=your-ark-key \
video-skill render examples/product.json --output-dir ./video-output

# 如需使用兼容网关，显式选择 gateway：
VIDEO_SKILL_BASE_URL=https://your-gateway.example \
VIDEO_SKILL_API_KEY=your-key \
video-skill render examples/product.json --provider gateway --output-dir ./video-output
```

`build-prompt` 只执行本地计划校验和 Prompt 构建，不会创建云端视频任务。
`render` 会创建一个真实任务并轮询到成片，请确认模型账号和素材授权后再运行。

### 使用前提与边界

- Python `>=3.10`；安装命令会注册 `video-skill` CLI。
- `references[].url` 必须是模型服务能够访问的 HTTP(S) 图片地址；本地路径、未授权资源和需要登录的地址不能直接使用。
- 官方 provider 需要火山方舟账号、可用的 Seedance 模型权限和有效 API Key；模型 ID 是否对你的账号开放，以方舟控制台为准。
- 当前核心契约固定为 15 秒、`generate_audio=true`，画幅使用计划中的支持值；不满足时会在发起请求前失败。
- `render` 会把 MP4 下载到 `--output-dir`，当前 CLI 不包含对象存储、视频转码、工作区登记或自动发布。需要这些能力时，实现 `ArtifactStore` / `DeliverySink` 适配器。
- 仓库测试使用模拟 HTTP 响应验证请求、轮询和下载逻辑；真实账号、额度、素材可访问性和平台审核仍需在你的环境中做一次小样本验收。

建议先执行 `validate` 和 `build-prompt`，确认计划与素材顺序，再用一条低成本样例调用 `render`。

### Provider 配置

`seedance` 是默认 provider，直连火山方舟任务接口：

- `ARK_API_KEY`：必填；也兼容 `VOLCENGINE_API_KEY`
- `SEEDANCE_BASE_URL`：可选，覆盖完整任务地址，默认 `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks`
- `SEEDANCE_MODEL`：可选，覆盖模型 ID，默认 `doubao-seedance-2-5-260628`

`gateway` 只在显式选择时启用：`VIDEO_SKILL_BASE_URL`、`VIDEO_SKILL_API_KEY` 和可选的 `VIDEO_SKILL_MODEL`。

两种 provider 互不回退。官方 API 缺少 `ARK_API_KEY` 时会直接返回配置错误，不会偷偷改走网关。

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

当前版本是 `0.2.0` 的可运行核心，默认可用官方 Seedance API，也支持兼容网关。用户仍需自行处理模型账号、版权和平台规则。

## License

Apache-2.0
