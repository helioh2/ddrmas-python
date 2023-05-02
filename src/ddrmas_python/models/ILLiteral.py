from __future__ import annotations
from dataclasses import dataclass
import enum
import typing
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ddrmas_python.models.Agent import Agent
from ddrmas_python.models.LLiteral import LLiteral



@dataclass
class ILLiteral(LLiteral):

    similarity: float

    def strength(self, agent: Agent) -> float:
        return agent.trust[self.definer] * self.similarity

    def __str__(self) -> str:
        return f"<{str(self.definer)}, {self.literal}, {self.similarity}>" 