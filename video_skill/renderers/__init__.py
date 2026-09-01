"""Optional renderer integrations."""

from .gateway import GatewayRenderer, GatewayRendererError
from .seedance_official import SeedanceOfficialRenderer, SeedanceOfficialRendererError

SeedanceRenderer = SeedanceOfficialRenderer
SeedanceRendererError = SeedanceOfficialRendererError

__all__ = [
    "GatewayRenderer",
    "GatewayRendererError",
    "SeedanceOfficialRenderer",
    "SeedanceOfficialRendererError",
    "SeedanceRenderer",
    "SeedanceRendererError",
]
