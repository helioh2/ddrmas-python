
import logging

import os
import shutil
import datetime

S = r"."
D = r"."

print(os.listdir(S))
print(os.listdir(D))

if os.path.isfile("execution.log"):
    path = shutil.copyfile("execution.log", f"execution_{str(datetime.datetime.now())}.log")
    os.remove("execution.log")

logging.basicConfig(filename="execution.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


logging.info("Agent Query Logging")

logger = logging.getLogger('agentQuery')