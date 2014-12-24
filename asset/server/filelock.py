import fcntl
import contextlib
import os


@contextlib.contextmanager
def lock(path):
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            raise Exception("Lock operation failed")
        yield
        fcntl.flock(f, fcntl.LOCK_UN)
