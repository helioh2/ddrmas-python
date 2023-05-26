
import string

from dataclasses import dataclass
from ddrmas_python.models.Agent import Agent

from ddrmas_python.models.System import System


def agent_name_generator():
    
    cont = 1
    while True:
        for letter in string.ascii_lowercase:
            yield letter + str(cont)
        cont += 1


@dataclass
class RandomDDRMASTester:

    agentsNumber: int
    literalsNumber: int
    rootLiteralsPercentage: float
    sslPercentage: float
    cyclePercentage: float
    highSimilarityProbability: float
    system: System = None


    def create_system(self):

        self.system = System()
        agents = []
        for k in range(self.agentsNumber):
                       

            # agent = Agent(next(agent_name_generator()), self.system, )


