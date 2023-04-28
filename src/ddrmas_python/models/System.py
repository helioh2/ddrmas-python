
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from ddrmas_python.models.Agent import Agent
from ddrmas_python.models.QueryFocus import QueryFocus
from ddrmas_python.models.LLiteral import LLiteral

@dataclass
class System():
    """
    Class that representas a DDRMAS system
    """
    name: str = "default"
    agents: list[Agent] = field(default_factory=list)
    query_focuses: list[QueryFocus] = field(default_factory=list)
    sim_function: Callable[[LLiteral, LLiteral], float] = lambda p, q: 1. if p == q else 0.
    sim_threshold: float = 1.

    def add_agent(self, agent: Agent):
        self.agents.append(agent)

    def remove_agent(self, agent: Agent):
        self.agents.remove(agent)

    def similar_enough(self, p:LLiteral, q:LLiteral) -> bool:
        return self.sim_function(p, q) >= self.sim_threshold
    