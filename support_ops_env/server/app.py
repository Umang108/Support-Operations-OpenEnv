from __future__ import annotations

from support_ops_env.models import SupportOpsAction, SupportOpsObservation, SupportOpsState
from support_ops_env.openenv_compat import create_app
from support_ops_env.server.support_ops_environment import SupportOpsEnvironment

environment = SupportOpsEnvironment()
app = create_app(environment, SupportOpsAction, SupportOpsObservation, SupportOpsState)
