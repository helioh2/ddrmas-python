from __future__ import annotations

import asyncio
import itertools

from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from ddrmas_python.models.ArgNodeLabel import ArgNodeLabel
from ddrmas_python.models.Argument import ArgType, Argument, TLabel
from ddrmas_python.models.Answer import Answer, TruthValue
from ddrmas_python.models.ILLiteral import ILLiteral
from ddrmas_python.models.LLiteral import LLiteral, Sign
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
        tv_p = TruthValue.FALSE

        if focus.name not in self.extended_kbs.keys():
            extended_kb = self.create_new_extended_kb(focus)
        else:
            extended_kb = self.extended_kbs[focus.name]

        rlits = self.find_similar_lliterals(p, extended_kb)

        print("CHEGUEI AQUI ANTES DO RETORNO SEM RLITS")

        if not rlits:
            return Answer(p, focus, TruthValue.FALSE)

        args_p = self.create_fallacious_arguments(hist, rlits)

        for p1 in rlits:

            (
                tv_p_strict,
                args_p1_strict,
                args_not_p1_strict,
                has_strict_answer_p1,
            ) = await self.find_local_answers(extended_kb, p1)

            print("CHEGUEI AQUI (APÓS STRICT FINDING)")
            args_p1 = await self.find_defeasible_args(p1, extended_kb, focus, hist)
            args_not_p1 = await self.find_defeasible_args(
                p1.negated(), extended_kb, focus, hist
            )
            
            if has_strict_answer_p1 and not tv_p_strict:
                tv_p = TruthValue.FALSE
                for arg in args_p1:
                    arg.rejected = True

            elif has_strict_answer_p1 and tv_p_strict:
                tv_p = TruthValue.TRUE
                for arg in args_not_p1:
                    arg.rejected = True

            # else:
            #     tv_p1 = self.compare_def_args(args_p1, args_not_p1)
                
            #     if tv_p1 == TruthValue.TRUE:
            #         tv_p = TruthValue.TRUE
            #     elif tv_p1 == TruthValue.UNDECIDED and tv_p != TruthValue.TRUE:
            #         tv_p = TruthValue.UNDECIDED
            
            # args_p = args_p.union(args_p1)
            # args_not_p = args_not_p.union(args_not_p1)


        return Answer(p, focus, tv_p, args_p1, args_not_p1)
    
    def create_new_extended_kb(self, focus):
        localized_focus_kb = set(rule.localize(self) for rule in focus.kb)
        extended_kb = self.kb.union(localized_focus_kb)
        self.extended_kbs[focus.name] = extended_kb
        return extended_kb
    
    def find_similar_lliterals(self, p: LLiteral, extended_kb: set[Rule]):
        rlits = []
        for rule in extended_kb:
            if self.system.similar_enough(rule.head, p):
                rlits.append(rule.head)

        return rlits

    def create_fallacious_arguments(self, hist: list[LLiteral], rlits: list[LLiteral]):
        args_p = []
        for i, p1 in enumerate(rlits):
            if not {p1, p1.negated()}.isdisjoint(hist):
                fall_arg_p1 = Argument(ArgNodeLabel(p1, fallacious=True))
                args_p.append(fall_arg_p1)
                rlits.pop(i)

        return args_p

    async def find_local_answers(self, extended_kb, p1):
        tv_p = False
        args_p = set()
        args_not_p = set()
        has_strict_answer = False

        local_answer_p1 = await self.local_ans(p1, extended_kb)
        if local_answer_p1["tv"]:
            args_p.add(local_answer_p1["arg"])
            tv_p = True
            has_strict_answer = True
            return tv_p, args_p, args_not_p, has_strict_answer

        local_answer_not_p1 = await self.local_ans(p1.negated(), extended_kb)
        if local_answer_not_p1["tv"]:
            args_not_p.add(local_answer_not_p1["arg"])
            has_strict_answer = True

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

    async def find_defeasible_args(
        self,
        p1: LLiteral,
        extended_kb: set[Rule],
        focus: QueryFocus,
        hist: list[LLiteral],
    ):
        async def build_subarguments_based_on_rule(rule: Rule):
            possible_subargs_r = list()
            map_arg_to_q = dict()
            # serve como indice reverso para recordar qual argumento conclui qual q (pois o q se perde quando se usa l-literais similares)

            for q in rule.body:
                args_q = None
                if q.definer == Sign.SCHEMATIC:
                    args_q = await self.query_agents(
                        self.system.agents, q, focus, hist_p1
                    )
                elif isinstance(q.definer, Agent):
                    args_q = await self.query_agents([q.definer], q, focus, hist_p1)
                if not args_q:
                    return None, None  # não foi possível construir args para todos os membros do corpo

                # else
                for arg in args_q:
                    map_arg_to_q[arg] = q

                possible_subargs_r.append(args_q)

            # else
            return possible_subargs_r, map_arg_to_q

        args_p1 = set()
        hist_p1 = hist + [p1]

        rules_with_head_p1 = {rule for rule in extended_kb if rule.head == p1}
        for rule in rules_with_head_p1:
            possible_subargs_r, map_arg_to_q = await build_subarguments_based_on_rule(
                rule
            )

            if possible_subargs_r is None:
                continue  # algum q não foi possível, logo não é possível usar a regra rule

            args_p1_r = self.build_def_args_based_on_rule(
                p1, possible_subargs_r, map_arg_to_q
            )

            args_p1.update(args_p1_r)

        return args_p1

    def build_def_args_based_on_rule(
        self, p1, possible_subargs_r: list[set[Argument]], map_arg_to_q: dict
    ):
        """
        TODO: tentar refatorar
        """
        args_r = set()

        if not possible_subargs_r:
            arg_p1 = Argument(ArgNodeLabel(p1)).with_T_child()
            arg_p1.supp_by_justified = True
            return {arg_p1}

        for subargs_combinations in itertools.product(*possible_subargs_r):
            arg_p1 = Argument(ArgNodeLabel(p1))

            for arg_q1 in subargs_combinations:
                q = map_arg_to_q[arg_q1]
                arg_q1: Argument = arg_q1
                q1 = arg_q1.conclusion.label

                similarity = self.system.sim_function(q, q1)

                if q1.definer != self or similarity < 1:  ## necessita instanciação !!
                    q_inst = ILLiteral(q1.definer, q1.literal, similarity)
                    arg_q1.conclusion.label = q_inst  #!!! verificar se não terá problema

                arg_p1.children.add(arg_q1)

            if any(arg.rejected for arg in arg_p1.children):
                arg_p1.rejected = True
            elif all(arg.justified for arg in arg_p1.children):
                arg_p1.justified = True

            arg_p1.update_strength()

            args_r.add(arg_p1)

        return args_r

    async def query_agents(
        self,
        agents: list[Agent],
        q: LLiteral,
        focus: QueryFocus,
        hist_p1: list[LLiteral],
    ):
        args_q = list()

        for agent in agents:
            answer = await agent.query(q, focus, hist_p1)
            args_q += answer.args_p

        return args_q

   
    def __str__(self) -> str:
        return self.name[0].upper()