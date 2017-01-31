from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
import sys
sys.modules['ndb'] = ndb

from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils.cache_keys import get_business_cache_key
from web.dao.business_dao import BusinessDao
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT
from models import Business
from web.lib.utils import user_has_role

logger = logging.getLogger(__name__)

class MemBusinessDao(BusinessDao):

    def __init__(self, _businessDao):
      self.businessDao = _businessDao
        
    def get_record(self, id):
      business = mc_wrap(get_business_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.businessDao.get_record(id))
      return business

    def query_by_alias(self, alias):
      return self.businessDao.query_by_alias(alias)

    def query_by_owner(self, user, status='all'):
      return self.businessDao.query_by_owner(user, status)

    def search(self, value, key='name', status='all'):
      return self.businessDao.search(self, value, key, status)

    def persist(self, business, user_info):
      return self.businessDao.persist(business, user_info)

        
class NdbBusinessDao(BusinessDao):
    
  def get_record(self, business_id):
    logger.info('NdbBusinessDao:: DBHIT: get_record for %s ' % business_id)
    return Business.get_by_id(long(business_id))
  
  def query_by_alias(self, alias):
    logger.info('NdbBusinessDao:: DBHIT: query_by_alias for %s ' % alias)
    business_query = Business.query(Business.alias == alias)
    business = business_query.fetch(1)
    return business[0] if business is not None and len(business) > 0 else None

  def query_by_owner(self, user, status='all'):
    logger.info('NdbBusinessDao:: DBHIT: query_by_owner for %s ' % user.email)
    business_query = Business.query(ndb.OR(Business.owners == user.key, Business.created_by == user.key, Business.updated_by == user.key))
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      business_query = business_query.filter(status == status_value)
    business_query = business_query.order(Business.updated_on)
    return business_query.fetch()
  
  def search(self, value, key='name', status='all'):
    logger.info('NdbBusinessDao:: DBHIT: search for %s, %s ' % key % value)
    search_query = Business.query(Business._properties[key] == value)
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      search_query = search_query.filter(status == status_value)
    search_query = search_query.order(Business.updated_on)
    return search_query.fetch()
  
  def persist(self, business, user_info):
    key = None
    if business is not None:
      curr_business = None
      if business.key is not None:
        curr_business = self.get_record(business.key.id())
      #If entry exists for the same business, udpate the data
      if curr_business is not None:
        self.copy_business_model(curr_business, business)
        curr_business.modified_by = user_info.key
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_business.status = 1 #pending_approval status
          if not user_info.key in curr_business.owners:
            curr_business.owners.append(user_info.key)
        key = curr_business.put()
      else:
        business.status = 0 #pending_creation status
        business.created_by = user_info.key
        business.modified_by = user_info.key
        if not user_has_role(user_info, 'admin'):
          business.owners = []
          business.owners.append(user_info.key)
        key = business.put()
      
      if key is not None:
        mc_delete(get_business_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, as that cannot be changed
  def copy_business_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.alias is not None:
      to_model.alias = from_model.alias 
    if from_model.description is not None:
      to_model.description = from_model.description 
    if from_model.logo is not None:
      to_model.logo = from_model.logo
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
    print 'to_model ' + str(to_model)
