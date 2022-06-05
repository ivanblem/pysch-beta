from connection import SSHConnection

def connect(target_host):
    SSHConnection(target_host).connect()