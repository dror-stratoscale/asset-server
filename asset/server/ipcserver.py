import threading
import zmq
import logging
import simplejson
from asset.server import allocations
from asset.server import filelock
from asset.server import config
from asset.tcp import heartbeat
from asset.tcp import suicide
from asset import api


class IPCServer(threading.Thread):
    def __init__(self, tcpPort):
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        self._socket.bind("tcp://*:%d" % tcpPort)
        threading.Thread.__init__(self)
        self.daemon = True
        threading.Thread.start(self)

    def _cmd_handshake(self, versionInfo):
        if versionInfo['ASSET_VERSION'] != api.VERSION:
            raise Exception(
                "Asset API version on the client side is '%s', and '%s' on the provider" % (
                    versionInfo['ASSET_VERSION'], api.VERSION))
        if versionInfo['ZERO_MQ']['VERSION_MAJOR'] != zmq.VERSION_MAJOR:
            raise Exception(
                "zmq version on the client side is '%s', and '%s' on the provider" % (
                    versionInfo['ZERO_MQ']['VERSION_MAJOR'], zmq.VERSION_MAJOR))

    def _cmd_allocate(self, assetKind, assetCount, pool, continent, allocationInfo):
        allocationsInstance = allocations.Allocations()
        allocation = allocationsInstance.create(
            assetKind=assetKind, assetCount=assetCount, pool=pool, continent=continent,
            allocationInfo=allocationInfo)
        return allocation['id']

    def _cmd_allocation__assets(self, id):
        return allocations.Allocations.loadAllocation(id)['assets']

    def _cmd_allocation__free(self, id):
        allocations.Allocations.destroy(id)

    def _cmd_allocation__pool(self, id):
        return allocations.Allocations.loadAllocation(id)['pool']

    def _cmd_allocation__continent(self, id):
        return allocations.Allocations.loadAllocation(id)['continent']

    def _cmd_heartbeat(self, ids):
        for id in ids:
            allocations.Allocations.heartbeat(id)
        return heartbeat.HEARTBEAT_OK

    def run(self):
        try:
            while True:
                try:
                    self._work()
                except:
                    logging.exception("Handling")
        except:
            logging.exception("Asset IPC server aborts")
            suicide.killSelf()
            raise

    def _work(self):
        message = self._socket.recv(0)
        try:
            incoming = simplejson.loads(message)
            handler = getattr(self, "_cmd_" + incoming['cmd'])
            with filelock.lock(config.LOCK_FILE):
                response = handler(** incoming['arguments'])
        except Exception, e:
            logging.exception('Handling')
            response = dict(exceptionString=str(e), exceptionType=e.__class__.__name__)
        self._socket.send_json(response)
