

from __future__ import annotations
from dataclasses import dataclass
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ddrmas_python.models.Agent import Agent

from ddrmas_python.models.Literal import Literal

class Sign(enum.Enum):
    SCHEMATIC = 1
    FOCUS = 2

@dataclass
class LLiteral:
    """ Represents a generic l-literal"""

    definer: Agent|Sign
    literal: Literal

    def negated(self) -> LLiteral:
        return LLiteral(self.definer, self.literal.negated())
    

    def localize(self, agent) -> LLiteral:
        if self.definer == Sign.FOCUS:
            return LLiteral(agent, self.literal)
        return self