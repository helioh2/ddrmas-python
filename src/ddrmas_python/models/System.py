
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from ddrmas_python.models.Agent import Agent
from ddrmas_python.models.Literal import Literal
from ddrmas_python.models.QueryFocus import QueryFocus
from ddrmas_python.models.LLiteral import LLiteral

import yaml
from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from ddrmas_python.utils.base_logger import logger


@dataclass
class System():
    """
    Class that representas a DDRMAS system
    """
    name: str = "default"
    agents: dict[str, Agent] = field(default_factory=dict)
    query_focuses: set[QueryFocus] = field(default_factory=set)
    sim_function: Callable[[Literal, Literal], float] = lambda p, q: 1. if p == q else 0.
    sim_threshold: float = 1.
    MAX_ARGUMENTS_NUMBER_PER_QUERY: int = 5000
    max_arguments_times = 0
    amount_messages_exchanged = 0
    max_argument_height: int = 10000000
    size_messages_answers: list = field(default_factory=list)
    


    def __post_init__(self):
        print("SISTEMA INICIALIZADO!!")

    def add_agent(self, agent: Agent):
        self.agents[agent.name] = agent

    def remove_agent(self, agent: Agent):
        self.agents.remove(agent)

    def similar_enough(self, p:LLiteral, q:LLiteral) -> bool:
        return self.sim_function(p, q) >= self.sim_threshold
    

    def str_similarities(self) -> list[str]:
        # print("Similarities: ")
        # logger.warning("Similarities: ")
        vocabulary = self.vocabulary
        res = []
        visited = set()
        for lit1 in vocabulary:
            if not lit1.positive:
                continue
            for lit2 in vocabulary:
                if lit1 == lit2 or not lit2.positive or (lit1,lit2) in visited or (lit2, lit1) in visited:
                    continue
                if self.sim_function(lit1, lit2) > 0:
                    res.append(f"theta({str(lit1)}, {str(lit2)}) = {str(self.sim_function(lit1, lit2))}")
                    visited.add((lit1, lit2))
        return res


    

    def __str__(self) -> str:

        res_dict = {}

        agents_dict = {}

        for agent in self.agents.values():

            agents_dict[agent.name] = {"rules": {}, "trust": {}}

            for rule in agent.kb:
                agents_dict[agent.name]["rules"][rule.name] = str(rule)

            for trusted_ag, value in agent.trust.items():
                agents_dict[agent.name]["trust"][trusted_ag.name] = value

        res_dict["agents"] = agents_dict

        res_dict["similarities"] = self.str_similarities()

        return str(yaml.dump(res_dict))
    
    def get_agent(self, agent_name: str):
        return self.agents[agent_name]
    
    @property
    def vocabulary(self):
        
        literals = set()
        for agent in self.agents.values():
            for rule in agent.kb:
                literals.add(rule.head.literal.as_positive())
                for bm in rule.body:
                    literals.add(bm.literal.as_positive())

        return literals
    

    def all_args_in_cache(self):
        all_args = []
        for agent in self.agents.values():
            for cached in agent.cache_args.values():
                if cached.done():
                    all_args += [arg.to_graph() for arg in cached.result()[0]]
                    all_args += [arg.to_graph() for arg in cached.result()[1]]
        return all_args
    
    # @property
    # def vocabulary_llits(self):

    #     lliterals = set()
    #     for agent in self.agents.values():
    #         for rule in agent.kb:
    #             lliterals.add(rule.head)
    #             for bm in rule.body:
    #                 lliterals.add(bm)

    #     return lliterals