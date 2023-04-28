

from __future__ import annotations
from dataclasses import dataclass, field

from ddrmas_python.models.Rule import Rule



@dataclass
class Agent:
    """
    Represents an agent in DDRMAS
    """
    name: str
    kb: set[Rule] = field(default_factory=set)
    trust: dict[Agent, float] = field(default_factory=dict)


    def __hash__(self) -> int:
        return hash(self.name)