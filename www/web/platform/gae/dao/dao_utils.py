# Utils that will use the DAO layer. Primarily used for custom caching of DAO objects. DAO layer cannot use this utils.
# Utils are seperated to avoid circular dependencies

from settings import STATIC_CACHE_EXPIRATION
from web.dao.dao_factory import DaoFactory
from web.utils.memcache_utils import mc_wrap
from web.utils import cache_keys


#TODO: This cache to be populated on server startup.
def get_localities(city_name):
  return mc_wrap(cache_keys.get_localities_cache_key(city_name), STATIC_CACHE_EXPIRATION, 
                 lambda x : _get_localities_from_dao(city_name))  

def _get_localities_from_dao(city_name):
  playgroundDao =  DaoFactory.create_ro_playgroundDao()
  eventDao =  DaoFactory.create_ro_eventDao()
  trainingcentreDao =  DaoFactory.create_ro_trainingCentreDao()  
  
  localities = set()
  active_playgrounds = playgroundDao.get_active(city_name, no_records=-1)
  for pg in active_playgrounds:
    localities.add(str(pg.address.locality))
  active_tc = trainingcentreDao.get_active(city_name, no_records=-1)
  for tc in active_tc:
    localities.add(str(tc.address.locality))
  active_events = eventDao.get_active(city_name, no_records=-1)
  for event in active_events:
    localities.add(str(event.address.locality))
  
  return sorted(list(localities))

