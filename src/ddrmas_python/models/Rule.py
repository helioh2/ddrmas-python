

from dataclasses import dataclass, field
import enum

from ddrmas_python.models.LLiteral import LLiteral


class RuleType(enum.Enum):
    STRICT = 1
    DEFEASIBLE = 2


@dataclass
class Rule:
    """Represents a generic rule"""

    head: LLiteral
    type: RuleType
    body: list[LLiteral] = field(default_factory=list)
    
    def __hash__(self) -> int:
        ## TODO: fazer a representaçao str e repr
        return hash("".join([str(self.head)]+[str(b) for b in self.body]))


    