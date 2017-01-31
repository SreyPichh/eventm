from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import images
import sys
sys.modules['ndb'] = ndb

from settings import ENTITY_CACHE_EXPIRATION
from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils import cache_keys
from web.dao.import_dao import ImportDao
from models import Locality
from web.lib.utils import user_has_role
logger = logging.getLogger(__name__)

class ImportDTO:
  locality = Locality()  
  
class MemImportDao(ImportDTO):

    def __init__(self, _importDao):
     self.importDao = _importDao
    
    def get_record(self, id):
      locality = mc_wrap(cache_keys.get_locality_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.importDao.get_record(id))
      return locality
  
    def query_by_place_id(self, place_id):
      return self.importDao.query_by_place_id(place_id)
    
    def query_by_place_name(self, place_name):
      return self.importDao.query_by_place_name(place_name)
  
    def persist(self, locality, user_info):
      return self.importDao.persist(locality, user_info)
  
class NdbImportDao(ImportDTO):
  
  def get_record(self, locality_id):
    logger.info('NdbImportDao:: DBHIT: get_record for %s ' % locality_id)
    return Locality.get_by_id(long(locality_id))

  def query_by_place_id(self, place_id):
    logger.info('NdbImportDao:: DBHIT: query_by_place_id for %s ' % place_id)
    locality_query = Locality.query(Locality.place_id == place_id)
    locality = locality_query.fetch(1)
    return locality[0] if locality is not None and len(locality) > 0 else None
  
  def query_by_place_name(self, place_name):
    logger.info('NdbImportDao:: DBHIT: query_by_place_name for %s ' % place_name)
    locality_query = Locality.query(Locality.name == place_name)
    locality = locality_query.fetch(1)
    return locality[0] if locality is not None and len(locality) > 0 else None

  def persist(self, locality, user_info):
    key = None
    if locality is not None:
      curr_locality = None
      if locality.key is not None:
        curr_locality = self.get_record(locality.key.id())
      #If entry exists for the same locality, udpate the data
      if curr_locality is not None:
        self.copy_locality_model(curr_locality, locality)        
        curr_locality.updated_by = user_info.key        
        key = curr_locality.put()
      else:
        #create a new locality        
        locality.created_by = user_info.key
        locality.updated_by = user_info.key        
        key = locality.put()
      
      if key is not None:
        mc_delete(cache_keys.get_locality_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_locality_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name
    if from_model.address is not None:
      to_model.address = from_model.address
    print 'to_model ' + str(to_model)
    