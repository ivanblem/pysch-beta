import logging
import os
import sys
from typing import List

from yaml import load as yaml_load
try:
    from yaml import CLoader as YamlLoader
except ImportError:
    from yaml import Loader as YamlLoader

logger = logging.getLogger(__name__)
console_logger = logging.getLogger('console_logger')

HOST_REQUIRED_FIELDS = {'hostname', 'credentials'}


class Inventory():

    def __init__(self, inventory_file) -> None:
        # inventory_path = os.path.abspath(inventory_file)
        inventory_path = os.path.abspath(os.path.expanduser(inventory_file))
        # yaml.
        try:
            with open(inventory_path, 'r') as f:
                self.inventory_dict = yaml_load(f, YamlLoader)
        except FileNotFoundError:
            console_logger.error('Inventory file not found. Exiting')
            sys.exit(1)

        self._flat = self._flatten_v2()

    def __len__(self):
        return len(self._flat)

    def __contains__(self, name):
        if name in self._flat.keys():
            return True
        return False

    def __iter__(self):
        return iter(self._flat)

    def __getitem__(self, hostname):
        host_config = self._flat.get(hostname, None)
        console_logger.debug('Got "{}" config: {}'.format(
            hostname,
            host_config)
        )
        if host_config:
            if (HOST_REQUIRED_FIELDS & set(host_config.keys()) !=
                    HOST_REQUIRED_FIELDS):
                missing_fields = (HOST_REQUIRED_FIELDS - (
                    HOST_REQUIRED_FIELDS & set(host_config.keys())
                ))
                console_logger.error(
                    'Host "{}" config is missing required fields {}'.format(
                        hostname, missing_fields
                    )
                )
                host_config = None
        else:
            console_logger.error(
                'Host "{}" not found!'.format(hostname)
            )
        return host_config

    def _flatten(self) -> List:
        flattened_dict = []

        def do_flat(d, prefix=''):
            new_prefix = prefix
            for k in d:
                if 'hostname' in d[k].keys():
                    flattened_dict.append(prefix+k)
                else:
                    new_prefix += k+'/'
                    do_flat(d[k], prefix=new_prefix)
                    new_prefix = prefix
            return flattened_dict

    def _flatten_v2(self) -> dict:
        flattened_dict = {}

        def do_flat(d, prefix=''):
            new_prefix = prefix
            for k, v in d.items():
                if isinstance(v, dict):
                    if all(map(lambda i: type(i) == dict, v.values())):
                        # node_type = 'group'
                        new_prefix += k+'/'
                        do_flat(d[k], prefix=new_prefix)
                        new_prefix = prefix
                    elif all(map(lambda i: type(i) != dict, v.values())):
                        # node_type = 'host'
                        flattened_dict[prefix+k] = v
                else:
                    console_logger.error(
                        'Incorrect node type: {}.'.format(k))
                    sys.exit(1)
            return flattened_dict

        return do_flat(self.inventory_dict)

    def get_host(self, hostname: str) -> dict:
        return self.__getitem__(hostname)
