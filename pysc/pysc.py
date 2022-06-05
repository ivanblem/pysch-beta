#/usr/bin/env python3

import sys
import commands

def main():
    if len(sys.argv) == 3:
        if sys.argv[1] == 'connect':
            commands.connect(sys.argv[2])

if __name__ == '__main__':
    main()