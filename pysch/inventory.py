import sys
import os
from typing import List
from .log_config import get_logger
import logging
from .common import flatten_log_msg

from yaml import load as yaml_load
try:
    from yaml import CLoader as YamlLoader
except ImportError:
    from yaml import Loader as YamlLoader

logger = get_logger(__name__)
console_logger = get_logger('console_logger')

class Inventory():

    def __init__(self, inventory_file) -> None:
        # inventory_path = os.path.abspath(inventory_file)
        inventory_path = os.path.expanduser(inventory_file)
        # yaml.
        try:
            with open(inventory_path, 'r') as f:
                self.inventory_dict = yaml_load(f, YamlLoader)
        except Exception as e:
            console_logger.error(flatten_log_msg(e))
            console_logger.error('Exiting')
            sys.exit(1)

        self.hosts = []
        self.groups = []
        for item in self.inventory_dict:
            if isinstance(self.inventory_dict[item], dict):
                self.hosts.append(item)
            elif isinstance(self.inventory_dict[item], list):
                self.groups.append(item)

        self._flat = self._flatten()

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
        return do_flat(self.inventory_dict)

    @property
    def flat(self):
        return self._flat
        
        

# if __name__ == '__main__':
#     # inv = Inventory('/Users/ivanb/dev/pyssh/inventory.yaml')
#     inv = Inventory('../inventory.yaml')
    # print(inv.groups)

#     from pprint import PrettyPrinter
#     pp = PrettyPrinter(indent=4)
#     pp.pprint(inv.inventory_dict)

#     pp.pprint(inv.inventory_dict['nas'])

#     pp.pprint(inv.groups)
#     pp.pprint(inv.hosts)