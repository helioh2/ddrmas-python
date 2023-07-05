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

from yaml import load, safe_load
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
    if split_rule[1].strip() == "":
        body = set()
    else:
        body = set(parse_lliteral(bm.strip(), agents_dict) for bm in split_rule[1].split(";"))

    return Rule(rule_name, head, body, rule_type)


def load_system_from_yaml_dict(data: dict) -> System:

    system = System()

    agents_dict: dict[str, Agent] = {}

    for agent_name in data["agents"].keys():
        agent = Agent(agent_name, system)
        system.add_agent(agent)
        agents_dict[agent_name] = agent

    for agent_name, agent in agents_dict.items():
        if data["agents"][agent_name]["rules"]:

            for rule_name, rule_string in data["agents"][agent_name]["rules"].items():   
                rule = parse_rule(rule_name, rule_string, agents_dict)
                agent.kb.add(rule)

        for agent_trusted_name, value in data["agents"][agent_name]["trust"].items():
            agent_trusted = agents_dict[agent_trusted_name]
            agent.trust[agent_trusted] = float(value)

    vocabulary = list(system.vocabulary)

    similarity_between_literals = {literal: {} for literal in 
                                       vocabulary + [lit.negated() for lit in vocabulary]}
    pairs = set()
    for sim in data["similarities"]:
        on_equal: list[str] = sim.split("=")
        # sim_value = int(on_equal[1].strip())
        left_side_cleaned = on_equal[0].replace("theta", "").replace("(", "").replace(")", "").replace("['M']", "").strip()
        on_comma = left_side_cleaned.split(",")
        lit1 = Literal(True, on_comma[0].strip(), ["M"])
        lit2 = Literal(True, on_comma[1].strip(), ["M"])

        pairs.add((lit1, lit2))

    for i in range(len(vocabulary)):
            literal1 = vocabulary[i]
            literal1_neg = literal1.negated()
            similarity_between_literals[literal1][literal1] = 1
            similarity_between_literals[literal1_neg][literal1_neg] = 1
            similarity_between_literals[literal1][literal1_neg] = 0
            similarity_between_literals[literal1_neg][literal1] = 0

            for j in range(i+1, len(vocabulary)):
                literal2 = vocabulary[j]
                literal2_neg = literal2.negated()

                sim = 0
                if (literal1, literal2) in pairs or (literal2, literal1) in pairs:
                    sim = 1

                similarity_between_literals[literal1][literal2] = sim
                similarity_between_literals[literal2][literal1] = sim
                similarity_between_literals[literal1_neg][literal2_neg] = sim
                similarity_between_literals[literal2_neg][literal1_neg] = sim

                similarity_between_literals[literal1][literal2_neg] = 0
                similarity_between_literals[literal2_neg][literal1] = 0
                similarity_between_literals[literal2][literal1_neg] = 0
                similarity_between_literals[literal1_neg][literal2] = 0
    
    system.sim_function = lambda a,b: similarity_between_literals[a][b]

    return system
    

def load_system_from_file(path: str) -> System:
    stream = open(path, "r", encoding="utf-8")
    data = load(stream, Loader=Loader)
    return load_system_from_yaml_dict(data)


def load_system_from_yaml_str(_yaml: str):
    data = safe_load(_yaml)
    return load_system_from_yaml_dict(data)
    
