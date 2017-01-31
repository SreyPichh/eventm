from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search 
import sys
sys.modules['ndb'] = ndb

from constants import SPORT_DICT, PLAYGROUND
from web.utils.memcache_utils import mc_wrap, mc_delete, mc_get
from web.utils import cache_keys
from web.dao.bulkdata_dao import BulkDataDao
from web.platform.gae.dao.gae_media_dao import NdbMediaDao
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT, PAGE_SIZE
from models import MasterData
from web.lib.utils import user_has_role
from web.utils.app_utils import normalize_sport_name

logger = logging.getLogger(__name__)

class MemBulkDataDao(BulkDataDao):

    def __init__(self, _bulkdataDao):
     self.bulkdataDao = _bulkdataDao
        
    def get_record(self, id):
      bulkdata = mc_wrap(cache_keys.get_bulkdata_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.bulkdataDao.get_record(id))
      return bulkdata    
    
    def persist(self, bulkdata, user_info):
      return self.bulkdataDao.persist(bulkdata, user_info)
  
class NdbBulkDataDao(BulkDataDao):
  mediaDao = NdbMediaDao()

  def get_record(self, bulkdata_id):
    logger.info('NdbBulkDataDao:: DBHIT: get_record for %s ' % bulkdata_id)
    return MasterData.get_by_id(long(bulkdata_id))  
  
  def persist(self, bulkdata, user_info):
    key = None
    if bulkdata is not None:
      curr_bulkdata = None
      if bulkdata.key is not None:
        curr_bulkdata = self.get_record(bulkdata.key.id())
      #If entry exists for the same bulkdata, udpate the data
      if curr_bulkdata is not None:
        #self.copy_bulkdata_model(curr_bulkdata, bulkdata)
        curr_bulkdata.updated_by = user_info.key
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_bulkdata.status = 1 #pending_approval status
          if not user_info.key in curr_bulkdata.owners:
            curr_bulkdata.owners.append(user_info.key)
        key = curr_bulkdata.put()
      else:
        #create a new bulkdata
        
        bulkdata.created_by = user_info.key
        bulkdata.updated_by = user_info.key       
        key = bulkdata.put()
      
      logger.debug("Bulkdata persisted in datastore, %s " % key)
      if key is not None:        
        #TODO: Make sure all the caches that has this entity is deleted here
        mc_delete(cache_keys.get_bulkdata_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_bulkdata_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.sport is not None:
      to_model.sport = from_model.sport 
    if from_model.description is not None:
      to_model.description = from_model.description    
    if from_model.address.line1 is not None:
      to_model.address.line1 = from_model.address.line1
    if from_model.address.line2 is not None:
      to_model.address.line2 = from_model.address.line2
    if from_model.address.locality is not None:
      to_model.address.locality = from_model.address.locality    
    if from_model.address.city is not None:
      to_model.address.city = from_model.address.city
    if from_model.address.pin is not None:
      to_model.address.pin = from_model.address.pin
    if from_model.address.latlong is not None:
      to_model.address.latlong = from_model.address.latlong
    if from_model.contact_info.person_name is not None:
      to_model.contact_info.person_name = from_model.contact_info.person_name
    if from_model.contact_info.email is not None:
      to_model.contact_info.email = from_model.contact_info.email
    if from_model.contact_info.phone is not None:
      to_model.contact_info.phone = from_model.contact_info.phone
    if from_model.contact_info.website is not None:
      to_model.contact_info.website = from_model.contact_info.website
    if from_model.contact_info.facebook is not None:
      to_model.contact_info.facebook = from_model.contact_info.facebook
    if from_model.contact_info.twitter is not None:
      to_model.contact_info.twitter = from_model.contact_info.twitter
    if from_model.contact_info.youtube is not None:
      to_model.contact_info.youtube = from_model.contact_info.youtube
    if from_model.contact_info.gplus is not None:
      to_model.contact_info.gplus = from_model.contact_info.gplus
    to_model.featured = from_model.featured
    print 'to_model ' + str(to_model)
    