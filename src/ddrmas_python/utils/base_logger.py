
import logging


logging.basicConfig(filename="execution.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


logging.info("Agent Query Logging")

logger = logging.getLogger('agentQuery')