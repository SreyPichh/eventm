from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
import sys
sys.modules['ndb'] = ndb

from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils import cache_keys
from web.dao.register_dao import RegisterDao
from settings import ENTITY_CACHE_EXPIRATION
from models import Register
from web.lib.utils import user_has_role
logger = logging.getLogger(__name__)

class MemRegisterDao(RegisterDao):

    def __init__(self, _registerDao):
     self.registerDao = _registerDao
        
    def get_record(self, id):
      register = mc_wrap(cache_keys.get_register_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.registerDao.get_record(id))
      return register   
    
    def query_by_user(self, user):
      return self.registerDao.query_by_user(user)
    
    def query_by_reg_user_id(self, reg_id, user_id, status='all'):
      return self.registerDao.query_by_reg_user_id(reg_id, user_id)
  
    def persist(self, register, user_info):
      return self.registerDao.persist(register, user_info)
  
class NdbRegisterDao(RegisterDao): 

  def get_record(self, record_id):
    logger.info('NdbRegisterDao:: DBHIT: get_record for %s ' % record_id)
    return Register.get_by_id(long(record_id))  
  
  def query_by_user(self, user):
    logger.info('NdbRegisterDao:: DBHIT: get_all_record ')
    reg_query = Register.query(Register.status == True, Register.user_id == user.key)
    return reg_query.fetch()
  
  def query_by_reg_user_id(self, reg_id, user, status='all'):
    logger.info('NdbEventDao:: DBHIT: query_by_reg_user_id for %s %s' % (reg_id, user.key))
    reg_query = Register.query(ndb.AND(Register.reg_id == reg_id, Register.user_id == user.key ))
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      reg_query = reg_query.filter(status == status_value)    
    register = reg_query.fetch(1)
    return register[0] if register is not None and len(register) > 0 else None

  def persist(self, register, user_info):
    key = None
    if register is not None:
      curr_register = None
      if register.key is not None:
        curr_register = self.get_record(register.key.id())
      #If entry exists for the same registration, udpate the data
      if curr_register is not None:
        self.copy_register_model(curr_register, register)
        curr_register.updated_by = user_info.key
        key = curr_register.put()
      else:
        # create a new registration        
        register.created_by = user_info.key
        register.updated_by = user_info.key                 
        register.status = 0 #pending_creation status        
        key = register.put()
        
      logger.debug("Register persisted in datastore, %s " % key)
      if key is not None:
        #TODO: Make sure all the caches that has this entity is deleted here
        mc_delete(cache_keys.get_register_cache_key(key.id()))
      return key

  def copy_register_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.payment is not None:
      to_model.payment = from_model.payment
    if from_model.team_id is not None:
      to_model.team_id = from_model.team_id
    if from_model.player_id is not None:
      to_model.player_id = from_model.player_id
    if from_model.reg_type is not None:
      to_model.reg_type = from_model.reg_type    
    print 'to_model ' + str(to_model)
    