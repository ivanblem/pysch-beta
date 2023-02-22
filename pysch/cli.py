import logging
import os
from random import randbytes
from hashlib import sha256

import click
from lxml import etree
import pykeepass
# from pykeepass.exceptions import CredentialsError
from yaml import dump as yaml_dump
try:
    from yaml import CDumper as YamlDumper
except ImportError:
    from yaml import Dumper as YamlDumper

from .common import (
    configure_logging,
    DEFAULT_CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_INVENTORY_FILE,
    DEFAULT_PWDDB_FILE,
    DEFAULT_PWDDB_KEY
)

from .pysch_cli import PyscCLI

console_logger = logging.getLogger('console_logger')
logger = logging.getLogger(__name__)


@click.group()
@click.option(
    '--config', '-c',
    help='Path to configuration file',
    type=click.Path(exists=True),
    default=DEFAULT_CONFIG_FILE)
@click.option(
    '--loglevel', '-l',
    type=click.Choice(
        ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        case_sensitive=False),
    default='ERROR')
@click.pass_context
def cli(ctx, loglevel, config):
    configure_logging(loglevel)
    cfg = os.path.abspath(os.path.expanduser(config))
    console_logger.debug('Using config file: {}'.format(cfg))
    ctx.obj = PyscCLI(config_file=cfg)


@cli.command(help='Create initial config and inventoty')
def init():
    click.echo()
    if not os.path.exists(DEFAULT_CONFIG_DIR):
        os.makedirs(DEFAULT_CONFIG_DIR)
    if os.path.exists(DEFAULT_CONFIG_FILE):
        click.echo('File {} exists. Use --force to override.'. format(
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
@click.pass_obj
def connect(pysc_cli, host):
    click.echo('Connecting to {}'.format(host))
    pysc_cli.connect(host)


@cli.command(help='Get list of hosts')
@click.pass_obj
def list_hosts(pysc_cli):
    click.echo('Available hosts:')
    pysc_cli.list_hosts()


@cli.command(help='Get list of credendials')
@click.pass_obj
def list_credentials(pysc_cli):
    click.echo('Available credentials:')
    pysc_cli.list_credentials()
