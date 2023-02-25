import logging
import os
import sys
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

DEFAULT_CONFIG_FILE_SET = (
    DEFAULT_CONFIG_FILE,
    DEFAULT_INVENTORY_FILE,
    DEFAULT_PWDDB_FILE,
    DEFAULT_PWDDB_KEY
)


@click.group()
@click.option(
    '--config', '-c',
    help='Path to configuration file',
    type=click.Path(exists=False),
    default=DEFAULT_CONFIG_FILE)
@click.option(
    '--loglevel', '-l',
    type=click.Choice(
        ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
        case_sensitive=False),
    default='ERROR')
@click.pass_context
def cli(ctx, loglevel, config):

    cfg = os.path.abspath(os.path.expanduser(config)) if config else None
    if config:
        cfg = os.path.abspath(os.path.expanduser(config))
        configure_logging(loglevel, config_file=cfg)
    else:
        cfg = None
        configure_logging(loglevel)
    console_logger.debug('Using config file: {}'.format(config))

    ctx.ensure_object(dict)
    ctx.obj['CONFIG'] = config


@cli.command(help='Create initial config and inventoty')
@click.option(
    '--force',
    is_flag=True,
    help='Rewrite existing configuration files in ~/.config/pysch'
)
def init(force):
    if not os.path.exists(DEFAULT_CONFIG_DIR):
        os.makedirs(DEFAULT_CONFIG_DIR)
    # if os.path.exists(DEFAULT_CONFIG_FILE):
    if any(map(os.path.exists, DEFAULT_CONFIG_FILE_SET)):
        if force:
            for fname in DEFAULT_CONFIG_FILE_SET:
                if os.path.exists(fname):
                    click.echo(
                        'File {} will be overrided!'.format(fname)
                    )
            click.confirm('Do you want to continue?', abort=True)
        else:
            click.echo(
                'Some of configuration files exist in {}'.format(
                    DEFAULT_CONFIG_DIR))
            click.echo('Use --force to override.')
            sys.exit()
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
@click.pass_context
def connect(ctx, host):
    click.echo('Connecting to {}'.format(host))
    PyscCLI(config_file=ctx.obj['CONFIG']).connect(host)


@cli.command(help='Get list of hosts')
@click.pass_context
def list_hosts(ctx):
    click.echo('Available hosts:')
    PyscCLI(config_file=ctx.obj['CONFIG']).list_hosts()


@cli.command(help='Get list of credendials')
@click.pass_context
def list_credentials(ctx):
    click.echo('Available credentials:')
    PyscCLI(config_file=ctx.obj['CONFIG']).list_credentials()
