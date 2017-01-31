from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
import sys
sys.modules['ndb'] = ndb

import constants
from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils.cache_keys import get_childevent_cache_key
from web.dao.childevent_dao import ChildEventDao
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT
from models import Event
from web.lib.utils import user_has_role
logger = logging.getLogger(__name__)

class MemChildEventDao(ChildEventDao):

    def __init__(self, _childeventDao):
     self.childeventDao = _childeventDao
        
    def get_record(self, id):
      childevent = mc_wrap(get_childevent_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.childeventDao.get_record(id))
      return childevent

    def query_by_alias(self, alias):
      return self.childeventDao.query_by_alias(alias)

    def query_by_owner(self, user, status='all'):
      return self.childeventDao.query_by_owner(user, status)

    def search(self, value, key='name', status='all'):
      return self.childeventDao.search(self, value, key, status)

    def persist(self, childevent, user_info):
      return self.childeventDao.persist(childevent, user_info)
  
class NdbChildEventDao(ChildEventDao):
    
  def get_record(self, childevent_id):
    logger.info('NdbChildEventDao:: DBHIT: get_record for %s ' % childevent_id)
    return Event.get_by_id(long(childevent_id))
  
  def query_by_alias(self, alias):
      logger.info('NdbChildEventDao:: DBHIT: query_by_alias for %s ' % alias)
      childevent_query = Event.query(Event.alias == alias)
      childevent = childevent_query.fetch(1)
      return childevent[0] if childevent is not None and len(childevent) > 0 else None

  def query_by_owner(self, user, status='all'):
    logger.info('NdbChildEventDao:: DBHIT: query_by_owner for %s ' % user.email)
    owner_query = Event.query(Event.owners == user.key)
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      owner_query = owner_query.filter(status == status_value)
    owner_query = owner_query.order(-Event.updated_on)
    return owner_query.fetch()
  
  def search(self, value, key='name', status='all'):
    logger.info('NdbChildEventDao:: DBHIT: search for %s, %s ' % key % value)
    search_query = Event.query(Event._properties[key] == value)
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      search_query = search_query.filter(status == status_value)
    search_query = search_query.order(-Event.updated_on)
    return search_query.fetch()
  
  def persist(self, childevent, user_info):
    key = None
    if childevent is not None:
      curr_childevent = None
      if childevent.key is not None:
        curr_childevent = self.get_record(childevent.key.id())
      #If entry exists for the same childevent, udpate the data
      if curr_childevent is not None:
        self.copy_childevent_model(curr_childevent, childevent)
        curr_childevent.modified_by = user_info.key
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_childevent.status = 1 #pending_approval status
          if not user_info.key in curr_childevent.owners:
            curr_childevent.owners.append(user_info.key)
        key = curr_childevent.put()
      else:
        childevent.status = 0 #pending_creation status
        childevent.created_by = user_info.key
        childevent.modified_by = user_info.key
        if not user_has_role(user_info, 'admin'):
          childevent.owners = []
          childevent.owners.append(user_info.key)
        key = childevent.put()
      
      if key is not None:
        mc_delete(get_childevent_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_childevent_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.description is not None:
      to_model.description = from_model.description
    if from_model.start_datetime is not None:
      to_model.start_datetime = from_model.start_datetime
    if from_model.end_datetime is not None:
      to_model.end_datetime = from_model.end_datetime
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
    #if from_model.custom_info.name is not None:
      #to_model.custom_info.name = from_model.custom_info.name
    #if from_model.custom_info.value is not None:
      #to_model.custom_info.value = from_model.custom_info.value 
    print 'to_model ' + str(to_model)
