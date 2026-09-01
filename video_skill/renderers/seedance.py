"""Legacy import path for the former Seedance-compatible gateway adapter.

Use :class:`SeedanceOfficialRenderer` for the official Ark API or
:class:`GatewayRenderer` for a compatible gateway in new code.
"""

from .gateway import DEFAULT_BASE_URL, DEFAULT_MODEL, GatewayRenderer, GatewayRendererError
from .seedance_official import DEFAULT_TASKS_URL, SeedanceOfficialRenderer, SeedanceOfficialRendererError

# Preserve the v0.1 gateway behavior for existing imports.
SeedanceRenderer = GatewayRenderer
SeedanceRendererError = GatewayRendererError

__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_BASE_URL",
    "DEFAULT_TASKS_URL",
    "GatewayRenderer",
    "GatewayRendererError",
    "SeedanceOfficialRenderer",
    "SeedanceOfficialRendererError",
    "SeedanceRenderer",
    "SeedanceRendererError",
]
