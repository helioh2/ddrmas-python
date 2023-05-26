"""
Exemplo de arquivo (YAML):

a:
    rules:
        r_a1: (a, ¬ed(M)) <= (a, dc(M))
        r_a2: (a, col(M)) <= (@, ed(M))
        r_a3: (a, ¬col(M)) <= (@, ¬ed(M))
    trust:
        b: 0.4
        c: 0.6
        d: 0.2
        e: 0.8

b:
    rules:
        r_b1: (b, ¬ed(M)) <= (b, hv(M))
        r_b2: (b, col(M)) <= (@, ed(M))
        r_b3: (b, ¬col(M)) <= (@, ¬ed(M))
    trust:
        a: 0.5
        c: 0.5
        d: 0.5
        e: 0.5

c:
    rules:
        r_c1: (c, ed(M)) <= (@, avl(M))
    trust:
        a: 1
        b: 0.4
        d: 0.4
        e: 1

d:
    rules:
        r_d1: (d, ¬ed(M)) <= (@, am(M))
    trust:
        a: 0.4
        b: 0.4
        c: 1
        e: 1

e:
    rules:
        r_e1: (e, spa(M)) <= (e, hv(M)); (e, pbc(M))
    trust:
        a: 0.4
        b: 0.6
        c: 0.2
        d: 0.8

"""

import re

from ddrmas_python import __version__

from ddrmas_python.models.Agent import Agent
from ddrmas_python.models.LLiteral import LLiteral, Sign
from ddrmas_python.models.Literal import Literal
from ddrmas_python.models.Rule import Rule, RuleType
from ddrmas_python.models.System import System

from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def parse_literal(literal_string: str) -> Literal:
    positive = not literal_string[0] == "¬"

    if not positive:
        literal_string = literal_string[1:]
    
    pred = literal_string.split("(")[0]

    between_parenthesis = re.findall(r"\((\w+)\)", literal_string)
    terms = between_parenthesis[0].split()
    
    return Literal(positive, pred, terms)


def parse_lliteral(lliteral_string: str, agents_dict: dict[str, Agent]) -> LLiteral:
    split_llit = lliteral_string[1:-1].split(",")

    if split_llit[0].strip() == "@":
        definer = Sign.SCHEMATIC
    else:
        definer = agents_dict[split_llit[0].strip()]
        
    literal = parse_literal(split_llit[1].strip()) 

    return LLiteral(definer, literal)


def parse_rule(rule_name: str, rule_string: str, agents_dict: dict[str, Agent]) -> Rule:

    if "<=" in rule_string:
        rule_type = RuleType.DEFEASIBLE
        split_rule = rule_string.split("<=")
    else:
        rule_type = RuleType.STRICT
        split_rule = rule_string.split("<-")

    head = parse_lliteral(split_rule[0].strip(), agents_dict)
    body = [parse_lliteral(bm.strip(), agents_dict) for bm in split_rule[1].split(";")]

    return Rule(rule_name, head, body, rule_type)


def load_system_from_file(path: str) -> System:
    
    stream = open(path, "r", encoding="utf-8")
    data = load(stream, Loader=Loader)
    
    system = System()

    agents_dict: dict[str, Agent] = {}

    for agent_name in data.keys():
        agent = Agent(agent_name, system)
        system.add_agent(agent)
        agents_dict[agent_name] = agent

    for agent_name, agent in agents_dict.items():
        for rule_name, rule_string in data[agent_name]["rules"].items():   
            rule = parse_rule(rule_name, rule_string, agents_dict)
            agent.kb.add(rule)

        for agent_trusted_name, value in data[agent_name]["trust"].items():
            agent_trusted = agents_dict[agent_trusted_name]
            agent.trust[agent_trusted] = float(value)
    
    # print_system(system)

    return system


# load_system_from_file("./mushroom.yaml")