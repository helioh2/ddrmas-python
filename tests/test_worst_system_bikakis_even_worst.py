
import asyncio
from itertools import product
import math
import os
import random
import string
import time


import pandas as pd
import numpy as np

from dataclasses import dataclass, field
from ddrmas_python.models.LLiteral import Sign
from ddrmas_python.models.QueryFocus import QueryFocus
from ddrmas_python.models.Rule import RuleType
from ddrmas_python.models.Agent import Agent
from ddrmas_python.models.LLiteral import LLiteral
from ddrmas_python.models.Literal import Literal
from ddrmas_python.models.Rule import Rule

from ddrmas_python.models.System import System
from ddrmas_python.services.load_system_from_file import load_system_from_yaml_str
from ddrmas_python.services.print_system import print_system

from ddrmas_python.utils.base_logger import logger

import signal
import traceback

import pickle



class MyException(RuntimeError):
    def __init__(self,message,query_focus):
        super().__init__(message)
        self.query_focus = query_focus


def agent_name_generator():
    
    cont = 1
    while True:
        for letter in string.ascii_lowercase:
            yield letter + str(cont)
        cont += 1


def literal_name_generator():

    cont = 1
    while True:
        for letter1, letter2 in product(string.ascii_lowercase, string.ascii_lowercase):
            yield letter1 + letter2 + str(cont) 
        cont += 1


def focus_name_generator():

    greek_letters = [
        'Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Iota', 'Kappa', 'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho',
        'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega'
    ]
    cont = 1
    while True:
        for letter in greek_letters:
             yield letter + str(cont)
        cont += 1


def sim_to_str(sim_dict):
    str_ = ""
    for lit1, rlits in sim_dict.items():
        for lit2 in rlits:
            if lit1 == lit2 or not lit1.positive:
                continue
            if sim_dict[lit1][lit2] != 0:
                str_ += f"theta({str(lit1)}, {str(lit2)}) = {str(sim_dict[lit1][lit2])}"

    return str_


def print_similarities(sim_dict):
    print("Similarities: ")
    logger.info("Similarities: ")
    for lit1, rlits in sim_dict.items():
        for lit2 in rlits:
            if lit1 == lit2 or not lit1.positive:
                continue
            if sim_dict[lit1][lit2] != 0:
                print(f"theta({str(lit1)}, {str(lit2)}) = {str(sim_dict[lit1][lit2])}")
                logger.info(f"theta({str(lit1)}, {str(lit2)}) = {str(sim_dict[lit1][lit2])}")


@dataclass
class DDRMASTester:

    literalsNumber: int
    similarity_between_literals: dict = field(default_factory=dict)
    system: System = None
    focus_name_gen = focus_name_generator()
    literals: list[Literal] = field(default_factory=list)
    agents_list: list[Agent] = field(default_factory=list)
    

    def create_system(self) -> System:

        self.system = System(sim_threshold=1)

        agents = {}
        agents_last_rule_numbers = {}

        agent_name_gen = agent_name_generator()
        literal_name_gen = literal_name_generator()

        for _ in range(self.literalsNumber):
            agent = Agent(next(agent_name_gen), self.system)
            agents[agent.name] = agent
            agents_last_rule_numbers[agent.name] = 1
            self.agents_list.append(agent)

        for agent, trusted_agent in product(agents.values(), agents.values()):
            if agent == trusted_agent:
                agent.trust[trusted_agent] = 1
            else:
                agent.trust[trusted_agent] = random.random()

        for _ in range(self.literalsNumber):
            self.literals.append(Literal(positive=True, pred=next(literal_name_gen), terms=["M"]))


        self.similarity_between_literals = {literal: {} for literal in 
                                       self.literals + [lit.negated() for lit in self.literals]}

       
        for i in range(len(self.literals)):
            literal1 = self.literals[i]
            literal1_neg = literal1.negated()
            self.similarity_between_literals[literal1][literal1] = 1
            self.similarity_between_literals[literal1_neg][literal1_neg] = 1
            self.similarity_between_literals[literal1][literal1_neg] = 0
            self.similarity_between_literals[literal1_neg][literal1] = 0

            for j in range(i+1, len(self.literals)):
                literal2 = self.literals[j]
                literal2_neg = literal2.negated()

                sim = 0
                # if (literal1, literal2) in pairs or (literal2, literal1) in pairs:
                #     sim = 1

                self.similarity_between_literals[literal1][literal2] = sim
                self.similarity_between_literals[literal2][literal1] = sim
                self.similarity_between_literals[literal1_neg][literal2_neg] = sim
                self.similarity_between_literals[literal2_neg][literal1_neg] = sim

                self.similarity_between_literals[literal1][literal2_neg] = 0
                self.similarity_between_literals[literal2_neg][literal1] = 0
                self.similarity_between_literals[literal2][literal1_neg] = 0
                self.similarity_between_literals[literal1_neg][literal2] = 0

        print_similarities(self.similarity_between_literals)

        self.system.sim_function = lambda a,b: self.similarity_between_literals[a][b]


        for k in range(self.literalsNumber):
            """padrão de pior caso do bikakis"""
            head_literal = self.literals[k]
            head_literal_negated = head_literal.negated()
            definer_agent = self.agents_list[k]
            head = LLiteral(definer_agent, head_literal)
            head_negated = LLiteral(definer_agent, head_literal_negated)

            
            for j in range(0, self.literalsNumber):
                body = set()

                literal_to_exclude = self.literals[j]

                if head_literal == literal_to_exclude:
                        continue

                for i in range(0, self.literalsNumber):
                    literal2 = self.literals[i]

                    if head_literal == literal2 or literal2 == literal_to_exclude:
                        continue

                    definer = self.agents_list[i]
                    lliteral = LLiteral(definer, literal2)
                    body.add(lliteral)
            
                rule_pos_name = "r_" + definer_agent.name + str(agents_last_rule_numbers[definer_agent.name])
                agents_last_rule_numbers[definer_agent.name] += 1
                rule_pos = Rule(rule_pos_name, head, body)

                rule_neg_name = "r_" + definer_agent.name + str(agents_last_rule_numbers[definer_agent.name])
                agents_last_rule_numbers[definer_agent.name] += 1
                rule_neg = Rule(rule_neg_name, head_negated, body)

                definer_agent.kb.add(rule_pos)
                definer_agent.kb.add(rule_neg)


        self.system.agents = agents

        logger.info(f"System:\n{self.system}")
        
        return self.system

        
    async def do_query(self, focus_kb_side = 0):

        literal = self.literals[0]
        emitter_agent = self.agents_list[0]
        lliteral = LLiteral(emitter_agent, literal)

        focus_name = next(self.focus_name_gen)
        focus_kb = []
        focus_rule_number = 1
        for k in range(focus_kb_side):

            head_literal = random.choice(self.literals)
            while literal == head_literal:
                head_literal = random.choice(self.literals)
            head_lliteral = LLiteral(Sign.FOCUS, head_literal)
            
            rule_name = "r_" + focus_name + str(focus_rule_number)
            focus_rule_number += 1
            rule = Rule(rule_name, head_lliteral, [], RuleType.DEFEASIBLE)

            if rule in focus_kb:
                k -= 1
                continue


            focus_kb.append(rule)

        
        focus = QueryFocus(focus_name, lliteral, emitter_agent, focus_kb)


        print("Query: ")
        print(focus)
        logger.info("Query: "+str(focus)+"\n")
    
        try:
            ans = await emitter_agent.query(lliteral, focus, [])
        except Exception as exc:
            exc2 = Exception(focus)
            raise exc2
        
        return ans, focus

        


##TESTE:

def handler(signum, frame):
    print("Demorou demais!!")
    raise Exception("end of time")



# def results_loader():

#     for _ in range(TIMES_RUN):
#         with open('results.pkl', 'rb') as f:
#             yield pickle.load(f)


async def perform_queries():
    
    results = []

    logger.setLevel("WARNING")

    exec_times = []

    # agentsNumber=5
    # literalsNumber=10 
    # rulesNumber=10 
    # sslPercentage=0.8
    # cyclePercentage=0
    # similarityPercentage=0.1

    if os.path.isfile("results.pkl"):
        os.remove("results.pkl")

    timesRun = 1

    literalsNumber=5

    for k in range(timesRun):

        # tester = RandomDDRMASTester(
        #     agentsNumber=3, 
        #     literalsNumber=10, 
        #     rulesNumber=10, 
        #     sslPercentage=0.8, 
        #     cyclePercentage=0,
        #     similarityPercentage=0.1
        # )


        tester = DDRMASTester(
            literalsNumber=literalsNumber
        )


        # signal.signal(signal.SIGALRM, handler)

        # signal.alarm(15)

        # tester = RandomDDRMASTester(
        #     agentsNumber=20, 
        #     literalsNumber=100, 
        #     rulesNumber=300, 
        #     sslPercentage=0.8, 
        #     cyclePercentage=0,
        #     similarityPercentage=0.1200
        # )
        tester.create_system()
        print_system(tester.system)
                
        print("\n\n\n--------query\n\n")
        ans, query_focus = None, None
        start_time = time.time()
        try:
            ans, query_focus = await tester.do_query(focus_kb_side=0)
        except Exception as exc:
            traceback.print_exc()
            logger.error(exc)
            query_focus = exc.args[0]

        end_time = time.time()

        exec_times.append(end_time-start_time)


        # results.append({"system": tester.system, "answer": ans})

        agents = tester.system.agents.values()
        all_args = []
        for agent in agents:
            for cached in agent.cache.values():
                if cached.done():
                    all_args += [str(arg) for arg in cached.result()[0]]
                    all_args += [str(arg) for arg in cached.result()[1]]
        

        if all_args:
            print("tem args")

        with open('results.pkl', 'ab') as f:
            pickle.dump(
                {
                    "all_args": all_args, 
                    "query_focus": str(query_focus),
                    # "tv": ans.tv_p,
                    "system": str(tester.system),
                    "similarities": sim_to_str(tester.similarity_between_literals),
                    "messages_count": tester.system.amount_messages_exchanged,
                    "max_count":  tester.system.max_arguments_times
                }, 
                f)

        logger.info("Answer: "+str(ans))

    logger.warning("Config:")


    # results = results_loader()

    amount_arguments_per_ans = []
    messages_exchanged_per_ans = []
    times_max_arguments_achieved = []
    query_focuses_per_ans = []
    tvs_per_ans = []
    max_args_len = 0
    max_args = []
    max_system = None
    max_similarities = None
    max_query_focus = None
    with open('results.pkl', 'rb') as f:
        for k in range(timesRun):
            
            res = pickle.load(f)

            total_args = len(res["all_args"])

            if total_args > max_args_len:
                max_args_len = total_args
                max_args = res["all_args"]
                max_system = res["system"]
                max_similarities = res["similarities"]
                max_query_focus = res["query_focus"]

            
            amount_arguments_per_ans.append(total_args)

            messages_exchanged_per_ans.append(res["messages_count"])
            times_max_arguments_achieved.append(res["max_count"])
            query_focuses_per_ans.append(res["query_focus"])
            # tvs_per_ans.append(res["tv"])

    logger.warning("Times in which max number of arguments was achieved: "+str(sum(times_max_arguments_achieved)))


    # distinct_arguments_per_ans = [set(arg for arg in res["answer"].args_p.union(res["answer"].args_not_p)) for res in results]

    # distinct_args_and_subargs_per_ans = []
    # for args_set in distinct_arguments_per_ans:
    #     subargs_set = set()
    #     for arg in args_set:
    #         subargs_set.add(arg)
    #         subargs_set.update(arg.proper_subargs())
        
    #     distinct_args_and_subargs_per_ans.append(subargs_set)


    # amount_arguments_per_ans = [len(subargs_set) for subargs_set in distinct_args_and_subargs_per_ans]


    # logger.warning("Amount of arguments of the greatest case:" + str(len(max_ans.args_p.union(max_ans.args_not_p))))
    
    
    logger.warning("System of the greatest case:")
    logger.warning(max_system)

    logger.warning("Query focus of the greatest case:")
    logger.warning(max_query_focus)

    logger.warning("Similarities of the greatest case:")
    logger.warning(max_similarities)

    
    logger.warning("Arguments of the greatest case:")
    for arg in max_args:
        logger.warning(arg)


        

    logger.info("Statistics for amount of arguments in answers:")

    # logger.info("Average size of arguments: "+ str(sum(arg_sizes) / len(arg_sizes)))
    # logger.info("Min size of arguments: "+ str(min(arg_sizes)))
    # logger.info("Max size of arguments: "+ str(max(arg_sizes)))

    logger.warning("Amounts of arguments ordered from greatest to smallest: "+str(sorted(amount_arguments_per_ans, reverse=True)))

    arg_sizes_array = np.asarray(amount_arguments_per_ans)
    df_describe = pd.DataFrame(arg_sizes_array)
    logger.warning("Amount of arguments generated statistics:")
    logger.warning(df_describe.describe().astype(str))

    arg_sizes_array = np.asarray(messages_exchanged_per_ans)
    df_describe = pd.DataFrame(arg_sizes_array)
    logger.warning("Amount of messages exchanged statistics:")
    logger.warning(df_describe.describe().astype(str))


    arg_sizes_array = np.asarray(exec_times)
    df_describe = pd.DataFrame(arg_sizes_array)
    logger.warning("Times of execution statistics:")
    logger.warning(df_describe.describe().astype(str))
    # print(ans.tv_p)
    # logger.info(str(ans.tv_p)+"\n")


asyncio.run(perform_queries())

    
