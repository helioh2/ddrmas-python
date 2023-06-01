
from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass, field
if TYPE_CHECKING:
    from ddrmas_python.models.Agent import Agent

from ddrmas_python.models.LLiteral import LLiteral
from ddrmas_python.models.Rule import Rule


@dataclass
class QueryFocus:
    """ Representas a query focus"""

    name: str
    literal: LLiteral
    emitter_agent: Agent
    kb: set[Rule] = field(default_factory=set)

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        res = self.name + ": " + str(self.literal) + " by " + str(self.emitter_agent)
        res += " with focus rules: \n"
        for rule in self.kb:
            res += str(rule) + "\n"

        return res
    
    def __repr__(self) -> str:
        return str(self)