from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from .viewer import ViewerWidget
from .module_host import ModuleHost
from .panels.params_panel import ParamPanel


class MainWindow(QtWidgets.QMainWindow):
    """Main frame hosting a central 3D viewer and a parameters dock."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Physics & Math Explorer — MVP")
        self.resize(1200, 800)

        # Central viewer
        self.viewer = ViewerWidget(parent=self)
        self.setCentralWidget(self.viewer)

        # Left dock: dynamic parameter panel
        self.param_panel = ParamPanel(parent=self)
        self.param_dock = QtWidgets.QDockWidget("Parameters", self)
        self.param_dock.setObjectName("dock.parameters")
        self.param_dock.setWidget(self.param_panel)
        self.param_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.param_dock)

        # Module host (presenter/controller)
        self.host = ModuleHost(viewer=self.viewer, param_panel=self.param_panel, parent=self)

        # Menus
        self._build_menu()

        # Activate the demo module on startup
        self.host.activate_module("linear_transform_2d")

    # ------------------------- UI plumbing -------------------------
    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        act_quit = file_menu.addAction("E&xit")
        act_quit.triggered.connect(self.close)

        view_menu = menubar.addMenu("&View")
        act_reset_cam = view_menu.addAction("Reset Camera")
        act_reset_cam.triggered.connect(self.viewer.reset_camera)
        act_toggle_grid = view_menu.addAction("Toggle Grid")
        act_toggle_grid.setCheckable(True)
        act_toggle_grid.setChecked(True)
        act_toggle_grid.toggled.connect(self.viewer.set_grid_visible)
        act_toggle_axes = view_menu.addAction("Toggle Axes")
        act_toggle_axes.setCheckable(True)
        act_toggle_axes.setChecked(True)
        act_toggle_axes.toggled.connect(self.viewer.set_axes_visible)

        help_menu = menubar.addMenu("&Help")
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self._show_about)

    def _show_about(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "Physics & Math Explorer\nPySide6 + PyVista MVP with a Linear Transform module."
        )
