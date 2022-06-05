import logging

log_format = f"%(asctime)s [%(levelname)s] %(name)s (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(logging.Formatter(log_format))

    logger.addHandler(log_handler)

    return logger