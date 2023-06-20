
import asyncio
from itertools import product
import math
import random
import string


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
class RandomDDRMASTester:

    agentsNumber: int
    literalsNumber: int
    rulesNumber: int
    sslPercentage: float
    cyclePercentage: float   ## TODO
    similarityPercentage: float
    similarity_function = lambda a, b: 1 if a==b or random.random() <= 0.1 else 0
    system: System = None
    focus_name_gen = focus_name_generator()
    literals: list[Literal] = field(default_factory=list)
    

    def create_system(self) -> System:

        self.system = System(sim_threshold=1)

        agents = {}
        self.literals = []
        rules = []
        agents_last_rule_numbers = {}

        agent_name_gen = agent_name_generator()
        literal_name_gen = literal_name_generator()

        for _ in range(self.agentsNumber):
            agent = Agent(next(agent_name_gen), self.system)
            agents[agent.name] = agent
            agents_last_rule_numbers[agent.name] = 1

        for agent, trusted_agent in product(agents.values(), agents.values()):
            if agent == trusted_agent:
                agent.trust[trusted_agent] = 1
            else:
                agent.trust[trusted_agent] = random.random()

        for _ in range(self.literalsNumber):
            self.literals.append(Literal(positive=True, pred=next(literal_name_gen), terms=["M"]))


        similarity_between_literals = {literal: {} for literal in 
                                       self.literals + [lit.negated() for lit in self.literals]}
        
        pairs = set()
        for i in range(int(len(self.literals)*self.similarityPercentage)):
            lit1 = random.choice(self.literals)
            lit2 = random.choice(self.literals)

            while lit1 == lit2 or (lit1, lit2) in pairs or (lit2, lit1) in pairs:
                lit1 = random.choice(self.literals)
                lit2 = random.choice(self.literals)

            pairs.add((lit1, lit2))

        #ex: 10 literais. 10% de similaridade = 1 par de literais
        #ex: 100 literais. 10% de similaridade = 10 pares de literais (<=20 literais envolvidos?)

        for i in range(len(self.literals)):
            literal1 = self.literals[i]
            literal1_neg = literal1.negated()
            similarity_between_literals[literal1][literal1] = 1
            similarity_between_literals[literal1_neg][literal1_neg] = 1
            similarity_between_literals[literal1][literal1_neg] = 0
            similarity_between_literals[literal1_neg][literal1] = 0

            for j in range(i+1, len(self.literals)):
                literal2 = self.literals[j]
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

        print_similarities(similarity_between_literals)

        self.system.sim_function = lambda a,b: similarity_between_literals[a.literal][b.literal]

        for k in range(self.rulesNumber):
            definer_agent = random.choice(list(agents.values()))
            head_literal = random.choice(self.literals)
            head_literal.positive = True if random.randrange(0,2)==0 else False
            head_lliteral = LLiteral(definer_agent, head_literal)

            body_length = random.randrange(0,3)
            
            body_lliterals = []
            used_literals = {head_literal}
            for _ in range(body_length):

                literal = random.choice(self.literals)
                while literal in used_literals:
                    literal = random.choice(self.literals)
                used_literals.add(literal)

                literal.positive = random.randrange(0,2) == 0


                is_ssl = random.random() <= self.sslPercentage
                if is_ssl:
                    definer = Sign.SCHEMATIC
                else:
                    definer = random.choice(list(agents.values()))
                
                body_lliterals.append(LLiteral(definer, literal))


            rule_name = "r_" + definer_agent.name + str(agents_last_rule_numbers[definer_agent.name])
            agents_last_rule_numbers[definer_agent.name] += 1
            rule = Rule(rule_name, head_lliteral, body_lliterals, RuleType.DEFEASIBLE)

            if rule in definer_agent.kb:
                k -= 1
                continue

            rules.append(rule)
            definer_agent.kb.add(rule)



        self.system.agents = agents

        logger.info(f"System:\n{self.system}")
        
        return self.system

        
    async def do_random_query(self, focus_kb_side = 0):

        literal = random.choice(self.literals)
        emitter_agent = random.choice(list(self.system.agents.values()))
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
    
        ans = await emitter_agent.query(lliteral, focus, [])

        return ans
        # for arg in ans.args_p:
        #     print(str(arg))
        #     logger.info(str(arg))
        


##TESTE:

def handler(signum, frame):
    print("Demorou demais!!")
    raise Exception("end of time")



async def perform_queries():
    
    results = []

    logger.setLevel("WARNING")

    for k in range(1000):

        # tester = RandomDDRMASTester(
        #     agentsNumber=3, 
        #     literalsNumber=10, 
        #     rulesNumber=10, 
        #     sslPercentage=0.8, 
        #     cyclePercentage=0,
        #     similarityPercentage=0.1
        # )


          tester = RandomDDRMASTester(
            agentsNumber=5, 
            literalsNumber=10, 
            rulesNumber=10, 
            sslPercentage=0.8, 
            cyclePercentage=0,
            similarityPercentage=0.1
        )



        """ 
        TODO: verificar o que se deseja registrar.
            - Quantidade e tamanho médio dos argumentos gerados
                - Uso de memória
                - Verificação da existência de argumentos repetidos ou muito similares
            - Tempo de execução médio
            - Quantidade de mensagens trocadas entre os agentes

        """

        # signal.signal(signal.SIGALRM, handler)

        # signal.alarm(15)

        # tester = RandomDDRMASTester(
        #     agentsNumber=20, 
        #     literalsNumber=100, 
        #     rulesNumber=300, 
        #     sslPercentage=0.8, 
        #     cyclePercentage=0,
        #     similarityPercentage=0.1
        # )

        print_system(tester.create_system())
                
        print("\n\n\n--------query\n\n")
        ans = None
        try:
            ans = await tester.do_random_query(3)
        except Exception as exc:
            traceback.print_exc()
            logger.error(exc)


        results.append({"system": tester.system, "answer": ans})
        logger.info("Answer: "+str(ans))


    amount_arguments_per_ans = []
    for res in results:
        sum_ = 0
        for agent in res["system"].agents.values():
            for cached in agent.cache.values():
                if cached.done():
                    sum_ += len(cached.result()[0]) + len(cached.result()[1]) 
        
        amount_arguments_per_ans.append(sum_)


    times_max_arguments_achieved = sum(res["system"].max_arguments_times for res in results)
    logger.warning("Times in which max number of arguments was achieved: "+str(times_max_arguments_achieved))

    # distinct_arguments_per_ans = [set(arg for arg in res["answer"].args_p.union(res["answer"].args_not_p)) for res in results]

    # distinct_args_and_subargs_per_ans = []
    # for args_set in distinct_arguments_per_ans:
    #     subargs_set = set()
    #     for arg in args_set:
    #         subargs_set.add(arg)
    #         subargs_set.update(arg.proper_subargs())
        
    #     distinct_args_and_subargs_per_ans.append(subargs_set)


    # amount_arguments_per_ans = [len(subargs_set) for subargs_set in distinct_args_and_subargs_per_ans]

    max_amount_args = max(amount_arguments_per_ans)    
    max_index = amount_arguments_per_ans.index(max_amount_args)
    max_res = results[max_index]

    # logger.warn("Amount of arguments of the greatest case:" + str(len(max_ans.args_p.union(max_ans.args_not_p))))
    logger.warn("Arguments of the greatest case:")
    for arg in [ag.cache for ag in max_res["system"].agents.values()]:
        logger.warn(arg)

    logger.info("Statistics for amount of arguments in answers:")

    # logger.info("Average size of arguments: "+ str(sum(arg_sizes) / len(arg_sizes)))
    # logger.info("Min size of arguments: "+ str(min(arg_sizes)))
    # logger.info("Max size of arguments: "+ str(max(arg_sizes)))

    arg_sizes_array = np.asarray(amount_arguments_per_ans)
    df_describe = pd.DataFrame(arg_sizes_array)
    logger.warn(df_describe.describe().astype(str))

    # print(ans.tv_p)
    # logger.info(str(ans.tv_p)+"\n")


asyncio.run(perform_queries())

    
