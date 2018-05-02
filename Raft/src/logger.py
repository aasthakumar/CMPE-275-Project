import logging
import sys

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.NOTSET)

logger = logging.getLogger('client')

def get_logger():
    if(not rootLogger.hasHandlers()):
        setup_logging()
    return logger
    

def setup_logging():
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('[%(levelname)-.1s] %(asctime)s | %(message)s'))
    rootLogger.addHandler(handler)
    
    
