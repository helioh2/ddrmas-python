from __future__ import annotations
from dataclasses import dataclass
import enum
import typing
from ddrmas_python.models.LLiteral import LLiteral



@dataclass
class ILLiteral(LLiteral):

    similarity: float