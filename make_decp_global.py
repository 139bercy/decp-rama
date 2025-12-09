from general_process.GlobalProcess import GlobalProcess
import augmente.utils
import logging

logger = logging.getLogger()
logger.handlers.clear()
logger.setLevel(logging.INFO)


gp = GlobalProcess('2022',None)
gp.generate_global()
