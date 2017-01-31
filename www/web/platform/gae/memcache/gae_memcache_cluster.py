from google.appengine.api import memcache

class GaeMemcacheCluster(object):
    def get(self, cachekey):
        memdata = memcache.get(cachekey)
        return memdata
        
    def add(self, cachekey, memdata, expiration_in_secs):
        memcache.add(cachekey, memdata, expiration_in_secs)
            
    def delete(self, cachekey):
        memcache.delete(cachekey)
