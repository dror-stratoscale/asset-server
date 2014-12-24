import subprocess
import os
import tempfile
import shutil
import yaml
import socket
import time
from asset import api


class AssetServerWrapper:
    def __init__(self):
        self._varLib = tempfile.mkdtemp()
        self._worldFile = os.path.join(self._varLib, "asset.world.yaml")
        self._allocationsDir = os.path.join(self._varLib, "allocations")
        self._allocationsLockFile = os.path.join(self._varLib, "allocations.lock")
        self._clientConfig = os.path.join(self._varLib, "clinet.conf")
        os.environ['ASSET_CONFIG_FILE'] = self._clientConfig
        self._popen = None

    def start(self):
        self._port = self._freeTCPPort()
        self._popen = subprocess.Popen([
            "python", "asset/server/main.py",
            "--requestPort", str(self._port),
            "--worldFile", self._worldFile,
            "--allocationsDir", self._allocationsDir,
            "--allocationsLockFile", self._allocationsLockFile])
        self._waitForServerToBeReady()
        self._writeClientConfig()

    def _writeClientConfig(self):
        conf = dict(
            CONFIG_VERSION=api.VERSION,
            DEFAULT_USER='fake user',
            PROVIDER="tcp://localhost:%d" % self._port,
            DEFAULT_CONTINENT="datacenter 1",
            DEFAULT_PURPOSE="testing")
        with open(self._clientConfig, "w") as f:
            yaml.dump(conf, f)

    def stop(self):
        assert self._popen is not None
        assert self._popen.poll() is None
        self._popen.terminate()
        self._popen.wait()
        self._popen = None

    def cleanUp(self):
        if self._popen is not None:
            self.stop()
        shutil.rmtree(self._varLib, ignore_errors=True)

    def writeWorld(self, data):
        with open(self._worldFile, "w") as f:
            yaml.dump(data, f)

    def _waitForServerToBeReady(self):
        for i in xrange(10):
            sock = socket.socket()
            try:
                sock.connect(("localhost", self._port))
                return
            except:
                time.sleep(0.1)
            finally:
                sock.close()
        raise Exception("Server did not start")

    def _freeTCPPort(self):
        sock = socket.socket()
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", 0))
            return sock.getsockname()[1]
        finally:
            sock.close()
