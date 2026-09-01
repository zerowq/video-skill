# Adapter Contract

The core package must not import a provider SDK, web framework, queue client, object-storage SDK, or Agent host implementation.

Implement these boundaries for a production integration:

```python
class Renderer(Protocol):
    def create(self, request: RenderRequest) -> TaskHandle: ...
    def wait(self, task: TaskHandle) -> RenderedVideo: ...

class ArtifactStore(Protocol):
    def put(self, path: Path) -> StoredArtifact: ...

class DeliverySink(Protocol):
    def publish(self, artifact: StoredArtifact) -> PublishedArtifact: ...
```

An adapter owns provider authentication, provider field mapping, retries, polling intervals, and provider errors. The core owns plan validation, reference ordering, prompt construction, and the decision not to submit invalid requests.

An adapter should expose a deterministic dry-run mode and never log credentials or private user asset URLs. If the host has SSE, workspace cards, or a conversation context, translate the published artifact at the host boundary instead of importing those concepts into `video_skill`.

## Seedance renderer

`video_skill.renderers.SeedanceRenderer` targets a configurable Seedance task API:

```text
POST ${SEEDANCE_BASE_URL}
GET  ${SEEDANCE_BASE_URL}/{task_id}
```

Set `SEEDANCE_BASE_URL` to the complete task creation endpoint and `SEEDANCE_API_KEY` for Bearer authentication. `SEEDANCE_MODEL` may override the model ID. The adapter sends one task, polls that same task, and downloads the final MP4 atomically. Missing credentials are a hard configuration error; there is no gateway fallback.

## Compatible gateway renderer

`video_skill.renderers.GatewayRenderer` targets a gateway exposing:

```text
POST /v1/videos/generations
GET  /v1/videos/generations/{task_id}
```

Set `VIDEO_SKILL_BASE_URL` and optionally `VIDEO_SKILL_API_KEY`. The renderer sends a
single text item followed by ordered `reference_image` items, passes the stable
idempotency key in request headers, polls the original task, and downloads the final
MP4 atomically into `output_dir`. It does not retry by creating a second task.

`video_skill.renderers.seedance.SeedanceRenderer` is the configurable Seedance
adapter. New code can import it or `GatewayRenderer` explicitly.
