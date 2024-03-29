from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Literal:
    """ Represents a generic l-literal"""

    positive: bool
    pred: str
    terms: list[str]
    
    def negated(self) -> Literal:
        return Literal(not self.positive, self.pred, self.terms)
    
    def as_positive(self) -> Literal:
        return Literal(True, self.pred, self.terms)

    def __eq__(self, __value: object) -> bool:
        return self.positive == __value.positive and self.pred == __value.pred
    
    def __str__(self) -> str:
        sign = "" if self.positive else "~"
        return f"{sign}{self.pred}{self.terms}"
    
    def __hash__(self) -> int:
        return hash(str(self))
    
    def __repr__(self) -> str:
        return str(self)