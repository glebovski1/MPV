from __future__ import annotations
from typing import Optional
from PySide6 import QtWidgets
from pyvistaqt import QtInteractor
import pyvista as pv


class ViewerWidget(QtWidgets.QWidget):
    """Thin facade around a single PyVista plotter embedded in Qt."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter)

        # Default scene decorations
        self._axes = self.plotter.add_axes()
        self._grid_shown = True
        self._axes_shown = True
        self.plotter.set_background("white")
        self.plotter.show_grid()

    # --------------------- Facade helpers ---------------------
    def render(self) -> None:
        self.plotter.update()  # triggers a redraw

    def reset_camera(self) -> None:
        self.plotter.reset_camera()
        self.render()

    def clear(self) -> None:
        self.plotter.clear()
        if self._grid_shown:
            self.plotter.show_grid()
        if self._axes_shown:
            self._axes = self.plotter.add_axes()
        self.render()

    def set_grid_visible(self, visible: bool) -> None:
        self._grid_shown = visible
        if visible:
            self.plotter.show_grid()
        else:
            self.plotter.remove_bounds_axes()
        self.render()

    def set_axes_visible(self, visible: bool) -> None:
        self._axes_shown = visible
        # there is no direct on/off; re-add or clear them
        if visible and self._axes is None:
            self._axes = self.plotter.add_axes()
        elif not visible and self._axes is not None:
            try:
                self.plotter.remove_actor(self._axes)
            except Exception:
                pass
            self._axes = None
        self.render()
