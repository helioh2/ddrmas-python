from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ddrmas_python.models.LLiteral import LLiteral


@dataclass
class ArgNodeLabel:

    label: LLiteral
    fallacious: bool = False

    def __str__(self) -> str:
        if self.fallacious:
            return str(self.label) + "!"
        return str(self.label)