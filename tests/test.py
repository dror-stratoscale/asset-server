import assetserverwrapper
import unittest
from asset import clientfactory
import logging
import time
import subprocess
import signal


class Test(unittest.TestCase):
    def setUp(self):
        self.server = assetserverwrapper.AssetServerWrapper()

    def tearDown(self):
        self.server.cleanUp()

    def test_oneAsset_oneAllocation(self):
        self.server.writeWorld(
            {"datacenter 1": {'subnet': {'network 1': {
                'defaultPool': True,
                'assets': [{'subnet': '192.168.1.0'}]}}}})
        self.server.start()
        client = clientfactory.factory()
        try:
            allocation = client.allocate('subnet')
            self.assertEquals(allocation.continent(), 'datacenter 1')
            self.assertEquals(allocation.assetKind(), 'subnet')
            self.assertEquals(allocation.pool(), 'network 1')
            self.assertEquals(allocation.assets(), [{'subnet': '192.168.1.0'}])
            allocation.free()
        finally:
            client.close()

    def test_oneAsset_freeAndReallocate(self):
        self.server.writeWorld(
            {"datacenter 1": {'subnet': {'network 1': {
                'defaultPool': True,
                'assets': [{'subnet': '192.168.1.0'}]}}}})
        self.server.start()
        client = clientfactory.factory()
        try:
            allocation = client.allocate('subnet')
            self.assertEquals(allocation.assets(), [{'subnet': '192.168.1.0'}])
            allocation.free()
            allocation2 = client.allocate('subnet')
            self.assertEquals(allocation2.assets(), [{'subnet': '192.168.1.0'}])
            allocation2.free()
        finally:
            client.close()

    def test_oneAsset_busy(self):
        self.server.writeWorld(
            {"datacenter 1": {'subnet': {'network 1': {
                'defaultPool': True,
                'assets': [{'subnet': '192.168.1.0'}]}}}})
        self.server.start()
        client = clientfactory.factory()
        try:
            allocation = client.allocate('subnet')
            self.assertEquals(allocation.assets(), [{'subnet': '192.168.1.0'}])
            with self.assertRaises(Exception):
                client.allocate('subnet')
            logging.info("Sleeping for timeout")
            time.sleep(30)
            logging.info("Done Sleeping for timeout")
            with self.assertRaises(Exception):
                client.allocate('subnet')
            allocation.free()
            allocation2 = client.allocate('subnet')
            self.assertEquals(allocation2.assets(), [{'subnet': '192.168.1.0'}])
            allocation2.free()
        finally:
            client.close()

    def test_oneAsset_timeout(self):
        self.server.writeWorld(
            {"datacenter 1": {'subnet': {'network 1': {
                'defaultPool': True,
                'assets': [{'subnet': '192.168.1.0'}]}}}})
        self.server.start()
        client = clientfactory.factory()
        try:
            popen = subprocess.Popen([
                "python", "-c",
                'from asset import clientfactory\n'
                'client = clientfactory.factory()\n'
                'client.allocate("subnet")\n'
                'import time\n'
                'time.sleep(1000000)'])
            time.sleep(3)
            with self.assertRaises(Exception):
                client.allocate('subnet')
            popen.send_signal(signal.SIGKILL)
            logging.info("Sleeping for timeout")
            time.sleep(30)
            logging.info("Done Sleeping for timeout")
            allocation2 = client.allocate('subnet')
            self.assertEquals(allocation2.assets(), [{'subnet': '192.168.1.0'}])
            allocation2.free()
        finally:
            client.close()


if __name__ == '__main__':
    unittest.main()
