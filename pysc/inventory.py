import sys
import yaml
import log_config
import logging

logger = log_config.get_logger(__name__)

class Inventory():

    def __init__(self, inventory_file) -> None:
        try:
            with open(inventory_file, 'r') as f:
                self.inventory_dict = yaml.load(f, yaml.Loader)
        except FileNotFoundError as e:
            logger.error(e)
            sys.exit(1)

        self.hosts = []
        self.groups = []
        for item in self.inventory_dict:
            print(item)
            if isinstance(self.inventory_dict[item], dict):
                self.hosts.append(item)
            elif isinstance(self.inventory_dict[item], list):
                self.groups.append(item)

if __name__ == '__main__':
    inv = Inventory('/Users/ivanb/dev/pyssh/inventory.yaml')

#     from pprint import PrettyPrinter
#     pp = PrettyPrinter(indent=4)
#     pp.pprint(inv.inventory_dict)

#     pp.pprint(inv.inventory_dict['nas'])

#     pp.pprint(inv.groups)
#     pp.pprint(inv.hosts)