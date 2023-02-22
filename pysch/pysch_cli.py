import logging
import os
import sys
from typing import List

import paramiko
import pykeepass

from .common import (
    get_local_terminal_size,
    get_local_terminal_type,
    DEFAULT_CONFIG_FILE,
)
from .config import Config
from .interactive import interactive_shell
from .inventory import Inventory

console_logger = logging.getLogger('console_logger')
logger = logging.getLogger(__name__)


class PyscCLI():

    def __init__(self, config_file=DEFAULT_CONFIG_FILE) -> None:
        self.config = Config(config_file)

        try:
            self._inventory = Inventory(self.config.inventory_file)
            logger.debug('Loaded inventory from file ' +
                         self.config.inventory_file)
        except AttributeError:
            console_logger.error('No inventory file provided!')
            sys.exit(1)

        try:
            self.pwddb = pykeepass.PyKeePass(
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
        for host in self.inventory:
            print(host)

    def list_credentials(self) -> List:
        for entry in self.pwddb.entries:
            print(entry)

    def connect(self, target_host):
        self.target_host = target_host
        connection_config = self.inventory.get_host(self.target_host)
        if not connection_config:
            sys.exit(1)

        credentials = self.pwddb.find_entries_by_title(
            connection_config['credentials'],
            first=True
        )
        if not credentials:
            console_logger.error(
                'Credentials "{}" not found'.format(
                    connection_config['credentials']
                )
            )
            sys.exit(1)
        try:
            connection_config['username'] = credentials.username
            connection_config['password'] = credentials.password
            connection_config.pop('credentials')
        except AttributeError as e:
            console_logger.error(str(e))
            console_logger.error(
                'Please check the credentials "{}" config'.format(credentials)
            )
            sys.exit(1)

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        # logger.debug('Host keys:')
        # logger.debug(client._system_host_keys.keys())
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

        for var_name, var_value in os.environ.items():
            if var_name.startswith('LC_') or var_name == 'LANG':
                channel.set_environment_variable(var_name, var_value)

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
