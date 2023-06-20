
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from ddrmas_python.models.Agent import Agent
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
    query_focuses: list[QueryFocus] = field(default_factory=list)
    sim_function: Callable[[LLiteral, LLiteral], float] = lambda p, q: 1. if p == q else 0.
    sim_threshold: float = 1.
    MAX_ARGUMENTS_NUMBER_PER_QUERY: int = 500
    max_arguments_times = 0


    def __post_init__(self):
        print("SISTEMA INICIALIZADO!!")

    def add_agent(self, agent: Agent):
        self.agents[agent.name] = agent

    def remove_agent(self, agent: Agent):
        self.agents.remove(agent)

    def similar_enough(self, p:LLiteral, q:LLiteral) -> bool:
        return self.sim_function(p, q) >= self.sim_threshold
    
    def __str__(self) -> str:
        agents_dict = {}

        for agent in self.agents.values():

            agents_dict[agent.name] = {"rules": {}, "trust": {}}

            for rule in agent.kb:
                agents_dict[agent.name]["rules"][rule.name] = str(rule)

            for trusted_ag, value in agent.trust.items():
                agents_dict[agent.name]["trust"][trusted_ag.name] = value

        return str(yaml.dump(agents_dict))
    
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