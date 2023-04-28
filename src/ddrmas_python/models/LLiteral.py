

from __future__ import annotations
from dataclasses import dataclass
import enum
import typing

from ddrmas_python.models.Literal import Literal

class Sign(enum.Enum):
    SCHEMATIC = 1
    FOCUS = 2

@dataclass
class LLiteral:
    """ Represents a generic l-literal"""

    definer: typing.Any
    literal: Literal

    def negated(self) -> LLiteral:
        return LLiteral(self.definer, self.literal.negated())