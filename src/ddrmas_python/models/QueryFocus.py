
from dataclasses import dataclass, field
from ddrmas_python.models.Agent import Agent

from ddrmas_python.models.LLiteral import LLiteral
from ddrmas_python.models.Rule import Rule


@dataclass
class QueryFocus:
    """ Representas a query focus"""

    name: str
    literal: LLiteral
    emitter_agent: Agent
    kb: set[Rule] = field(default_factory=set)

