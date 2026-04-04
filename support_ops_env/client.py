from __future__ import annotations

from typing import Any

from support_ops_env.models import SupportOpsAction, SupportOpsObservation, SupportOpsState
from support_ops_env.openenv_compat import EnvClient
from support_ops_env.server.support_ops_environment import SupportOpsEnvironment


class SupportOpsEnv(EnvClient[SupportOpsAction, SupportOpsObservation, SupportOpsState]):
    """Typed client for the support operations environment."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(environment_factory=SupportOpsEnvironment, **kwargs)
