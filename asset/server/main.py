import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
import argparse
from asset.server import ipcserver
import time
from asset.server import config

parser = argparse.ArgumentParser()
parser.add_argument("--requestPort", default=1017, type=int)
parser.add_argument("--worldFile")
parser.add_argument("--allocationsDir")
parser.add_argument("--allocationsLockFile")
args = parser.parse_args()

if args.worldFile:
    config.WORLD_PATH = args.worldFile
if args.allocationsDir:
    config.ALLOCATIONS_DIR = args.allocationsDir
if args.allocationsLockFile:
    config.LOCK_FILE = args.allocationsLockFile

ipcServer = ipcserver.IPCServer(tcpPort=args.requestPort)
while True:
    time.sleep(1000000)
