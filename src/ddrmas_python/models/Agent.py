from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from ddrmas_python.models.ArgNodeLabel import ArgNodeLabel
from ddrmas_python.models.Argument import ArgType, Argument, TLabel
from ddrmas_python.models.Answer import Answer, TruthValue
from ddrmas_python.models.LLiteral import LLiteral
from ddrmas_python.models.QueryFocus import QueryFocus

from ddrmas_python.models.Rule import Rule, RuleType

if TYPE_CHECKING:
    from ddrmas_python.models.System import System


@dataclass
class Agent:
    """
    Represents an agent in DDRMAS
    """

    name: str
    system: System
    kb: set[Rule] = field(default_factory=set)
    trust: dict[Agent, float] = field(default_factory=dict)
    extended_kbs: dict[str, set[Rule]] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.name)

    async def query(
        self, p: LLiteral, focus: QueryFocus, hist: list[LLiteral]
    ) -> Answer:
        args_p = set()
        args_not_p = set()

        if focus.name not in self.extended_kbs.keys():
            extended_kb = self.create_new_extended_kb(focus)
        else:
            extended_kb = self.extended_kbs[focus.name]

        rlits = self.find_similar_lliterals(p, extended_kb)

        print("CHEGUEI AQUI ANTES DO RETORNO SEM RLITS")

        if not rlits:
            return Answer(p, focus, TruthValue.FALSE)

        args_p = self.create_fallacious_arguments(hist, rlits)

        (
            tv_p_strict,
            args_p_strict,
            args_not_p_strict,
            has_strict_answer,
        ) = await self.find_local_answers(extended_kb, rlits)

        tv_p = tv_p_strict

        print("CHEGUEI AQUI (APÓS STRICT FINDING)")
        # for p1 in rlits:
        #     args_p1 = self.find_defeasible_args(p1, extended_kb, focus, hist)
        #     args_not_p1 = self.find_defeasible_args(p1.negated(), extended_kb, focus, hist)

        # TODO continuaçao


    async def find_local_answers(self, extended_kb, rlits):
        tv_p = False
        args_p = set()
        args_not_p = set()
        rlits_negated = [p1.negated() for p1 in rlits]
        has_strict_answer = {p1: False for p1 in rlits + rlits_negated}

        for p1 in rlits:
            local_answer_p1 = await self.local_ans(p1, extended_kb)
            if local_answer_p1["tv"]:
                args_p.add(local_answer_p1["arg"])
                tv_p = True
                has_strict_answer[p1] = True
                continue

            local_answer_not_p1 = await self.local_ans(p1.negated(), extended_kb)
            if local_answer_not_p1["tv"]:
                args_not_p.add(local_answer_not_p1["arg"])
                # Se uma resposta estrita True já tiver sido encontrada, ela será usada no final
                tv_p = tv_p or False
                has_strict_answer[p1.negated()] = True
                continue

        return tv_p, args_p, args_not_p, has_strict_answer


    async def local_ans(self, p1: LLiteral, extended_kb: set[Rule]) -> dict:
        async def build_subarguments_based_on_rule(rule: Rule):
            subarguments = set()
            for q in rule.body:
                ans = await self.local_ans(q, extended_kb)
                if not ans["tv"]:
                    return None  # se um dos membros do corpo não puder ser ativado, não é possível ativar a regra
                subarguments.add(ans["arg"])

            return subarguments

        strict_rules_for_p1 = {
            rule
            for rule in extended_kb
            if rule.head == p1 and rule.type == RuleType.STRICT
        }

        for rule in strict_rules_for_p1:
            arg = Argument.build(ArgNodeLabel(p1)).being_strict()
            if not rule.body:
                arg = arg.with_T_child()
            else:
                subarguments = await build_subarguments_based_on_rule(rule)
                if (
                    subarguments is None
                ):  # quando não é possível construir os subargumentos com base na regra
                    continue
                arg.children.update(subarguments)

            return {
                "tv": True,
                "arg": arg,
            }  # a primeira regra a partir da qual um argumento pode ser gerado é usado.

        # else
        return {"tv": False, "arg": None}

    def create_fallacious_arguments(self, hist: list[LLiteral], rlits: list[LLiteral]):
        args_p = []
        for i, p1 in enumerate(rlits):
            if not {p1, p1.negated()}.isdisjoint(hist):
                fall_arg_p1 = Argument(ArgNodeLabel(p1, fallacious=True))
                args_p.append(fall_arg_p1)
                rlits.pop(i)

        return args_p

    def find_similar_lliterals(self, p: LLiteral, extended_kb: set[Rule]):
        rlits = []
        for rule in extended_kb:
            if self.system.similar_enough(rule.head, p):
                rlits.append(rule.head)

        return rlits

    def create_new_extended_kb(self, focus):
        localized_focus_kb = set(rule.localize(self) for rule in focus.kb)
        extended_kb = self.kb.union(localized_focus_kb)
        self.extended_kbs[focus.name] = extended_kb
        return extended_kb
