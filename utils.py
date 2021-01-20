import logging


def setup_log(name, usage=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if usage == "local":
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger
