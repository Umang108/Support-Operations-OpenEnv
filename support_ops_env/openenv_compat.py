"""Compatibility layer so the project can run with or without openenv-core installed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar

from fastapi import Body, FastAPI
from pydantic import BaseModel

ActionT = TypeVar("ActionT", bound=BaseModel)
ObservationT = TypeVar("ObservationT", bound=BaseModel)
StateT = TypeVar("StateT", bound=BaseModel)


try:
    from openenv import Action, EnvClient, Observation, State, StepResult  # type: ignore
    from openenv.core.env_server import create_app  # type: ignore
except ImportError:  # pragma: no cover
    class Action(BaseModel):
        """Fallback action model."""

    class Observation(BaseModel):
        """Fallback observation model."""

    class State(BaseModel):
        """Fallback state model."""

    @dataclass
    class StepResult(Generic[ObservationT]):
        observation: ObservationT
        reward: float
        done: bool
        info: dict[str, Any]

    class EnvClient(Generic[ActionT, ObservationT, StateT]):
        """Tiny fallback client used for local direct execution."""

        def __init__(self, environment_factory: Callable[[], Any] | None = None, **_: Any) -> None:
            if environment_factory is None:
                raise ValueError("Fallback EnvClient requires an environment_factory.")
            self._env = environment_factory()

        def reset(self, **kwargs: Any) -> StepResult[ObservationT]:
            observation = self._env.reset(**kwargs)
            return StepResult(observation=observation, reward=0.0, done=False, info={"source": "local"})

        def step(self, action: ActionT) -> StepResult[ObservationT]:
            return self._env.step(action)

        def state(self) -> StateT:
            return self._env.state()

        def close(self) -> None:
            return None

    def create_app(
        env: Any,
        action_model: type[BaseModel],
        observation_model: Optional[type[BaseModel]] = None,
        state_model: Optional[type[BaseModel]] = None,
    ) -> FastAPI:
        """Minimal HTTP app that mirrors reset/step/state for local development."""

        app = FastAPI(title="Support Ops Env")

        @app.get("/health")
        def health() -> dict[str, str]:
            return {"status": "ok"}

        @app.post("/reset")
        def reset(payload: dict[str, Any] | None = None) -> dict[str, Any]:
            observation = env.reset(**(payload or {}))
            return {"observation": observation.model_dump()}

        @app.post("/step")
        def step(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
            action = action_model.model_validate(payload)
            result = env.step(action)
            return {
                "observation": result.observation.model_dump(),
                "reward": result.reward,
                "done": result.done,
                "info": result.info,
            }

        @app.get("/state")
        def state() -> dict[str, Any]:
            return env.state().model_dump()

        return app
