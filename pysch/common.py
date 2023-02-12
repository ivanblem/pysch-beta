import functools
import os

import logging
import logging.config
import sys
import yaml

DEFAULT_CONFIG_DIR = os.path.expanduser('~/.config/pysch')
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR + '/config.yaml'
DEFAULT_INVENTORY_FILE = DEFAULT_CONFIG_DIR + '/inventory.yaml'
DEFAULT_PWDDB_FILE = DEFAULT_CONFIG_DIR + '/pwddb.kdbx'
DEFAULT_PWDDB_KEY = DEFAULT_CONFIG_DIR + '/pwddb.keyx'

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'simple': {
            'format': '%(levelname)s - %(message)s'
        },
        'pysc_default': {
            'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'log_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'pysc_default',
            'filename': 'pysch.log'
        }
    },
    'loggers': {
        'console_logger': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': True
        },
        'pysch': {
            'level': 'DEBUG',
            'handlers': ['log_file'],
            'propagate': True
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['log_file']
    },
    'disable_existing_loggers': False
}


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


def configure_logging(loglevel) -> None:

    try:
        with open(DEFAULT_CONFIG_FILE, 'r') as f:
            conf_dict = yaml.load(f, yaml.Loader)
    except Exception as e:
        print(e)
        sys.exit(1)

    try:
        logging_config = conf_dict['logging']
    except KeyError:
        logging_config = DEFAULT_LOGGING_CONFIG

    try:
        for logger in logging_config['loggers']:
            logging_config['loggers'][logger]['level'] = loglevel
        logging_config['root']['level'] = loglevel
    except Exception:
        print('Cannot set logging level. Plese check the configuration.')
        sys.exit(1)

    logging.config.dictConfig(logging_config)
