import sys
from typing import List

import click
import paramiko
from pykeepass import PyKeePass
# from pykeepass.exceptions import CredentialsError

from .common import get_local_terminal_size, get_local_terminal_type
from .config import Config
from .interactive import interactive_shell
from .inventory import Inventory
from .log_config import get_logger


console_logger = get_logger('console_logger')

# TODO ~/.config/pysc/config.yaml
DEFAULT_CONFIG_FILE = 'config.yaml'

# class CLICommand():

#     def __init__(self) -> None:
#         pass
#     def run(self):
#         pass


@click.group()
def cli():
    pass


@cli.command(help='Connect to the host')
@click.argument('host')
def connect(host):
    click.echo('Connecting to the {}'.format(host))
    PyscCLI().connect(host)
    # pysc_cli = PyscCLI()
    # pysc_cli.connect(host)


@cli.command(help='Get list of hosts')
def list_hosts():
    click.echo('Available hosts:')
    PyscCLI().list_hosts()
    # pysc_cli = PyscCLI()
    # pysc_cli.list_hosts()


@cli.command(help='Get list of credendials')
def list_credentials():
    click.echo('Available credentials:')
    PyscCLI().list_credentials()
    
class PyscCLI():

    def __init__(self, config_file=DEFAULT_CONFIG_FILE) -> None:
        self.config = Config(config_file)

        try:
            self._inventory = Inventory(self.config.inventory_file)
        except AttributeError:
            console_logger.error('No inventory file provided!')
            sys.exit(1)

        try:
            self.pwddb = PyKeePass(
                self.config.keepass_db_file,
                keyfile=self.config.keepass_key_file
            )
        except FileNotFoundError as e:
            console_logger.error(str(e))
            # logger.exception(e)
            sys.exit(1)
        # except CredentialsError as e:
        #     console_logger.error(str(e)
        #     sys.exit(1)

    @property
    def inventory(self):
        if not hasattr(self, '_inventory'):
            self._inventory = Inventory(self.inventory_file)
        return self._inventory

    def list_hosts(self) -> List:
        for host in self.inventory.flat:
            print(host)

    def list_credentials(self) -> List:
        for entry in self.pwddb.entries:
            print(entry)

    def connect(self, target_host):
        self.target_host = target_host
        if target_host in self.inventory.flat:
            item_path = target_host.split('/')
            # self.connection_config = self.inventory_dict[]
            connection_config = self.inventory.inventory_dict[item_path[0]]
            if len(item_path) > 1:
                for item in item_path[1:]:
                    connection_config = connection_config[item]

        if 'credentials' in connection_config.keys():
            credentials = self.pwddb.find_entries_by_title(
                connection_config['credentials'],
                first=True
            )
            try:
                connection_config['username'] = credentials.username
                connection_config['password'] = credentials.password
                connection_config.pop('credentials')
            except AttributeError as e:
                console_logger.error(str(e))

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        # logger.info('connecting to '+self.config['hostname'])
        # logger.info('connecting to '+self.config['hostname'])
        # TODO: deal with BadHostKeyException
        # better to check it in advance even
        # client.load_system_host_keys
        # paramiko.HostKeys
        client.connect(**connection_config)

        t = client.get_transport()
        channel = t.open_session()

        try:
            channel.get_pty(
                get_local_terminal_type(),
                *get_local_terminal_size()
            )
            channel.invoke_shell()
        except Exception as err:
            console_logger.error(str(err))
            sys.exit(1)

        interactive_shell(channel)
