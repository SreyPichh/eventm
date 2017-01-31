from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import images
import sys
sys.modules['ndb'] = ndb

from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT
from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils import cache_keys
from web.dao.match_dao import MatchDao
from web.platform.gae.dao.gae_event_dao import NdbEventDao
from models import Match, Playground
from web.lib.utils import user_has_role, has_admin_access
logger = logging.getLogger(__name__)

class MatchDTO:
  match = Match()
  playground = None
  teams = []
  
class MemMatchDao(MatchDao):

    def __init__(self, _matchDao):
     self.matchDao = _matchDao
        
    def get_record(self, id):
     return mc_wrap(cache_keys.get_match_cache_key(id), ENTITY_CACHE_EXPIRATION,
                     lambda x: self.matchDao.get_record(id))
    
    def query_by_owner(self, user, status='all'):
      return self.matchDao.query_by_owner(user, status)
    
    def query_by_alias(self, alias, sport):
      return self.matchDao.query_by_alias(alias, sport)    
    
    def get_matches_for_event(self, event_key, no_records=-1):
      return self.matchDao.get_matches_for_event(event_key, no_records)
    
    def status_change(self, match, user_info):
      return self.matchDao.status_change(match, user_info)
  
    def persist(self, media, user_info):
      return self.matchDao.persist(media, user_info)
  
class NdbMatchDao(MatchDao):
  eventDao = NdbEventDao()
    
  def get_record(self, match_id):
    logger.info('NdbMatchDao:: DBHIT: get_record for %s ' % match_id)
    return Match.get_by_id(long(match_id))
  
  def query_by_owner(self, user, status='all'):
    logger.info('NdbMatchDao:: DBHIT: query_by_owner for %s ' % user.email)
    owner_query = Match.query()
    if not user_has_role(user, 'admin'):
      owner_query = Match.query(ndb.OR(Match.owners == user.key, Match.created_by == user.key, Match.updated_by == user.key))
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      owner_query = owner_query.filter(status == status_value)
    owner_query = owner_query.order(-Match.updated_on)
    return owner_query.fetch()
  
  def query_by_alias(self, alias, event_id, sport):
    logger.info('NdbMatchDao:: DBHIT: query_by_alias for %s ' % alias)
    match_query = Match.query(Match.alias == alias, Match.event_id == event_id, Match.sport == sport)
    match = match_query.fetch(1)
    return match[0] if match is not None and len(match) > 0 else None

  def get_matches_for_event(self, event_key, user_info=None, no_records=-1):
    logger.info('NdbMatchDao:: DBHIT: get_matches_for_event for event_key, %s' % (event_key))
    match_query = Match.query(Match.event_id == event_key) 
    if user_info is None or (not has_admin_access(user_info, self.eventDao.get_record(event_key.id()))):
      match_query = match_query.filter(Match.status == 2)    
    match_query = match_query.order(-Match.start_datetime)
    
    if no_records > -1:
      matches = match_query.fetch(no_records)
    else:
      matches = match_query.fetch()
      
    match_dtos = []
    if matches is not None:
      for match in matches:
        match_dto = MatchDTO()
        match_dto.match = match
        if match.playground_id:
          match_dto.playground = match.playground_id.get()
        else:
          match_dto.playground = None
        if match.participants:
          match_dto.teams = []
          for participant in match.participants:
            match_dto.teams.append(participant.get())
        match_dtos.append(match_dto)
    return match_dtos    
  
  def status_change(self, match, user_info):
    key = None
    if match is not None:      
      if match.key is not None:                
        match.updated_by = user_info.key
        # change the status from current status
        if match.status == 2:
          match.status = 1 #deactive status
        else:
          match.status = 2 #active status
        key = match.put()
      
      if key is not None:
        mc_delete(cache_keys.get_match_cache_key(key.id()))
      return key
  
  def persist(self, match, user_info):
    key = None
    if match is not None:
      curr_match = None
      if match.key is not None:
        curr_match = self.get_record(match.key.id())
      #If entry exists for the same match, udpate the data
      if curr_match is not None:
        self.copy_match_model(curr_match, match)
        match.playground_id = None
        curr_match.updated_by = user_info.key
        
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_match.status = 1 #pending_approval status
          if not user_info.key in curr_match.owners:
            curr_match.owners.append(user_info.key)
        key = curr_match.put()
      else:
        #create a new match
        match.status = 0 #pending_creation status
        match.created_by = user_info.key
        match.updated_by = user_info.key
        match.playground_id = None
        if not user_has_role(user_info, 'admin'):
          match.owners = []
          match.owners.append(user_info.key)
        key = match.put()
      
      if key is not None:
        mc_delete(cache_keys.get_match_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_match_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.sport is not None:
      to_model.sport = from_model.sport 
    if from_model.start_datetime is not None:
      to_model.start_datetime = from_model.start_datetime    
    if from_model.end_datetime is not None:
      to_model.end_datetime = from_model.end_datetime
    if from_model.result is not None:
      to_model.result = from_model.result
    if from_model.summary is not None:
      to_model.summary = from_model.summary    
    print 'to_model ' + str(to_model)