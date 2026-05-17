import sys
from loguru import logger
from muse.utils.paths import get_log_file

def setup_logging(level="INFO"):
    logger.remove()
    logger.add(sys.stderr, level=level)
    logger.add(get_log_file(), rotation="10 MB", level="DEBUG")
