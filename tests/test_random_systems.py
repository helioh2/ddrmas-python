
import asyncio
from itertools import product
import random
import string

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

        agents = []
        self.literals = []
        rules = []
        agents_last_rule_numbers = {}

        agent_name_gen = agent_name_generator()
        literal_name_gen = literal_name_generator()

        for _ in range(self.agentsNumber):
            agent = Agent(next(agent_name_gen), self.system)
            agents.append(agent)
            agents_last_rule_numbers[agent.name] = 1

        for agent, trusted_agent in product(agents, agents):
            if agent == trusted_agent:
                agent.trust[trusted_agent] = 1
            else:
                agent.trust[trusted_agent] = random.random()

        for _ in range(self.literalsNumber):
            self.literals.append(Literal(positive=True, pred=next(literal_name_gen), terms=["M"]))


        similarity_between_literals = {literal: {} for literal in 
                                       self.literals + [lit.negated() for lit in self.literals]}
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
                sim = 1 if random.random() <= self.similarityPercentage else 0
                similarity_between_literals[literal1][literal2] = sim
                similarity_between_literals[literal2][literal1] = sim
                similarity_between_literals[literal1_neg][literal2_neg] = sim
                similarity_between_literals[literal2_neg][literal1_neg] = sim

                similarity_between_literals[literal1][literal2_neg] = 0
                similarity_between_literals[literal2_neg][literal1] = 0
                similarity_between_literals[literal2][literal1_neg] = 0
                similarity_between_literals[literal1_neg][literal2] = 0


        self.system.sim_function = lambda a,b: similarity_between_literals[a.literal][b.literal]

        for _ in range(self.rulesNumber):
            definer_agent = random.choice(agents)
            head_literal = random.choice(self.literals)
            head_literal.positive = True if random.randrange(0,2)==0 else False
            head_lliteral = LLiteral(definer_agent, head_literal)

            body_length = random.randrange(0,3)
            
            body_lliterals = []
            for _ in range(body_length):

                literal = random.choice(self.literals)
                while literal == head_literal:
                    literal = random.choice(self.literals)
                literal.positive = random.randrange(0,2) == 0

                is_ssl = random.random() <= self.sslPercentage
                if is_ssl:
                    definer = Sign.SCHEMATIC
                else:
                    definer = random.choice(agents)
                
                body_lliterals.append(LLiteral(definer, literal))

            rule_name = "r_" + definer_agent.name + str(agents_last_rule_numbers[definer_agent.name])
            agents_last_rule_numbers[definer_agent.name] += 1
            rule = Rule(rule_name, head_lliteral, body_lliterals, RuleType.DEFEASIBLE)

            rules.append(rule)
            definer_agent.kb.add(rule)

        self.system.agents = agents

        logger.info(f"System:\n{self.system}")
        
        return self.system

        
    async def do_random_query(self, focus_kb_side = 0):

        literal = random.choice(self.literals)
        emitter_agent = random.choice(self.system.agents)
        lliteral = LLiteral(emitter_agent, literal)

        focus_name = next(self.focus_name_gen)
        focus_kb = []
        focus_rule_number = 1
        for _ in range(focus_kb_side):

            head_literal = random.choice(self.literals)
            while literal == head_literal:
                head_literal = random.choice(self.literals)
            head_lliteral = LLiteral(Sign.FOCUS, head_literal)
            
            rule_name = "r_" + focus_name + str(focus_rule_number)
            focus_rule_number += 1
            rule = Rule(rule_name, head_lliteral, [], RuleType.DEFEASIBLE)
            focus_kb.append(rule)

        
        focus = QueryFocus(focus_name, lliteral, emitter_agent, focus_kb)


        print("Query: ")
        print(focus)
        logger.info("Query: "+str(focus)+"\n")

        ans = await emitter_agent.query(lliteral, focus, [])

        print(ans.tv_p)
        logger.info(str(ans.tv_p)+"\n")


        # for arg in ans.args_p:
        #     print(str(arg))
        #     logger.info(str(arg))
        


##TESTE:

def handler(signum, frame):
    print("Demorou demais!!")
    raise Exception("end of time")



for k in range(1):

    tester = RandomDDRMASTester(
        agentsNumber=5, 
        literalsNumber=10, 
        rulesNumber=20, 
        sslPercentage=0.8, 
        cyclePercentage=0,
        similarityPercentage=0.05
    )

    """ 
    TODO: verificar o que se deseja registrar.
        - Quantidade e tamanho médio dos argumentos gerados
            - Uso de memória
            - Verificação da existência de argumentos repetidos ou muito similares
        - Tempo de execução médio
        - Quantidade de mensagens trocadas entre os agentes

    """

    signal.signal(signal.SIGALRM, handler)

    signal.alarm(20)

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

    try:
        asyncio.run(tester.do_random_query(3))
    except Exception as exc:
        traceback.print_exc()
        logger.error(exc)

