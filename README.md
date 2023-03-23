# pysch - Python-made SSH Connection Helper

pysch (spelled in Russian as пыщ, just for fun) is an SSH Client based on paramiko. It uses keepass to securely store remote hosts credentials and YAML to maintain your nodes tree.

## Installation 
At the moment, only `setup.py` methon is avaiable: 
```
python -m venv venv
cd venv
source bin/activate
python setup.py install
```

## Usage
Here is the avaiable commands:
```
(venv) % pysch
Usage: pysch [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config PATH               Path to configuration file
  -l, --loglevel [CRITICAL|ERROR|WARNING|INFO|DEBUG]
  --help                          Show this message and exit.

Commands:
  add-credentials   Add new credendials
  connect           Connect to the host
  init              Create initial config and inventoty
  list-credentials  Get list of credendials
  list-hosts        Get list of hosts
  ```

First, init the configuration. That creates sample configuration and inventory files with empty keepass file protected with key in `~/.config/pysch/` directory:
  ```
  (venv) % pysch init
  ```
Then add your hosts to the `~/.config/pysch/inventory.yaml` using the text editor of your choise and credentials for it using any keepass software or the `add-credentials` command.