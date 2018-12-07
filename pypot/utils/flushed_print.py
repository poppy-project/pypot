from __future__ import print_function
import sys


def flushed_print(*args, **kwargs):
    """
    Use to replace print(*args, flush=True) that doesn't exist for python<3.3
    """
    print(*args, **kwargs)
    file = kwargs.get('file', sys.stdout)
    file.flush() if file is not None else sys.stdout.flush()
