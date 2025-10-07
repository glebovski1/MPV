from __future__ import annotations
from typing import Optional
from PySide6 import QtCore
from .viewer import ViewerWidget
from .panels.params_panel import ParamPanel
from .core.base_module import BaseModule
from .core.types import ParamSpec

# Import built-in modules here (simple registry for MVP)
from .modules.linear_transform_2d.module import LinearTransform2DModule


class ModuleHost(QtCore.QObject):
    """Loads, configures, and updates the active module."""

    def __init__(self, viewer: ViewerWidget, param_panel: ParamPanel, parent=None) -> None:
        super().__init__(parent)
        self.viewer = viewer
        self.param_panel = param_panel
        self._active: Optional[BaseModule] = None
        self._registry = {
            "linear_transform_2d": LinearTransform2DModule,
        }

        self.param_panel.paramsChanged.connect(self._on_params_changed)

    # --------------------- API ---------------------
    def activate_module(self, module_id: str) -> None:
        if self._active is not None:
            try:
                self._active.teardown()
            finally:
                self.viewer.clear()
                self._active = None

        cls = self._registry.get(module_id)
        if not cls:
            raise KeyError(f"Unknown module id: {module_id}")

        self._active = cls()
        self._active.setup(self.viewer)

        schema = list(self._active.param_schema())
        self.param_panel.build_from_schema(schema)

        # Prime the module with current defaults
        self._active.update(self.param_panel.current_params())
        self.viewer.render()

    # --------------------- Slots ---------------------
    @QtCore.Slot(dict)
    def _on_params_changed(self, params: dict) -> None:
        if not self._active:
            return
        self._active.update(params)
        self.viewer.render()
