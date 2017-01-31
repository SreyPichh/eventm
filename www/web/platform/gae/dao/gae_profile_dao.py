from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
import sys
sys.modules['ndb'] = ndb

from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils import cache_keys
from web.dao.profile_dao import ProfileDao
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT, PAGE_SIZE
from models import User
from web.lib.utils import user_has_role
logger = logging.getLogger(__name__)

class MemProfileDao(ProfileDao):

    def __init__(self, _profileDao):
     self.profileDao = _profileDao
        
    def get_record(self, id):
      profile = mc_wrap(cache_keys.get_user_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.profileDao.get_record(id))
      return profile   
    
    def query_by_all(self, user):
      return self.profileDao.query_by_all(user)

    def persist(self, user, user_info):
      return self.profileDao.persist(user, user_info)
  
class NdbProfileDao(ProfileDao): 

  def get_record(self, user_id):
    logger.info('NdbProfileDao:: DBHIT: get_record for %s ' % user_id)
    return User.get_by_id(long(user_id))  
  
  def query_by_all(self, user):
    logger.info('NdbProfileDao:: DBHIT: get_all_record ')
    user_query = User.query(User.activated == True, User.key != user.key)
    return user_query.fetch()
  
  def persist(self, user, user_info):
    key = None
    if user is not None:
      curr_user = None
      if user.key is not None:
        curr_user = self.get_record(user.key.id())
      #If entry exists for the same user, udpate the data
      if curr_user is not None:
        self.copy_user_model(curr_user, user)
        curr_user.updated_by = user_info.key
        key = curr_user.put()
      
      logger.debug("User persisted in datastore, %s " % key)
      if key is not None:
        #TODO: Make sure all the caches that has this entity is deleted here
        mc_delete(cache_keys.get_user_cache_key(key.id()))
      return key

  def copy_user_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name
    if from_model.last_name is not None:
      to_model.last_name = from_model.last_name
    if from_model.sport is not None:
      to_model.sport = from_model.sport
    if from_model.email is not None:
      to_model.email = from_model.email
    if from_model.phone is not None:
      to_model.phone = from_model.phone
    if from_model.locality is not None:
      to_model.locality = from_model.locality
    if from_model.locality_id is not None:
      to_model.locality_id = from_model.locality_id
    if from_model.i_want is not None:
      to_model.i_want = from_model.i_want
    print 'to_model ' + str(to_model)
    