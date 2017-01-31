import logging
import cPickle as pickle

from web.platform.gae.memcache.gae_memcache_cluster import GaeMemcacheCluster

logger = logging.getLogger(__name__)

def create_memcache_cluster():
    return GaeMemcacheCluster()
       
memcache_cluster = create_memcache_cluster()

def mc_wrap(cachekey, expiration_in_secs, fn, store_result=True):
    result = None
    memdata = memcache_cluster.get(cachekey)
    if memdata is None:
        result = fn(None)
        if store_result and result is not None:
            memdata = pickle.dumps(result)
            memcache_cluster.add(cachekey, memdata, expiration_in_secs)
    else:
        result = pickle.loads(memdata)
    return result
    
def mc_delete(cachekey):
    memcache_cluster.delete(cachekey)
    pass    

def mc_get(cachekey):
    memdata = memcache_cluster.get(cachekey)
    return memdata