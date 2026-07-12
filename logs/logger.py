import logging
import sys

def build_logger(name: str = "etl"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        h.setFormatter(fmt)
        logger.addHandler(h)

    return logger