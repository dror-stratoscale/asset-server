import yaml
import simplejson
import time
import os
import logging
from asset.server import config


class Allocations:
    _TIMEOUT = 20

    def __init__(self):
        with open(config.WORLD_PATH) as f:
            self._available = yaml.load(f)
        if not os.path.isdir(config.ALLOCATIONS_DIR):
            os.makedirs(config.ALLOCATIONS_DIR)
        self._allocations = self._loadAllocations()
        self._removeAllocationsFromAvailable()

    def create(self, assetKind, assetCount, pool, continent, allocationInfo):
        id = max([a['id'] for a in self._allocations] + [0]) + 1
        pools = self._available[continent][assetKind]
        if pool:
            poolInstance = pools[pool]
        else:
            pool, poolInstance = self._defaultPool(continent, assetKind, pools)
        if len(poolInstance['assets']) < assetCount:
            raise Exception(
                "Continent %(continent)s assetKind %(assetKind)s pool %(pool)s does not have enough "
                "available resources" % dict(continent=continent, assetKind=assetKind, pool=pool))
        allocation = dict(
            continent=continent, assetKind=assetKind, pool=pool, id=id, allocationInfo=allocationInfo,
            assets=poolInstance['assets'][:assetCount],
            heartbeat=time.time())
        poolInstance['assets'][:assetCount] = []
        with open(os.path.join(config.ALLOCATIONS_DIR, str(id)), "w") as f:
            simplejson.dump(allocation, f)
        logging.info("Allocation created: %(allocation)s", dict(allocation=allocation))
        return allocation

    @classmethod
    def cleanup(cls):
        cls._loadAllocations()

    @classmethod
    def heartbeat(cls, id):
        path = os.path.join(config.ALLOCATIONS_DIR, str(id))
        with open(path, "r") as f:
            allocation = simplejson.load(f)
        allocation['heartbeat'] = time.time()
        with open(path, "w") as f:
            simplejson.dump(allocation, f)

    @classmethod
    def loadAllocation(self, id):
        path = os.path.join(config.ALLOCATIONS_DIR, str(id))
        with open(path) as f:
            allocation = simplejson.load(f)
        if allocation['heartbeat'] < time.time() - self._TIMEOUT:
            logging.warning("Allocation %(id)s timed out", dict(id=id))
            os.unlink(path)
            return None
        else:
            return allocation

    @classmethod
    def destroy(self, id):
        os.unlink(os.path.join(config.ALLOCATIONS_DIR, str(id)))

    @classmethod
    def _loadAllocations(cls):
        result = [cls.loadAllocation(id) for id in list(os.listdir(config.ALLOCATIONS_DIR))]
        return [a for a in result if a is not None]

    def _removeAllocationsFromAvailable(self):
        for allocation in self._allocations:
            if allocation['continent'] not in self._available:
                logging.warning("Allocation exists from unknown continent: %(continent)s", dict(
                    continent=allocation['continent']))
                return
            continent = self._available[allocation['continent']]
            if allocation['assetKind'] not in continent:
                logging.warning("Allocation exists of unknown asset kind: %(kind)s", dict(
                    kind=allocation['assetKind']))
                return
            pools = continent[allocation['assetKind']]
            if allocation['pool'] not in pools:
                logging.warning("Allocation exists of unknown pool: %(pool)s", dict(
                    pool=allocation['pool']))
                return
            pool = pools[allocation['pool']]
            for asset in allocation['assets']:
                try:
                    pool['assets'].remove(asset)
                except ValueError:
                    logging.warning(
                        "Asset %(asset)s in allocation %(allocation)s is either non-existent or "
                        "allocated twice", dict(asset=asset, allocation=allocation))

    def _defaultPool(self, continent, assetKind, pools):
        default = [(k, p) for k, p in pools.iteritems() if p.get('defaultPool', False)]
        if len(default) == 0:
            raise Exception(
                "No default pool defined for continent %(continent)s, assetKind %(assetKind)s" %
                dict(continent=continent, assetKind=assetKind))
        if len(default) > 1:
            raise Exception(
                "Multiple default pools defined for continent %(continent)s, assetKind %(assetKind)s" %
                dict(continent=continent, assetKind=assetKind))
        return default[0]
