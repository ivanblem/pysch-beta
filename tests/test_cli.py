from click.testing import CliRunner
from pysch import cli


def test_command_list():
    runner = CliRunner()
    result = runner.invoke(cli.cli)
    command_list = [
        'add-credentials',
        'connect',
        'init',
        'list-credentials',
        'list-hosts',
    ]
    assert all([command in result.output for command in command_list])


def test_connect_no_host():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ['connect'])
    assert result.exit_code == 2
    assert "Missing argument 'HOST'" in result.output
