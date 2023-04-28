from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from ddrmas_python.models.Argument import Argument

from ddrmas_python.models.LLiteral import LLiteral
from ddrmas_python.models.QueryFocus import QueryFocus


class TruthValue(Enum):
    TRUE = 1,
    FALSE = 2,
    UNDECIDED = 3

@dataclass
class Answer:

    p: LLiteral
    query_focus: QueryFocus
    tv_p: TruthValue
    args_p: set[Argument] = field(default_factory=set)
    args_not_p: set[Argument] = field(default_factory=set)