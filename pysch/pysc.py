#/usr/bin/env python3

import sys
import click

from .cli import PyscCLI
from .inventory import Inventory

@click.group()
def cli():
    pass

@cli.command(help='Connect to the host')
# @click.argument('host', type=click.Choice(['rtc/i79dcgw1', '192.168.0.1', 'tele2/nin3-vsc1']))
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

# if __name__ == '__main__':
#     main()