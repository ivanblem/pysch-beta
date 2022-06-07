import logging
import logging.config
import yaml
import sys

log_format = f"%(asctime)s [%(levelname)s] %(name)s (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"

def get_logger(name):
    try:
        with open('config.yaml', 'r') as f:
            conf_dict = yaml.load(f, yaml.Loader)
    except Exception as e:
        # logger.error(fle)
        print(e)
        sys.exit(1)

    logging.config.dictConfig(conf_dict['logging'])
    logger = logging.getLogger(name)
    # logger.setLevel(logging.DEBUG)

    # log_handler = logging.StreamHandler()
    # log_handler.setLevel(logging.DEBUG)
    # log_handler.setFormatter(logging.Formatter(log_format))

    # logger.addHandler(log_handler)

    return logger