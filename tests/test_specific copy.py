
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
from ddrmas_python.services.load_system_from_file import load_system_from_file, load_system_from_yaml_str
from ddrmas_python.services.print_system import print_system

from ddrmas_python.utils.base_logger import logger

import signal
import traceback

from conftest import print_similarities



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



        


##TESTE:

def handler(signum, frame):
    print("Demorou demais!!")
    raise Exception("end of time")



async def perform_queries():
    
    results = []

    for k in range(1):

        system = load_system_from_file("test2.yml")

        p = LLiteral(
                definer=system.agents["a1"], 
                literal=Literal(True, "af1", ["M"])
                )
        
        """
        (b1, ab1['M']) by b1 with focus rules: 
        (F, ac1['M']) <= 
        (F, aa1['M']) <= 
        (F, ae1['M']) <= 
        """
        queryfocus = QueryFocus("alfa1", 
                                p,
                                emitter_agent=system.agents["a1"],
                                kb=[
                                     Rule("r_alfa1", LLiteral(Sign.FOCUS, Literal(False, "ae1", ["M"]))),
                                     Rule("r_alfa2", LLiteral(Sign.FOCUS, Literal(True, "ah1", ["M"]))),
                                     Rule("r_alfa3", LLiteral(Sign.FOCUS, Literal(True, "ad1", ["M"]))),
                                ]
        )

        # signal.signal(signal.SIGALRM, handler)

        # signal.alarm(10)

        # tester = RandomDDRMASTester(
        #     agentsNumber=20, 
        #     literalsNumber=100, 
        #     rulesNumber=300, 
        #     sslPercentage=0.8, 
        #     cyclePercentage=0,
        #     similarityPercentage=0.1

                
        print("\n\n\n--------query\n\n")

        ans = None
        try:
            ans = await system.agents["a1"].query(p, queryfocus, [])
        except Exception as exc:
            traceback.print_exc()
            logger.error(exc)


        print(ans)

       
       


asyncio.run(perform_queries())

    
