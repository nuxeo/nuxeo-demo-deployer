"""Common utilities"""
# Author: Olivier Grisel <oogrisel@nuxeo.com>

from __future__ import print_function
import os
from os.path import join
from os.path import abspath
import sys

from time import sleep


KEYS_FOLDER = os.path.expanduser('~/aws_keys')
DEFAULT_MARKER = object()


def cmd(cmd):
    code = os.system(cmd)
    if code != 0:
        raise RuntimeError("Error executing: " + cmd)


def pflush(*args, **kwargs):
    """Flush stdout for making Jenkins able to monitor the progress live"""
    print(*args, **kwargs)
    sys.stdout.flush()