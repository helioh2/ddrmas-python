
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
from ddrmas_python.services.print_system import print_system


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
    cyclePercentage: float
    similarity_function = lambda a, b: 1 if a==b or random.random() <= 0.1 else 0
    system: System = None
    focus_name_gen = focus_name_generator()
    literals: list[Literal] = field(default_factory=list)
    

    def create_system(self) -> System:

        self.system = System(sim_function=self.similarity_function, sim_threshold=1)
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

        for _ in range(self.rulesNumber):
            definer_agent = random.choice(agents)
            head_literal = random.choice(self.literals)
            head_literal.positive = True if random.randrange(0,2)==0 else False
            head_lliteral = LLiteral(definer_agent, head_literal)

            body_length = random.randrange(0,4)
            
            body_lliterals = []
            for _ in range(body_length):

                literal = random.choice(self.literals)
                while literal == head_literal:
                    literal = random.choice(self.literals)
                literal.positive = True if random.randrange(0,2)==0 else False

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

        ans = await emitter_agent.query(lliteral, focus, [])

        print(ans)



        
##TESTE:
tester = RandomDDRMASTester(20, 100, 500, 0.8, 0)
print_system(tester.create_system())
        
print("\n\n\n--------query\n\n")

asyncio.run(tester.do_random_query(3))


