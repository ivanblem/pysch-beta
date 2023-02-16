import logging
import os
import sys
from typing import List
from random import randbytes
from hashlib import sha256

import click
from lxml import etree
import paramiko
import pykeepass
# from pykeepass.exceptions import CredentialsError
from yaml import dump as yaml_dump
try:
    from yaml import CDumper as YamlDumper
except ImportError:
    from yaml import Dumper as YamlDumper

from .common import (
    get_local_terminal_size,
    get_local_terminal_type,
    configure_logging,
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_INVENTORY_FILE,
    DEFAULT_PWDDB_FILE,
    DEFAULT_PWDDB_KEY
)
from .config import Config
from .interactive import interactive_shell
from .inventory import Inventory


console_logger = logging.getLogger('console_logger')
logger = logging.getLogger(__name__)


@click.group()
@click.option('--loglevel', '-l',
              type=click.Choice(
                  ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                  case_sensitive=False),
              default='ERROR')
def cli(loglevel):
    configure_logging(loglevel)
    pass


@cli.command(help='Create initial config and inventoty')
def init():
    click.echo()
    if not os.path.exists(DEFAULT_CONFIG_DIR):
        os.makedirs(DEFAULT_CONFIG_DIR)
    if os.path.exists(DEFAULT_CONFIG_FILE):
        click.echo('File {} exists. Use --force ro override.'. format(
            DEFAULT_CONFIG_FILE
        ))
    else:
        with open(DEFAULT_CONFIG_FILE, 'w') as config_file:
            yaml_dump(
                {
                    'inventory_file': DEFAULT_INVENTORY_FILE,
                    'keepass_db_file': DEFAULT_PWDDB_FILE,
                    'keepass_key_file': DEFAULT_PWDDB_KEY,
                },
                config_file,
                YamlDumper
            )

        with open(DEFAULT_INVENTORY_FILE, 'w') as inventory_file:
            yaml_dump(
                {
                    'localhost': {
                        'hostname': '127.0.0.1',
                        'credentials': 'my_credentials',
                    },
                    'my_group': {
                        'my-host-1': {
                            'hostname': '192.168.1.2',
                            'credentials': 'my_password',
                        },
                        'my-host-2': {
                            'hostname': 'server.local',
                            'credentials': 'my_server_password',
                        },
                    },
                },
                inventory_file,
                YamlDumper
            )

        key_bytes = randbytes(32)
        key_hex = key_bytes.hex().upper()
        key_hash = sha256(key_bytes).digest()[:4].hex().upper()
        with open(DEFAULT_PWDDB_KEY, 'wb') as key_file:
            xml_key = etree.XML('<KeyFile><Meta><Version>2.0</Version></Meta>\
                <Key><Data Hash="{}">{}</Data></Key></KeyFile>'.format(
                    key_hash,
                    key_hex
                )
            )
            etree.indent(xml_key)
            xml_tree = etree.ElementTree(xml_key)
            xml_tree.write(
                key_file,
                xml_declaration=True,
                encoding='utf-8',
                pretty_print=True
            )

        pykeepass.create_database(
            DEFAULT_PWDDB_FILE,
            keyfile=DEFAULT_PWDDB_KEY
        )

        click.echo('Default configuration has been saved at {}'.format(
            DEFAULT_CONFIG_DIR
        ))


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
        for host in self.inventory._flat:
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
