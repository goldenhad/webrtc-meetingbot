import os
import logging
from datetime import datetime
from enum import Enum

from constants import INFO, ERROR

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler
log_file = 'log.txt'

# Clear the log file on restart
if os.path.exists(log_file):
    os.remove(log_file)
file_handler = logging.FileHandler(log_file)

# Create a formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)


# Log function
def _log(text,type = INFO):
    if type == INFO:
        logger.info(text)
    elif type == ERROR:
        logger.error(text)
    else:
        logger.info(text)



