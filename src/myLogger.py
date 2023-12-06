# encoding: utf-8

import logging
import os

"""
see https://stackoverflow.com/questions/10706547/add-encoding-parameter-to-logging-basicconfig"""
logger = logging.getLogger("adfc")
try:
    _ = os.environ["DEBUG"]
    lvl = logging.DEBUG
except:
    lvl = logging.ERROR
logger.setLevel(lvl)  # or whatever
logFileName = "adfc.log"
logFilePath = os.path.abspath(logFileName)
handler = logging.FileHandler(logFileName, 'w', 'utf-8')  # need utf encoding
# formatter = logging.Formatter(style="$", datefmt="%d.%m %H:%M:%S", fmt="${asctime} ${levelname} ${filename}:${funcName}:${lineno} ${message}")
formatter = logging.Formatter(datefmt="%d.%m %H:%M:%S",
                              fmt="%(asctime)s %(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s")
handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
logger.addHandler(handler)
logger.info("cwd=%s", os.getcwd())
