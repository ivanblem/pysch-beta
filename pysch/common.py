import functools
import os

import logging
import logging.config
import sys
import yaml


def get_local_terminal_size():
    """"""
    term_size = os.get_terminal_size()
    return term_size.columns, term_size.lines


def get_local_terminal_type():
    return os.getenv('TERM')


def flatten_log_msg(msg):
    return str(msg).replace('\n', ', ')


def singlton_class(cls):
    instance = None

    @functools.wraps(cls)
    def inner(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance

    return inner


def flat_inventory(inv):
    pass


def configure_logging() -> None:

    try:
        with open('config.yaml', 'r') as f:
            conf_dict = yaml.load(f, yaml.Loader)
    except Exception as e:
        # logger.error(fle)
        print(e)
        sys.exit(1)

    logging.config.dictConfig(conf_dict['logging'])
