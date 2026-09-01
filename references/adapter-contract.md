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
