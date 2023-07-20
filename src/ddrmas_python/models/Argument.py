from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from uuid import UUID, uuid4
from ddrmas_python.models import LLiteral
from ddrmas_python.models.ArgNodeLabel import ArgNodeLabel
import functools


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
        return (self.conclusion.fallacious 
            or any(subarg.is_fallacious() for subarg in self.proper_subargs()))

    # @functools.cache
    def proper_subargs(self) -> set[Argument]:
        """
        TODO: pensar em colocar subargs numa cache (lista) para rápido acesso
        """
        subargs = set()

        for subarg in self.children:
            subargs.add(subarg)
            subargs.update(subarg.proper_subargs())
        
        return subargs

    def direct_external_subargs(self) -> set[Argument]:

        dex_subargs = set()
        for subarg in self.children:
            if subarg.definer == self.definer:
                dex_subargs.update(subarg.direct_external_subargs())
            else:
                dex_subargs.add(subarg)
        
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
                sum_ += ilstrength * subarg.strength

            self.strength = sum_ / len(dex_subargs)

            return self.strength

    def attacks(self, arg: Argument) -> bool:
        return self.conclusion.label.negated() == arg.conclusion.label

    def defeats(self, arg: Argument) -> bool:
        return self.attacks(arg) and self.strength >= arg.strength
    

    def prems(self):
        return [subarg.conclusion for subarg in self.proper_subargs()]

    def size(self) -> int:
        return 1 + len(self.prems())


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
    

    def to_graph(self) -> str:
        res = '"'+self.name+'" [\n'
        res += f'label = "{str(self.conclusion)}"\n'
        res += "];\n"
        
        for child in self.children:
            res += child.to_graph()+"\n"
            res += f'"{self.name}" -> "{child.name}";\n'

        
        return res
        
        

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return hash(self.id)