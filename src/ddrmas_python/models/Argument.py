from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from ddrmas_python.models.ArgNodeLabel import ArgNodeLabel


class TLabel(Enum):
    T = 1

class ArgType(Enum):
    STRICT = 1
    DEFEASIBLE = 2

@dataclass
class Argument:

    conclusion: ArgNodeLabel
    children: set[Argument|TLabel] = field(default_factory=set)
    type: ArgType = ArgType.DEFEASIBLE
    supp_by_justified: bool = False
    justified: bool = False
    rejected: bool = False
    strength: float = 0


    @staticmethod
    def build(conclusion: ArgNodeLabel) -> Argument:
        return Argument(conclusion)
    
    def being_strict(self) -> Argument:
        self.type = ArgType.STRICT
        return self

    def with_T_child(self) -> Argument:
        self.children.add(TLabel.T)
        return self

    def is_fallacious(self) -> bool:
        return self.conclusion.fallacious
    



