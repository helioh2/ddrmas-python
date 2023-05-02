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
    children: set[Argument] = field(default_factory=set)
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

    def is_fallacious(self) -> bool:
        return self.conclusion.fallacious
    
    def direct_external_subargs(self) -> set[Argument]:

        dex_subargs = []
        for subarg in self.children:
            if subarg.definer == self.definer:
                dex_subargs += subarg.direct_external_subargs()
            else:
                dex_subargs.append(subarg)
        
        return dex_subargs
                
    def update_strength(self):
        
        dex_subargs = self.direct_external_subargs()

        if not dex_subargs:
            self.strength = 1
            return self.strength
        
        else:
            sum_ = 0
            for subarg in dex_subargs:
                ilstrength = subarg.conclusion.label.strength(self.definer)
                sum_ += ilstrength * subarg.update_strength()

            self.strength = sum_ / len(dex_subargs)

            return self.strength

    def attacks(self, arg: Argument) -> bool:
        return self.conclusion.label.negated() == arg.conclusion.label

    def defeats(self, arg: Argument) -> bool:
        return self.attacks(arg) and self.strength >= arg.strength
    
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
            str_ += str(child.name) + ", "
        
        if not self.children:
            str_ += "T"

        str_ += "]"
        str_ += ")\n" 

        for arg in self.children:
            str_ += str(arg)

        return str_ 

    def __hash__(self) -> int:
        return hash(self.id)