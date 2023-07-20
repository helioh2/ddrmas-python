from __future__ import annotations

import asyncio
import functools
import itertools
import traceback
from operator import mul

from typing import TYPE_CHECKING
from dataclasses import dataclass, field

from promise import Promise
from ddrmas_python.models.ArgNodeLabel import ArgNodeLabel
from ddrmas_python.models.Argument import ArgType, Argument
from ddrmas_python.models.Answer import Answer, TruthValue
from ddrmas_python.models.ILLiteral import ILLiteral
from ddrmas_python.models.LLiteral import LLiteral, Sign
from ddrmas_python.models.QueryFocus import QueryFocus

from ddrmas_python.models.Rule import Rule, RuleType

# from ddrmas_python.utils import cache

from ddrmas_python.utils.base_logger import logger


if TYPE_CHECKING:
    from ddrmas_python.models.System import System
    


class MaxArgsExceededException(Exception):

    def __init__(self, query_focus, args):
        self.query_focus = query_focus
        self.args = args



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
    cache_args: dict[tuple(LLiteral, QueryFocus), asyncio.Future] = field(default_factory=dict)
    cache_answers: dict[tuple(LLiteral, QueryFocus), asyncio.Future] = field(default_factory=dict)
    cache_fall: dict[LLiteral, Argument] = field(default_factory=dict)


    def __hash__(self) -> int:
        return hash(self.name)



    async def query(
        self, p: LLiteral, focus: QueryFocus, hist: list[LLiteral]
    ) -> Answer:
        
        logger.info(f"""Agent {self.name} starting execution of Query {focus.name},
          p={str(p)}, hist=[{",".join([str(q) for q in hist])}]:\n
                        """)

        # if (p, focus) in self.cache_args.keys():
        #     logger.info(f"ESPERANDO GERACAO DE RESPOSTA PARA p={p}")
        #     ans = await self.cache_answers[(p, focus)]
        #     return ans
        
        # loop = asyncio.get_running_loop()
        # self.cache_answers[(p, focus)] = loop.create_future()

        self.system.query_focuses.add(focus)

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
            return Answer(p, focus, TruthValue.FALSE, args_p, args_not_p)

        # rlits = [p1 for p1 in rlits if {p1, p1.negated()}.isdisjoint(hist)]

        args_p, rlits_not_in_hist = self.create_fallacious_arguments(hist, rlits)

        if not rlits_not_in_hist:
            return Answer(p, focus, TruthValue.UNDECIDED, args_p, args_not_p)
        
        logger.info(f"""rlits não repetidos encontrados: {rlits_not_in_hist}
                    """)
    
        for p1 in rlits_not_in_hist:
            
            positive_p1 = LLiteral(p1.definer, p1.literal.as_positive())

            tv_p1_strict = False
            args_p1 = set()
            args_not_p1 = set()
            has_strict_answer_p1 = False

            if (positive_p1, focus) in self.cache_args.keys():
                logger.info(f"ESPERANDO GERACAO DE ARGUMENTO PARA p1={positive_p1} e not p1")
                args_p1, args_not_p1, tv_p1 = await self.get_cached_args(
                    focus, p1, positive_p1
                    )
            else:
                loop = asyncio.get_running_loop()
                self.cache_args[(positive_p1, focus)] = loop.create_future()

                local_answer_p1 = await self.local_ans(p1, extended_kb)
                if local_answer_p1["tv"] == True:
                    args_p1.add(local_answer_p1["arg"])
                    tv_p1_strict = True
                    has_strict_answer_p1 = True
                else:
                    local_answer_not_p1 = await self.local_ans(p1, extended_kb)
                    if local_answer_not_p1["tv"] == True:
                        args_not_p1.add(local_answer_not_p1["arg"])                      
                        has_strict_answer_p1 = True

                args_p1.update(await self.find_defeasible_args(p1, extended_kb, focus, hist))
                args_not_p1.update(
                    await self.find_defeasible_args(p1.negated(), extended_kb, focus, hist)
                    )
                logger.info(f"Agent {self.name} ACABOU DE TERMINAR EXECUÇÃO DO find_def_args")
                if has_strict_answer_p1 and not tv_p1_strict:
                    tv_p = TruthValue.FALSE
                    for arg in args_p1:
                        arg.rejected = True

                elif has_strict_answer_p1 and tv_p1_strict:
                    tv_p = TruthValue.TRUE
                    for arg in args_not_p1:
                        arg.rejected = True

                else:
                    tv_p1 = self.compare_def_args(args_p1, args_not_p1)

                if tv_p1 == TruthValue.TRUE:
                    tv_p = TruthValue.TRUE
                elif tv_p1 == TruthValue.UNDECIDED and tv_p != TruthValue.TRUE:
                    tv_p = TruthValue.UNDECIDED
                
                self.set_cached_args(
                    focus, p1, positive_p1, args_p1, args_not_p1, tv_p1
                    )

            print("CHEGUEI AQUI (APÓS DEF FINDING)")
            logger.info(f"""Agent {self.name} executou find_def_args para p1={p1}.\n
                            Query atual: p={p}, hist={hist}""")
            
            # if args_p1:
            #     args_p1_str = "\n".join(str(arg) for arg in args_p1)
            logger.info(f"""len(args_p1) = \n{len(args_p1)}""")
            # if args_not_p1:
            #     args_p1_str = "\n".join(str(arg) for arg in args_not_p1)
            logger.info(f"""len(args_not_p1) = {len(args_not_p1)}""")


            args_p = args_p.union(args_p1)
            args_not_p = args_not_p.union(args_not_p1)

        ans = Answer(p, focus, tv_p, args_p, args_not_p)

        logger.info(f"Agent {self.name} achou answer para {p}: {ans}")

        # self.cache_answers[(p, focus)].set_result(ans)

        return ans
    

    def set_cached_args(self, focus, p1, positive_p1, args_p1, args_not_p1, tv_p1):
        """
        TODO: verificar necessidade de criar criar lock para cache na atualização
        """
        
        if p1 == positive_p1:
            args_positive_p1 = args_p1
            args_negative_p1 = args_not_p1
        else:
            args_positive_p1 = args_not_p1
            args_negative_p1 = args_p1
                
        self.cache_args[(positive_p1, focus)].set_result(
                    (args_positive_p1, args_negative_p1, tv_p1)
                    )

    async def get_cached_args(self, focus, p1, positive_p1):
        args_positive_p1, args_negative_p1, tv_p1 = \
                    await self.cache_args[(positive_p1, focus)]
                
        if p1 == positive_p1:
            args_p1 = args_positive_p1
            args_not_p1 = args_negative_p1
        else:
            args_p1 = args_negative_p1
            args_not_p1 = args_positive_p1
        return args_p1, args_not_p1, tv_p1
    
            
        
    def create_new_extended_kb(self, focus):
        localized_focus_kb = set(rule.localize(self) for rule in focus.kb)
        extended_kb = self.kb.union(localized_focus_kb)
        self.extended_kbs[focus.name] = extended_kb
        return extended_kb

    def find_similar_lliterals(self, p: LLiteral, extended_kb: set[Rule]):
        rlits = set()
        for rule in extended_kb:
            if self.system.similar_enough(rule.head.literal, p.literal):
                rlits.add(rule.head)

        return rlits

    def create_fallacious_arguments(self, hist: list[LLiteral], rlits: list[LLiteral]):
        args_p = set()
        new_rlits = set()
        for i, p1 in enumerate(rlits):
            if not {p1.literal, p1.negated().literal}.isdisjoint(hist):
                if p1 in self.cache_fall.keys():
                    fall_arg_p1 = self.cache_fall[p1]
                else:
                    fall_arg_p1 = Argument(ArgNodeLabel(p1, fallacious=True), strength=1.)
                    self.cache_fall[p1] = fall_arg_p1
                args_p.add(fall_arg_p1)
            else:
                new_rlits.add(p1)

        return args_p, new_rlits
    

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

            subarguments = await build_subarguments_based_on_rule(rule)
            if subarguments is None:
                # quando não é possível construir os subargumentos com base na regra
                continue

            arg.children.update(subarguments)

            return {
                "tv": True,
                "arg": arg,
            }  # a primeira regra a partir da qual um argumento pode ser gerado é usado.

        # else
        return {"tv": False, "arg": None}


    # def remove_redundant_args(args_q):

    #     new_args_q = set()

    #     for arg1 in args_q:
    #         for arg2 in args_q:
    #             if arg1 != arg2:
    #                 leaf_nodes_arg1 = arg1.leaf_nodes()
    #                 leaf_nodes_arg2 = arg2.leaf_nodes()
    #                 if all(self.system.similar_enough(l_node) 



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
                   
                    args_q = await self.query_agents([self], q, focus, hist_p1)  # faz a query primeiro para o próprio agente

                    has_focus_rule_for_q = q.literal in (rule.head.literal for rule in focus.kb if not rule.body)

                    if not has_focus_rule_for_q:
                        logger.info(f"LOGO APÓS queryagents, len(args_q) = {len(args_q)}")
                        has_perfect_strength = any(not arg.is_fallacious() and arg.strength==1 for arg in args_q)
                        if not args_q or not has_perfect_strength:
                            all_agents_except_self = set(self.system.agents.values()).difference({self})
                            args_q.update(await self.query_agents(all_agents_except_self, q, focus, hist_p1))
                   
                elif isinstance(q.definer, Agent):
                    args_q = await self.query_agents([q.definer], q, focus, hist_p1)
                    
                if not args_q:
                    return (
                        None,
                        None,
                    )  # não foi possível construir args para todos os membros do corpo

                # args_q = self.remove_redundant_args(args_q)

                for arg in args_q:
                    map_arg_to_q[arg] = q

                possible_subargs_r.append(args_q)

            # else
            return possible_subargs_r, map_arg_to_q

        args_p1 = set()
        hist_p1 = hist + [p1.literal]

        rules_with_head_p1 = {rule for rule in extended_kb if rule.head == p1 and not rule.body}
        if not rules_with_head_p1:  #priorizar regras sem corpo
            rules_with_head_p1 = {rule for rule in extended_kb if rule.head == p1}

        for rule in rules_with_head_p1:

            logger.info(f"Processando regra: {rule}")

            possible_subargs_r, map_arg_to_q = await build_subarguments_based_on_rule(
                rule
            )


            if possible_subargs_r is None:
                logger.info(f"INDO PRA PROXIMA REGRA")
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
            arg_p1 = Argument(ArgNodeLabel(p1))  # "folha"
            arg_p1.supp_by_justified = True
            arg_p1.strength = 1.
            return {arg_p1}

        try:
            amount_args_resultant = 1
            for args_set in possible_subargs_r:
                amount_args_resultant *= len(args_set) 

            amount_args_in_cache = sum(len(cached.result()[0]) + len(cached.result()[1]) for cached in self.cache_args.values() if cached.done())
            if amount_args_resultant + amount_args_in_cache > self.system.MAX_ARGUMENTS_NUMBER_PER_QUERY:
                self.system.max_arguments_times += 1
                raise MaxArgsExceededException(list(self.system.query_focuses)[0], []) 
            
            for subargs_combinations in itertools.product(*possible_subargs_r):
                arg_p1 = Argument(ArgNodeLabel(p1))

                for arg_q1 in subargs_combinations:
                    q = map_arg_to_q[arg_q1]
                    arg_q1: Argument = arg_q1
                    q1 = arg_q1.conclusion.label

                    similarity = self.system.sim_function(q.literal, q1.literal)

                    if q1.definer != self or similarity < 1:  ## necessita instanciação !!
                        q_inst = ILLiteral(q1.definer, q1.literal, similarity)
                        arg_q1.conclusion.label = q_inst

                    arg_p1.children.add(arg_q1)

                if any(arg.rejected for arg in arg_p1.children):
                    arg_p1.rejected = True
                elif all(arg.justified for arg in arg_p1.children):
                    arg_p1.supp_by_justified = True

                arg_p1.update_strength() #TODO: verificare possibilidade e beneficios de se interromper geração de
                ## argumentos quando um argumento com força 1 (max) for encontrado

                args_r.add(arg_p1)

        except Exception as exc:
            traceback.print_exc()
            logger.error(exc)
            logger.error("len(possible_subargs_r)"+str(len(possible_subargs_r)))
            # for arg in possible_subargs_r:
            #     logger.error(str(arg))

            raise exc
        return args_r

    async def query_agents(
        self,
        agents: list[Agent],
        q: LLiteral,
        focus: QueryFocus,
        hist_p1: list[LLiteral],
    ):
        args_q = set()

        for agent in agents:
            answer = await agent.query(q, focus, hist_p1)
            args_q.update(answer.args_p)

            if self != agent:
                self.system.amount_messages_exchanged += 2

                all_args = set()
                for arg in answer.args_p.union(answer.args_not_p):
                    all_args.add(arg)
                    for sub_arg in arg.proper_subargs():
                        all_args.add(sub_arg)

                self.system.size_messages_answers.append(len(all_args))
            
        return args_q

    def compare_def_args(
        self, args_p1: set[Argument], args_not_p1: set[Argument]
    ) -> TruthValue:
        
        tv_p1 = TruthValue.UNDECIDED


        nu_args_for_p1 = {
            a_p1 for a_p1 in args_p1 if not a_p1.rejected
        }  ## args para p1 não rejeitados por undercut

        nu_args_for_not_p1 = {
            a_n_p1 for a_n_p1 in args_not_p1 if not a_n_p1.rejected
        }  ## args para not p1 não rejeitados por undercut


        for arg in nu_args_for_p1.union(nu_args_for_not_p1):

            opposite_args = nu_args_for_not_p1 if (arg in nu_args_for_p1) else nu_args_for_p1
            # custo de verificação constante pelo uso de set
            
            any_nu_for_opposite_defeats = any(
                a.defeats(arg) for a in opposite_args
            )

            ## a ideia é verificar se todos os argumentos opostos que não foram rejeitados
            ## não derrotam arg. Se um argumento derrota, mas é rejeitado, então
            ## foi undercut.

            if not any_nu_for_opposite_defeats:

                if arg.supp_by_justified:
                    arg.justified = True

                    # basta um argumento justificado para que resposta seja true
                    if arg in nu_args_for_p1:
                        tv_p1 = TruthValue.TRUE

            else:
                # só é rejeitado se alguém derrota, mesmo que não seja SuppJ (i.e. falaciosos)
                arg.rejected = True


        if tv_p1 != TruthValue.TRUE and (
            not args_p1 or all(arg_p1.rejected for arg_p1 in args_p1)
        ):
            # não há argumentos em args_p1 ou todos foram rejeitados
            tv_p1 = TruthValue.FALSE

        return tv_p1

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return str(self)
