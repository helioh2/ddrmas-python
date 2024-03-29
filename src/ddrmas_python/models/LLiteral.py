

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

    def __str__(self) -> str:
        return "@" if self.value == 1 else "F"

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
    
    def equivalent_to(self, lliteral: LLiteral, sim_function: function, sim_threshold: float) -> bool:
        return (sim_function(self.literal, lliteral.literal) >= sim_threshold and 
                (self.definer == lliteral.definer or Sign.SCHEMATIC in (self.definer, lliteral.definer)))


    def has_equivalent_positive_literal(self, lliteral: LLiteral, sim_function: function, sim_threshold: float) -> bool:
        return (sim_function(self.literal.as_positive(), lliteral.literal.as_positive()) >= sim_threshold and 
                (self.definer == lliteral.definer or Sign.SCHEMATIC in (self.definer, lliteral.definer)))

    def __hash__(self) -> int:
        return hash(str(self))
    
    def __str__(self) -> str:
        return f"({str(self.definer)}, {self.literal})" 
    
    def __repr__(self) -> str:
        return str(self)
    
    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)
    
    def strength(self, agent: Agent) -> float:
        return 1.

