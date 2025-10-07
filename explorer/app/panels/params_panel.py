from __future__ import annotations
from typing import Any, Dict, List, Sequence, Tuple
from PySide6 import QtCore, QtWidgets
from app.core.types import ParamSpec


class ParamPanel(QtWidgets.QWidget):
    """Auto-builds a small form from ParamSpec entries and emits live dict values."""

    paramsChanged = QtCore.Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._schema: List[ParamSpec] = []
        self._widgets: Dict[str, Any] = {}

        self._form = QtWidgets.QFormLayout()
        self._form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.setLayout(self._form)

    # --------------------- Public API ---------------------
    def build_from_schema(self, schema: Sequence[ParamSpec]) -> None:
        # clear
        while self._form.count():
            item = self._form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._widgets.clear()
        self._schema = list(schema)

        for spec in self._schema:
            label = spec.label or spec.name
            if spec.kind in ("float", "int"):
                spin = QtWidgets.QDoubleSpinBox(self) if spec.kind == "float" else QtWidgets.QSpinBox(self)
                if spec.min is not None:
                    spin.setMinimum(spec.min)
                if spec.max is not None:
                    spin.setMaximum(spec.max)
                if spec.step is not None and hasattr(spin, "setSingleStep"):
                    spin.setSingleStep(spec.step)
                # set default
                if spec.kind == "float":
                    spin.setDecimals(4)
                    spin.setValue(float(spec.default))
                else:
                    spin.setValue(int(spec.default))
                spin.valueChanged.connect(self._emit_params)
                self._widgets[spec.name] = spin
                self._form.addRow(label, spin)

            elif spec.kind == "bool":
                cb = QtWidgets.QCheckBox(self)
                cb.setChecked(bool(spec.default))
                cb.toggled.connect(self._emit_params)
                self._widgets[spec.name] = cb
                self._form.addRow(label, cb)

            elif spec.kind == "enum":
                combo = QtWidgets.QComboBox(self)
                combo.addItems(list(spec.options or []))
                if spec.default in (spec.options or []):
                    combo.setCurrentText(str(spec.default))
                combo.currentTextChanged.connect(self._emit_params)
                self._widgets[spec.name] = combo
                self._form.addRow(label, combo)

            elif spec.kind == "matrix2x2":
                grid = QtWidgets.QGridLayout()
                container = QtWidgets.QWidget(self)
                container.setLayout(grid)
                a11 = QtWidgets.QDoubleSpinBox(self); a12 = QtWidgets.QDoubleSpinBox(self)
                a21 = QtWidgets.QDoubleSpinBox(self); a22 = QtWidgets.QDoubleSpinBox(self)
                for sb in (a11, a12, a21, a22):
                    sb.setDecimals(4)
                    sb.setRange(spec.min or -1e6, spec.max or 1e6)
                    sb.setSingleStep(spec.step or 0.1)
                    sb.valueChanged.connect(self._emit_params)
                # defaults
                d = spec.default or [[1, 0], [0, 1]]
                a11.setValue(float(d[0][0])); a12.setValue(float(d[0][1]))
                a21.setValue(float(d[1][0])); a22.setValue(float(d[1][1]))

                grid.addWidget(a11, 0, 0); grid.addWidget(a12, 0, 1)
                grid.addWidget(a21, 1, 0); grid.addWidget(a22, 1, 1)
                self._widgets[spec.name] = (a11, a12, a21, a22)
                self._form.addRow(label, container)

        # initial emit
        self._emit_params()

    def current_params(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        for spec in self._schema:
            w = self._widgets.get(spec.name)
            if spec.kind == "float":
                params[spec.name] = float(w.value())
            elif spec.kind == "int":
                params[spec.name] = int(w.value())
            elif spec.kind == "bool":
                params[spec.name] = bool(w.isChecked())
            elif spec.kind == "enum":
                params[spec.name] = str(w.currentText())
            elif spec.kind == "matrix2x2":
                a11, a12, a21, a22 = w
                params[spec.name] = [[a11.value(), a12.value()], [a21.value(), a22.value()]]
        return params

    # --------------------- Internals ---------------------
    def _emit_params(self) -> None:
        self.paramsChanged.emit(self.current_params())
