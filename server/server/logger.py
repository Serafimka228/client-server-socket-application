import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_handler = logging.FileHandler("loggs\\debug.log", encoding="UTF-8")
logger_formatter = logging.Formatter(
    "%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logger_handler.setFormatter(logger_formatter)
logger.addHandler(logger_handler)
