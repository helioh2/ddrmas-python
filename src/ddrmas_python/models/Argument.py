from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from uuid import UUID, uuid4
from ddrmas_python.models.ArgNodeLabel import ArgNodeLabel


class TLabel(Enum):
    T = 1

    def __str__(self) -> str:
        return "T"

class ArgType(Enum):
    STRICT = 1
    DEFEASIBLE = 2


@dataclass
class Argument:

    conclusion: ArgNodeLabel
    id: UUID = field(default_factory=uuid4)
    children: set[Argument|TLabel] = field(default_factory=set)
    type: ArgType = ArgType.DEFEASIBLE
    supp_by_justified: bool = False
    justified: bool = False
    rejected: bool = False
    strength: float = 0

        
    @staticmethod
    def build(conclusion: ArgNodeLabel) -> Argument:
        arg = Argument(conclusion)
        return arg

    def being_strict(self) -> Argument:
        self.type = ArgType.STRICT
        return self

    def with_T_child(self) -> Argument:
        self.children.add(TLabel.T)
        return self

    def is_fallacious(self) -> bool:
        return self.conclusion.fallacious
    

    def update_strength(self):
        pass


    def __hash__(self) -> int:
        return hash(self.id)
    
    @property
    def definer(self):
        return self.conclusion.label.definer

    @property
    def name(self):
        return str(self.definer)[0].upper() + "_" + str(self.id)

    def __str__(self) -> str:
        str_ = self.name
        str_ += ":\n"
        str_ += "\t ("

        str_ += str(self.conclusion) 
        str_ +=  " <- ["

        for child in self.children:
            if isinstance(child, Argument):
                str_ += str(child.name) + ", "
            else:
                str_ += str(child) + ", "

        str_ += "]"
        str_ += ")\n" 

        for arg in self.children:
            str_ += str(arg)

        return str_ 
