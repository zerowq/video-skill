"""Host- and provider-neutral adapter protocols.

Concrete integrations should implement these protocols without importing their
SDKs into the core package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RenderRequest:
    prompt: str
    references: tuple[str, ...]
    aspect_ratio: str = "16:9"
    duration_seconds: int = 15
    generate_audio: bool = True
    idempotency_key: str = ""


@dataclass(frozen=True)
class TaskHandle:
    task_id: str


@dataclass(frozen=True)
class RenderedVideo:
    path: Path
    task_id: str
    duration_seconds: int = 15


@dataclass(frozen=True)
class StoredArtifact:
    uri: str
    path: Path


@dataclass(frozen=True)
class PublishedArtifact:
    uri: str
    title: str = "视频成片"


class Renderer(Protocol):
    def create(self, request: RenderRequest) -> TaskHandle:
        """Create one provider task for one validated request."""

    def wait(self, task: TaskHandle) -> RenderedVideo:
        """Wait for the original task and return a playable local file."""


class ArtifactStore(Protocol):
    def put(self, path: Path) -> StoredArtifact:
        """Persist a validated video and return a stable URI."""


class DeliverySink(Protocol):
    def publish(self, artifact: StoredArtifact) -> PublishedArtifact:
        """Expose the artifact to the host application."""


__all__ = [
    "ArtifactStore",
    "DeliverySink",
    "PublishedArtifact",
    "RenderRequest",
    "RenderedVideo",
    "Renderer",
    "StoredArtifact",
    "TaskHandle",
]
