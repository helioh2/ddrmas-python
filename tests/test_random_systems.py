
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
from ddrmas_python.models.Agent import Agent, MaxArgsExceededException
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
    visited = set()
    for lit1, rlits in sim_dict.items():
        for lit2 in rlits:
            if lit1 == lit2 or not lit1.positive or (lit1,lit2) in visited or (lit2, lit1) in visited:
                continue
            if sim_dict[lit1][lit2] != 0:
                str_ += f"theta({str(lit1)}, {str(lit2)}) = {str(sim_dict[lit1][lit2])}\n"
                visited.add((lit1, lit2))

    return str_


def print_similarities(sim_dict):
    # print("Similarities: ")
    logger.info("Similarities: ")
    # print(sim_to_str(sim_dict))




@dataclass
class RandomDDRMASTester:

    agentsNumber: int
    literalsNumber: int
    rulesNumber: int
    sslPercentage: float
    hasCycles: bool
    similarityPercentage: float
    maxBodySize: int
    maxHeight: int = 10000000
    similarity_function = lambda a, b: 1 if a==b or random.random() <= 0.1 else 0
    similarity_between_literals: dict = field(default_factory=dict)
    system: System = None
    focus_name_gen = focus_name_generator()
    literals: list[Literal] = field(default_factory=list)
    cycles_count: int = 0
    

    def create_system(self) -> System:

        self.system = System(sim_threshold=1, max_argument_height=self.maxHeight )

        self.cycles_count = 0

        self.system.agents = {}
        self.literals = []
        # rules = []
        agents_last_rule_numbers = {}

        agent_name_gen = agent_name_generator()
        literal_name_gen = literal_name_generator()

        

        for _ in range(self.agentsNumber):
            agent = Agent(next(agent_name_gen), self.system)
            self.system.agents[agent.name] = agent
            agents_last_rule_numbers[agent.name] = 1

        for agent, trusted_agent in product(self.system.agents.values(), self.system.agents.values()):
            if agent == trusted_agent:
                agent.trust[trusted_agent] = 1
            else:
                agent.trust[trusted_agent] = random.random()

        for _ in range(self.literalsNumber):
            self.literals.append(Literal(positive=True, pred=next(literal_name_gen), terms=["M"]))


        self.similarity_between_literals = {literal: {} for literal in 
                                       self.literals + [lit.negated() for lit in self.literals]}
        
        pairs = set()
        max_combinations = int((math.factorial(len(self.literals))/(2*(math.factorial(len(self.literals)-2))))*self.similarityPercentage)
        for i in range(max_combinations):
            lit1 = random.choice(self.literals)
            lit2 = random.choice(self.literals)

            while lit1 == lit2 or (lit1, lit2) in pairs or (lit2, lit1) in pairs:
                lit1 = random.choice(self.literals)
                lit2 = random.choice(self.literals)

            pairs.add((lit1, lit2))

        #ex: 10 literais. 45 combinações máximas. 10% de similaridade = 4 pares de literais
        #ex: 10 literais. 45 combinações máximas. 100% de similaridade = 45 pares de literais

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
                if (literal1, literal2) in pairs or (literal2, literal1) in pairs:
                    sim = 1

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

        body_length_count = 0

        agents_list = list(self.system.agents.values())
        random.shuffle(agents_list)
        current_agent_index = 0
        k = 0
        while k < self.rulesNumber:
            definer_agent:Agent = agents_list[current_agent_index]
            
            head_literal = random.choice(self.literals)
            head_literal_copy = Literal(True if random.randrange(0,2)==0 else False, head_literal.pred, head_literal.terms) 
            head_lliteral = LLiteral(definer_agent, head_literal_copy)

            body_length = body_length_count
            
            body_lliterals = []
            used_literals = {head_literal_copy}
            for _ in range(body_length):

                literal = random.choice(self.literals)
                literal_copy = Literal(True if random.randrange(0,2)==0 else False, literal.pred, literal.terms) 
                while literal_copy in used_literals:
                    literal = random.choice(self.literals)
                    literal_copy = Literal(True if random.randrange(0,2)==0 else False, literal.pred, literal.terms) 
                
                
                used_literals.add(literal_copy)


                is_ssl = random.random() <= self.sslPercentage
                if is_ssl:
                    definer = Sign.SCHEMATIC
                else:
                    definer = random.choice(list(self.system.agents.values()))
                
                body_lliterals.append(LLiteral(definer, literal_copy))


            rule_name = "r_" + definer_agent.name + str(agents_last_rule_numbers[definer_agent.name])
            agents_last_rule_numbers[definer_agent.name] += 1
            rule = Rule(rule_name, head_lliteral, set(body_lliterals), RuleType.DEFEASIBLE)

            if rule in definer_agent.kb:
                continue
            
            else:

                rule, rules_to_remove = self.check_rule(definer_agent.kb, rule)

                if not rule:
                    continue
                
                will_add = True
                for r in rules_to_remove:
                    if r == rule:
                        will_add = False
                        continue
                    definer_agent.kb.remove(r)
                    # body_length_count = len(r.body)
                    k -= 1
                    
                if will_add:
                    definer_agent.kb.add(rule)
                else:
                    continue
             

            k += 1
            body_length_count = (body_length_count + 1) % (self.maxBodySize+1)  #distribuição igual de regras com corpo de tamanho 0, 1 ou 2
            current_agent_index = (current_agent_index + 1) % len(agents_list)
            if current_agent_index == 0:
                random.shuffle(agents_list)

        logger.info(f"System:\n{self.system}")
        
        return self.system
    


    def check_rule(self, kb: list[Rule], new_rule: Rule):
        """
        test if new rule introduces some kind of reduncancy, and updates
        kb as necessary
        """

        def remove_body_members_which_are_redundant_or_conflicting(new_rule: Rule):
            """
            Ex: r_a16: (a1, aa1['M']) <= (@, ac1['M']), (a1, ac1['M'])  // keep only (@, ac1['M'])

            """ 
            # to_remove = set()
            # for bm1 in new_rule.body:
            #     for bm2 in new_rule.body:
            #         if bm1 != bm2 and bm1.has_equivalent_positive_literal(bm2, self.system.sim_function, self.system.sim_threshold):
            #             if bm1.definer == Sign.SCHEMATIC:
            #                 to_remove.add(bm2)
            #             elif bm2.definer == Sign.SCHEMATIC:
            #                 to_remove.add(bm1)

            # for bm in to_remove:
            #     new_rule.body.remove(bm)

            # return new_rule

            to_remove = set()
            for bm1 in new_rule.body:
                for bm2 in new_rule.body:
                    if bm1 != bm2 and bm1.has_equivalent_positive_literal(bm2, self.system.sim_function, self.system.sim_threshold):
                        return None
            return new_rule
      


        def remove_more_specific_rule_when_general_exists(new_rule_aux: Rule):
            """
            Ex: 
            (a1, aa1['M']) <= (@, ~ab1['M']), (@, ac1['M'])  // keep this
            (a1, aa1['M']) <= (a1, ~ab1['M']), (@, ac1['M'])


            """
            if not new_rule_aux:
                return None, set()
            mod_rule = Rule(name=new_rule_aux.name, head=new_rule_aux.head, type=new_rule_aux.type)
            for rule in kb:
                if rule.head.literal == new_rule_aux.head.literal and len(rule.body) == len(new_rule_aux.body) and rule.type == new_rule_aux.type:
                    for bm in rule.body:
                        for bm_new in rule.body:
                            if bm.literal == bm_new.literal:
                                if bm.definer == Sign.SCHEMATIC:
                                    mod_rule.body.add(bm)
                                else:
                                    mod_rule.body.add(bm_new)
                                break
                    if len(new_rule_aux.body) == len(mod_rule.body):
                        return mod_rule, {rule}
                    #else
                    mod_rule.body.clear()
                    
            return new_rule_aux, set()




        def remove_rules_whose_body_is_a_superset_of_other(new_rule_aux: Rule):
            """
            Ex:
            (a1, aa1['M']) <= (@, ~ab1['M'])
            (a1, aa1['M']) <= (@, ~ab1['M']), (@, ac1['M']) //remove this
            (a1, aa1['M']) <= (@, ac1['M'])
            """
            if not new_rule_aux:
                return None, set()
            to_remove = set()
            for rule in kb:
                if rule.head.literal == new_rule_aux.head.literal:
                    if rule.body.issubset(new_rule_aux.body):
                        return None, {}  #do not add new_rule_aux
                    elif new_rule_aux.body.issubset(rule.body):
                        to_remove.add(rule)
            
            return new_rule_aux, to_remove
                    


        def remove_rule_if_introduces_cycle(new_rule_aux: Rule):
            
            def has_cycle_backwards(kb: set[Rule], chain: tuple[Rule]):
                for rule_kb in kb:  # para cada regra da kb
                    if rule_kb in chain:
                        continue
                    
                    for bm in chain[-1].body:  # para cada membro do corpo do último da cadeia

                        if rule_kb.head.equivalent_to(bm, self.system.sim_function, self.system.sim_threshold):  # se a cabeça da regra "bate" com o membro do corpo do último da cadeia
                             # achou regra de ligação (rule_kb)
                            for b in rule_kb.body:  # para cada membro do corpo da regra da kb
                                for rule in chain:
                                    if b.has_equivalent_positive_literal(rule.head, self.system.sim_function, self.system.sim_threshold):
                                        # se algum membro do corpo da regra da kb é equivalente à cabeça de alguma regra na cadeia
                                        #ciclo encontrado
                                        return True

                            res = has_cycle_backwards(kb.difference({rule_kb}), chain + (rule_kb,))
                            if res:  # encontrou ciclo em algum ponto
                                return res
                return False
                         

            def has_cycle_forward(kb: set[Rule], chain: tuple[Rule]):
                for rule_kb in kb:  # para cada regra da kb
                    if rule_kb in chain:
                        continue
                    
                    for bm in rule_kb.body:  # para cada membro do corpo da regra da kb

                        if bm.equivalent_to(chain[-1].head, System.sim_function, System.sim_threshold):  # se a cabeça da última regra da cadeia "bate" com o membro do corpo da regra da kb
                            # achou regra de ligação (rule_kb)
                            chain_bodies = set()
                            for rule in chain:
                                chain_bodies.update(rule.body)
                            for b in chain_bodies:  # para cada membro do corpo das regras da cadeia
                                if b.has_equivalent_positive_literal(rule_kb.head, System.sim_function, System.sim_threshold):  # se algum membro do corpo das regras da cadeia "bate" com a cabeça da regra da kb
                                    #ciclo encontrado
                                    return True

                            res = has_cycle_forward(kb.difference({rule_kb}), chain + (rule_kb,))
                            if res:  # encontrou ciclo em algum ponto
                                return res
                return False


            if not new_rule_aux:
                return None
            
            for bm in new_rule_aux.body:
                if new_rule_aux.head.has_equivalent_positive_literal(bm, self.system.sim_function, self.system.sim_threshold):
                    return None

            if self.hasCycles:
                return new_rule_aux
            
            # max_cycles = int(self.rulesNumber * self.cyclePercentage)
            

            

            # for rule in set().union(agent.kb for agent in self.system.agents.values()):
            #     ## check head with body of others:

            
            global_kb = set()
            for agent in self.system.agents.values():
                global_kb.update(agent.kb)

            if (has_cycle_backwards(global_kb,
                                    chain=(new_rule_aux,)) or
                has_cycle_forward(global_kb,
                                 chain=(new_rule_aux,))):
                    return None
        
            return new_rule_aux
                

        rules_to_remove = set()

        new_rule = remove_body_members_which_are_redundant_or_conflicting(new_rule)
        new_rule, to_remove = remove_more_specific_rule_when_general_exists(new_rule)
        rules_to_remove.update(to_remove)
        new_rule, to_remove = remove_rules_whose_body_is_a_superset_of_other(new_rule)
        rules_to_remove.update(to_remove)
        new_rule = remove_rule_if_introduces_cycle(new_rule)
        return new_rule, rules_to_remove

        
    async def do_random_query(self, focus_kb_side = 0):

        literal = random.choice(self.literals)
        emitter_agent = random.choice(list(self.system.agents.values()))
        lliteral = LLiteral(emitter_agent, literal)

        focus_name = next(self.focus_name_gen)
        focus_kb = []
        focus_rule_number = 1
        for k in range(focus_kb_side):

            head_literal = random.choice(self.literals)
            while literal == head_literal or head_literal in (r.head for r in focus_kb):
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
    
        # try:
        ans = await emitter_agent.query(lliteral, focus, [])
        # except Exception as exc:
        #     exc2 = Exception(focus)
        #     raise exc2
        
        return ans, focus
        # for arg in ans.args_p:
        #     print(str(arg))
        #     logger.info(str(arg))
        

   

##TESTE:

def handler(signum, frame):
    print("Demorou demais!!")
    raise Exception("end of time")



# def results_loader():

#     for _ in range(TIMES_RUN):
#         with open('results.pkl', 'rb') as f:
#             yield pickle.load(f)


def complete_dot(string: str):
    antes = '''
        strict digraph g {
        fontname="Helvetica,Arial,sans-serif"
        node [fontname="Helvetica,Arial,sans-serif"]
        edge [fontname="Helvetica,Arial,sans-serif"]
        graph [
        rankdir = "UD"
        ];
        node [
        fontsize = "16"
        shape = "ellipse"
        ];
        edge [
        ];\n
        '''
    
    return antes + string + "}"


async def perform_queries():
    
    results = []

    logger.setLevel("WARNING")

    exec_times = []

    if os.path.isfile("results.pkl"):
        os.remove("results.pkl")

    timesRun = 2000
    actualTimesRun = 0

    agentsNumber=20 
    literalsNumber=20
    rulesNumber=50
    sslPercentage=1
    hasCycles=True
    similarityPercentage=0.1
    maxBodySize=3
    focusKbSize=3


    # agentsNumber=5 
    # literalsNumber=5
    # rulesNumber=10
    # sslPercentage=1
    # hasCycles=False
    # similarityPercentage=0.1
    # maxBodySize=2
    # focusKbSize=1

    for k in range(timesRun):

        tester = RandomDDRMASTester(
            agentsNumber=agentsNumber, 
            literalsNumber=literalsNumber, 
            rulesNumber=rulesNumber, 
            sslPercentage=sslPercentage, 
            hasCycles=hasCycles,
            similarityPercentage=similarityPercentage,
            maxBodySize=maxBodySize
        )

        # signal.signal(signal.SIGALRM, handler)

        # signal.alarm(15)

        tester.create_system()
        # print_system(tester.system)
                
        # print("\n\n\n--------query\n\n")
        ans, query_focus = None, None
        start_time = time.time()
        try:
            ans, query_focus = await tester.do_random_query(focusKbSize)
        except MaxArgsExceededException as exc:
            traceback.print_exc()
            # logger.error(exc)
            query_focus = exc.query_focus
            continue
            # args = exc.args
            
            # logger.warning("System:")
            # logger.warning(str(tester.system))
            # logger.warning(str(query_focus))
            # for arg in args:
            #     logger.warning(str(arg))

            # with open("args.dot", "w") as f:
            #     f.write(complete_dot(str("".join(args))))
            
            # return

        except Exception as exc:
            traceback.print_exc()
            logger.error(exc)
            query_focus = exc.args[0]
            continue

        end_time = time.time()

        


        # results.append({"system": tester.system, "answer": ans})

        agents = tester.system.agents.values()
        all_args = set()
        for agent in agents:
            for cached in agent.cache_args.values():
                if cached.done():
                    all_args.update([arg for arg in cached.result()[0]])
                    all_args.update([arg for arg in cached.result()[1]])
        

        if all_args:
            print("tem args")
            exec_times.append(end_time-start_time)


            with open('results.pkl', 'ab') as f:
                pickle.dump(
                    {
                        "all_args": [arg.to_graph() for arg in all_args], 
                        "len(all_args)":str(len(all_args)),
                        "query_focus": str(query_focus),
                        "sizes_messages": tester.system.size_messages_answers,
                        # "tv": ans.tv_p,
                        "system": str(tester.system),
                        "similarities": sim_to_str(tester.similarity_between_literals),
                        "messages_count": tester.system.amount_messages_exchanged,
                        "max_count":  tester.system.max_arguments_times
                    }, 
                    f)
                actualTimesRun += 1

        # logger.info("Answer: "+str(ans))
        # all_args = set()

    logger.warning("Config:")

    logger.warning("Times Run: "+str(timesRun))
    logger.warning("Agents Number: "+str(agentsNumber))
    logger.warning("Literals Number: "+str(literalsNumber))
    logger.warning("Rules Number: "+str(rulesNumber))
    logger.warning("ssl Percentage: "+str(sslPercentage))
    logger.warning("has cycles: "+str(hasCycles))
    logger.warning("similarity Percentage: "+str(similarityPercentage))
    


    # results = results_loader()

    amount_arguments_per_ans = []
    messages_exchanged_per_ans = []
    times_max_arguments_achieved = []
    avg_sizes_messages_answers = []
    max_sizes_messages_answers = []
    query_focuses_per_ans = []
    tvs_per_ans = []
    max_args_len = -1
    max_args = []
    max_system = None
    max_similarities = None
    max_query_focus = None
    try:
        with open('results.pkl', 'rb') as f:
            for k in range(actualTimesRun):
                
                res = pickle.load(f)

                total_args = int(res["len(all_args)"])
                # total_args = len(res["all_args"])

                if total_args == 0:  ## IGNORANDO QUANDO NAO HA ARGUMENTOS
                    continue

                if total_args >= max_args_len:
                    max_args_len = total_args
                    if "all_args" in res.keys():
                        max_args = res["all_args"]
                    max_system = res["system"]
                    max_similarities = res["similarities"]
                    max_query_focus = res["query_focus"]

                
                amount_arguments_per_ans.append(total_args)

                messages_exchanged_per_ans.append(res["messages_count"])
                times_max_arguments_achieved.append(res["max_count"])
                query_focuses_per_ans.append(res["query_focus"])
                if not res["sizes_messages"]:
                    avg_sizes_messages_answers.append(0)
                    max_sizes_messages_answers.append(0)
                else:
                    avg_sizes_messages_answers.append(sum(res["sizes_messages"])/len(res["sizes_messages"]))
                    max_sizes_messages_answers.append(max(res["sizes_messages"]))
                # tvs_per_ans.append(res["tv"])
    except:
        print(actualTimesRun)
        print("pickle error")

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

    
    # logger.warning("Arguments of the greatest case:")
    # for arg in max_args:
    #     logger.warning(arg)

    if max_args:
        with open("args.dot", "w") as f:
            f.write(complete_dot(str("".join(arg for arg in max_args))))

        

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


    arg_sizes_array = np.asarray(avg_sizes_messages_answers)
    df_describe = pd.DataFrame(arg_sizes_array)
    logger.warning("Average size of messages statistics:")
    logger.warning(df_describe.describe().astype(str))

    arg_sizes_array = np.asarray(max_sizes_messages_answers)
    df_describe = pd.DataFrame(arg_sizes_array)
    logger.warning("Max size of messages statistics:")
    logger.warning(df_describe.describe().astype(str))

asyncio.run(perform_queries())

    
