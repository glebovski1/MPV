from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal, Sequence

ParamKind = Literal["float", "int", "bool", "enum", "matrix2x2"]


@dataclass
class ParamSpec:
    """UI schema for a single parameter.

    - kind: one of ParamKind
    - default: initial value
    - min/max/step: numeric bounds (as applicable)
    - options: for enums
    - label: pretty name for forms
    """

    name: str
    kind: ParamKind
    default: Any
    min: float | int | None = None
    max: float | int | None = None
    step: float | int | None = None
    options: Sequence[str] | None = None
    label: str | None = None
