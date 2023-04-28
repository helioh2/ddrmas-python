

from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass, field
import enum
if TYPE_CHECKING:
    from ddrmas_python.models.Agent import Agent

from ddrmas_python.models.LLiteral import LLiteral


class RuleType(enum.Enum):
    STRICT = 1
    DEFEASIBLE = 2


@dataclass
class Rule:
    """Represents a generic rule"""

    head: LLiteral
    body: list[LLiteral] = field(default_factory=list)
    type: RuleType = RuleType.DEFEASIBLE
    
    def __hash__(self) -> int:
        ## TODO: fazer a representaçao str e repr
        return hash("".join([str(self.head)]+[str(b) for b in self.body]))

    def localize(self, agent: Agent) -> Rule:
        localized_head = self.head.localize(agent)
        localized_body = [b.localize(agent) for b in self.body]
        return Rule(localized_head, localized_body)
    