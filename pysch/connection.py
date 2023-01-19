import re
import sys
import paramiko
from pykeepass import PyKeePass

from .interactive import interactive_shell
from .inventory import Inventory
from .log_config import get_logger
from .common import get_local_terminal_size, get_local_terminal_type

logger = get_logger(__name__)

_re_raw_ssh = re.compile(r'([\d\w\.\-_]+)@([\d\w\.\-_]+)')
# _re_inventory_ssh = re.compile(r'((([\w\d\.\-_]+)/?)+)')


class ConnectionConfig():

    def __init__(self, username=None, hostname=None, **kwargs) -> None:
        self.username = username
        self.hostname = hostname
        pass


class SSHConnection():

    def __init__(self, target: str) -> None:
        self.target = target
        # self.type = self._identify_type()
        # self.config = ConnectionConfig
        self.config = self._get_config()
        if 'credentials' in self.config.keys():
            self.__get_credentials()
        logger.debug(self.config)

    # def _identify_type(self) -> str:
    #     raw_match = _re_raw_ssh.match(self.target)
    #     logger.error(raw_match)
    #     if raw_match:
    #         self.config = ConnectionConfig(
    #           username=raw_match.group(1),
    #           hostname=raw_match.group(2))
    #         logger.error(self.config)
    #     pass

    def _get_config(self):
        inventory = Inventory('../inventory.yaml')
        item_path = self.target.split('/')
        logger.debug(item_path)
        # logger.debug(self.target.split('@'))
        # logger.debug(inventory.inventory_dict)
        config = inventory.inventory_dict[item_path[0]]
        if len(item_path) > 1:
            for item in item_path[1:]:
                logger.debug(item)
                logger.debug(config)
                config = config[item]

        # temporary workaround
        if 'key_filename' in config.keys():
            config.pop('key_filename')

        # paramiko.SSHClient()
        # hostname,
        # port=SSH_PORT,
        # username=None,
        # password=None,
        # pkey=None,
        # key_filename=None,
        # timeout=None,
        # allow_agent=True,
        # look_for_keys=True,
        # compress=False,
        # sock=None,
        # gss_auth=False,
        # gss_kex=False,
        # gss_deleg_creds=True,
        # gss_host=None,
        # banner_timeout=None,
        # auth_timeout=None,
        # gss_trust_dns=True,
        # passphrase=None,
        # disabled_algorithms=None,

        return config

    def __get_credentials(self):
        try:
            pwd_db = PyKeePass('../pwd_db.kdbx', keyfile='pwddb.keyx')
        except FileNotFoundError as e:
            logger.error(e)
            # logger.exception(e)
            sys.exit(1)

        credentials = pwd_db.find_entries_by_title(
            self.config['credentials'],
            first=True
        )
        logger.debug(credentials)
        try:
            self.config['username'] = credentials.username
            self.config['password'] = credentials.password
            self.config.pop('credentials')
        except AttributeError as e:
            logger.error(e)

    def connect(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        # logger.info('connecting to '+self.config['hostname'])
        logger.info('connecting to '+self.config['hostname'])
        # TODO: deal with BadHostKeyException
        # better to check it in advance even
        # client.load_system_host_keys
        # paramiko.HostKeys
        client.connect(**self.config)

        t = client.get_transport()
        channel = t.open_session()

        # local_terminal_size = os.get_terminal_size()
        # local_terminal_type = os.getenv('TERM')

        try:
            channel.get_pty(
                get_local_terminal_type(),
                *get_local_terminal_size()
            )
            channel.invoke_shell()
        except Exception as err:
            logger.error(str(err))
            sys.exit(1)

        interactive_shell(channel)

        # print(channel.getpeername())
        # print(channel.active)

# if __name__ == '__main__':
#     t480 = SSHConnection('t480')
#     print(t480.config)
#     # SSHConnection('ivan@1.1.1.1')
#     auto_vm = SSHConnection('rtc/t023auto01')
#     print(auto_vm.config)
#     nas = SSHConnection('nas')
#     print(nas.config)
#     # SSHConnection('tele2/nin3/vsc-1')
