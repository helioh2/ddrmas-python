

from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass, field
import enum
if TYPE_CHECKING:
    from ddrmas_python.models.Agent import Agent

from ddrmas_python.models.LLiteral import LLiteral


class RuleType(enum.Enum):
    STRICT = "<-"
    DEFEASIBLE = "<="


@dataclass
class Rule:
    """Represents a generic rule"""
    
    name: str
    head: LLiteral
    body: list[LLiteral] = field(default_factory=list)
    type: RuleType = RuleType.DEFEASIBLE
    
    
    def localize(self, agent: Agent) -> Rule:
        localized_head = self.head.localize(agent)
        localized_body = [b.localize(agent) for b in self.body]
        localized_name = self.name + "_" + agent.name
        return Rule(localized_name, localized_head, localized_body)
    
    def __str__(self) -> str:
        str_ = self.name + ": "
        str_ += str(self.head)
        str_ += " "+ self.type.value+" "
        str_ += ", ".join(str(bm) for bm in self.body) 
        return str_
    
    def __hash__(self) -> int:
        return hash(self.name)