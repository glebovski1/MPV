from __future__ import annotations
import math
from typing import List, Tuple
import numpy as np
import pyvista as pv
from app.core.base_module import BaseModule, ViewerFacade
from app.core.types import ParamSpec


def _polyline(points: np.ndarray) -> pv.PolyData:
    """Create a single polyline from Nx3 points."""
    n = points.shape[0]
    poly = pv.PolyData()
    poly.points = points
    cells = np.hstack([[n], np.arange(n, dtype=np.int64)])
    poly.lines = cells
    return poly


def _unit_circle(n: int = 128) -> np.ndarray:
    th = np.linspace(0.0, 2 * math.pi, n, endpoint=True)
    pts = np.c_[np.cos(th), np.sin(th), np.zeros_like(th)]
    return pts


def _grid_lines(n: int = 10, extent: float = 1.0) -> List[np.ndarray]:
    """Return list of polylines (each as Nx3) for a square grid in [-extent, extent]^2."""
    xs = np.linspace(-extent, extent, n)
    ys = np.linspace(-extent, extent, n)
    lines: List[np.ndarray] = []
    for x in xs:
        yline = np.column_stack([np.full_like(ys, x), ys, np.zeros_like(ys)])
        lines.append(yline)
    for y in ys:
        xline = np.column_stack([xs, np.full_like(xs, y), np.zeros_like(xs)])
        lines.append(xline)
    return lines


class LinearTransform2DModule(BaseModule):
    """Visualize a 2×2 linear map acting on the unit circle and a square grid.

    Parameters:
      - A (matrix2x2): the transform matrix
      - grid_n (int): number of grid lines per direction
      - animate_t (float): 0..1 interpolation I→A
      - show_eigen (bool): draw real eigenvectors if available
    """

    def __init__(self) -> None:
        self.viewer: ViewerFacade | None = None
        self._actors: dict[str, pv.Actor] = {}
        self._geoms_base: dict[str, List[np.ndarray] | np.ndarray] = {}

    # --------------------- Boilerplate ---------------------
    def meta(self) -> dict:
        return {
            "id": "linear_transform_2d",
            "name": "Linear Transform (2D)",
            "category": "Linear Algebra",
            "description": "Map unit circle and grid through a 2×2 matrix; show eigenvectors.",
        }

    def param_schema(self):
        return [
            ParamSpec(name="A", kind="matrix2x2", default=[[1, 0], [0, 1]], min=-5.0, max=5.0, step=0.1, label="Matrix A"),
            ParamSpec(name="grid_n", kind="int", default=10, min=4, max=40, step=1, label="Grid lines"),
            ParamSpec(name="animate_t", kind="float", default=1.0, min=0.0, max=1.0, step=0.01, label="Interpolate t"),
            ParamSpec(name="show_eigen", kind="bool", default=True, label="Show eigenvectors"),
        ]

    # --------------------- Lifecycle ---------------------
    def setup(self, viewer: ViewerFacade) -> None:
        self.viewer = viewer
        plotter = viewer.plotter  # type: ignore[attr-defined]
        plotter.show_grid()

        # Base (untransformed) geometry cached for fast updates
        circle = _unit_circle(128)
        grid = _grid_lines(n=10, extent=1.0)
        self._geoms_base["circle"] = circle
        self._geoms_base["grid"] = grid

        # Create actors once
        circle_poly = _polyline(circle)
        self._actors["circle"] = plotter.add_mesh(circle_poly, color="black", line_width=2)

        self._actors["grid"] = []  # type: ignore[assignment]
        grid_actors: List[pv.Actor] = []
        for ln in grid:
            poly = _polyline(ln)
            act = plotter.add_mesh(poly, color="#999999", line_width=1)
            grid_actors.append(act)
        self._actors["grid"] = grid_actors  # type: ignore[assignment]

        # Eigenvector placeholders
        self._actors["eig1"] = None  # type: ignore[assignment]
        self._actors["eig2"] = None  # type: ignore[assignment]

    def update(self, params: dict) -> None:
        if not self.viewer:
            return
        plotter = self.viewer.plotter  # type: ignore[attr-defined]

        A = np.array(params.get("A", [[1, 0], [0, 1]]), dtype=float)
        t = float(params.get("animate_t", 1.0))
        grid_n = int(params.get("grid_n", 10))
        show_eigen = bool(params.get("show_eigen", True))

        # Rebuild grid base if density changed
        if isinstance(self._geoms_base.get("grid"), list) and len(self._geoms_base["grid"]) != 2 * grid_n:
            self._rebuild_grid(grid_n)

        # Interpolated transform A_t = (1-t) I + t A
        At = (1.0 - t) * np.eye(2) + t * A

        # Update circle
        circle_base: np.ndarray = self._geoms_base["circle"]  # (N, 3)
        circ_xy = circle_base[:, :2] @ At.T
        circ = np.column_stack([circ_xy, np.zeros(circ_xy.shape[0])])
        # mutate the underlying polydata points
        circle_actor: pv.Actor = self._actors["circle"]
        circle_poly: pv.PolyData = circle_actor.GetMapper().GetInputAsDataSet()  # type: ignore
        circle_poly.points = circ

        # Update grid
        for ln_base, act in zip(self._geoms_base["grid"], self._actors["grid"]):  # type: ignore[index]
            ln_xy = ln_base[:, :2] @ At.T
            ln = np.column_stack([ln_xy, np.zeros(ln_xy.shape[0])])
            poly: pv.PolyData = act.GetMapper().GetInputAsDataSet()  # type: ignore
            poly.points = ln

        # Eigenvectors (real only)
        self._update_eigenvectors(At, show_eigen)

    def teardown(self) -> None:
        self._actors.clear()
        self._geoms_base.clear()

    # --------------------- Helpers ---------------------
    def _rebuild_grid(self, n: int) -> None:
        plotter = self.viewer.plotter  # type: ignore[attr-defined]
        # Remove old grid actors
        for act in self._actors.get("grid", []):  # type: ignore[assignment]
            try:
                plotter.remove_actor(act)
            except Exception:
                pass
        lines = _grid_lines(n=n, extent=1.0)
        self._geoms_base["grid"] = lines
        grid_actors: List[pv.Actor] = []
        for ln in lines:
            poly = _polyline(ln)
            act = plotter.add_mesh(poly, color="#999999", line_width=1)
            grid_actors.append(act)
        self._actors["grid"] = grid_actors  # type: ignore[assignment]

    def _update_eigenvectors(self, A: np.ndarray, show: bool) -> None:
        plotter = self.viewer.plotter  # type: ignore[attr-defined]
        # Clean existing first
        for key in ("eig1", "eig2"):
            act = self._actors.get(key)
            if act is not None:
                try:
                    plotter.remove_actor(act)  # type: ignore[arg-type]
                except Exception:
                    pass
                self._actors[key] = None
        if not show:
            return

        vals, vecs = np.linalg.eig(A)
        # Draw only real eigenvectors
        drawn = 0
        for i in range(2):
            if abs(vals[i].imag) < 1e-8 and abs(vecs[:, i].imag).max() < 1e-8:
                v = vecs[:, i].real
                v = v / (np.linalg.norm(v) + 1e-9)
                scale = 1.2
                pts = np.array([[0.0, 0.0, 0.0], [scale * v[0], scale * v[1], 0.0]])
                poly = _polyline(pts)
                color = "#d62728" if drawn == 0 else "#1f77b4"
                act = plotter.add_mesh(poly, color=color, line_width=3)
                self._actors["eig1" if drawn == 0 else "eig2"] = act
                drawn += 1
