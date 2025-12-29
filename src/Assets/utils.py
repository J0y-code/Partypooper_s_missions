"""
Utilities module for common functions and decorators.
"""

__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

import time
from functools import wraps


def profile(func):
    """
    Decorator to profile function execution time.

    Args:
        func: The function to profile.

    Returns:
        The wrapped function that prints execution time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"[PROFILE] {func.__name__} took {elapsed:.6f} seconds")
        return result
    return wrapper


def get_local_ip():
    """
    Get the local IP address of the machine.

    Returns:
        str: The local IP address.
    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip