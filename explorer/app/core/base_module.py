from __future__ import annotations
from typing import Protocol, Sequence
from .types import ParamSpec


class ViewerFacade(Protocol):
    """Minimal surface area the modules rely on (for testability)."""

    def render(self) -> None: ...
    def clear(self) -> None: ...


class BaseModule:
    """Abstract module interface for plug-in visualizations."""

    def meta(self) -> dict:
        """Return id, name, category, description."""
        raise NotImplementedError

    def param_schema(self) -> Sequence[ParamSpec]:
        """Return a list describing controls for this module."""
        raise NotImplementedError

    def setup(self, viewer: ViewerFacade) -> None:
        """Create actors in the viewer. Called once when activated."""
        raise NotImplementedError

    def update(self, params: dict) -> None:
        """Apply parameter changes without recreating actors."""
        raise NotImplementedError

    def teardown(self) -> None:
        """Clean up references (if any)."""
        pass
