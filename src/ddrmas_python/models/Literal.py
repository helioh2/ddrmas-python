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
    
    def __eq__(self, __value: object) -> bool:
        return self.positive == __value.positive and self.pred == __value.pred