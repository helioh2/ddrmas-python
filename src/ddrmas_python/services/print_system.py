


import yaml
from ddrmas_python.models.System import System

from yaml import load

from ddrmas_python.services.load_system_from_file import load_system_from_file
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def print_system(system: System):
    
    agents_dict = {}

    for agent in system.agents:

        agents_dict[agent.name] = {"rules": {}, "trust": {}}

        for rule in agent.kb:
            agents_dict[agent.name]["rules"][rule.name] = str(rule)

        for trusted_ag, value in agent.trust.items():
            agents_dict[agent.name]["trust"][trusted_ag.name] = value

    print(yaml.dump(agents_dict))


# print_system(load_system_from_file("mushroom.yaml"))