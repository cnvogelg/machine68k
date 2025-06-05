import socket
import threading
import time

import pytest


def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    addr, port = s.getsockname()
    s.close()
    return port


@pytest.fixture(scope="module")
def threaded_server():
    rmachine68k = pytest.importorskip("rmachine68k")
    """run a threaded rpyc server with rmachine and return port of server"""
    port = get_free_port()
    server = rmachine68k.create_service(port=port, type="threaded")
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield port
    server.close()
    thread.join(timeout=2)


@pytest.fixture(scope="function")
def remote_client(threaded_server):
    """return a rpyc client connected to a rmachine server"""
    rmachine68k = pytest.importorskip("rmachine68k")
    port = threaded_server

    client = rmachine68k.create_client(port=port)
    yield client
    client.close()
