from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import images
import sys
sys.modules['ndb'] = ndb

from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT, PAGE_SIZE
from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils import cache_keys
from web.dao.team_dao import TeamDao, PlayerDao
from models import Team, Player
from web.lib.utils import user_has_role
logger = logging.getLogger(__name__)

class TeamDTO:
  team = Team()
  player = Player()
  
class MemTeamDao(TeamDTO):

    def __init__(self, _teamDao):
     self.teamDao = _teamDao
        
    def get_record(self, id):
     return mc_wrap(cache_keys.get_team_cache_key(id), ENTITY_CACHE_EXPIRATION,
                     lambda x: self.teamDao.get_record(id))
        
    def query_by_owner(self, user, status='all'):
      return self.teamDao.query_by_owner(user, status)
  
    def query_by_alias(self, alias, sport):
      return self.teamDao.query_by_alias(alias, sport)
  
    def query_by_team_alias(self, alias, user):
      return self.teamDao.query_by_team_alias(alias, user)
 
    def persist(self, team, user_info):
      return self.teamDao.persist(team, user_info)
  
class NdbTeamDao(TeamDTO):
    
  def get_record(self, team_id):
    logger.info('NdbTeamDao:: DBHIT: get_record for %s ' % team_id)
    return Team.get_by_id(long(team_id))  
  
  def query_by_owner(self, user, status='all', no_record=8):
    logger.info('NdbTeamDao:: DBHIT: query_by_owner for %s ' % user.email)
    owner_query = Team.query()
    if not user_has_role(user, 'admin'):
      owner_query = Team.query(ndb.OR(Team.owners == user.key, Team.created_by == user.key, Team.updated_by == user.key))
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      owner_query = owner_query.filter(status == status_value)    
    owner_query = owner_query.order(-Team.updated_on)
    if no_record > -1:
      return list(owner_query.fetch(no_record))
    else: #return all. simulating -1 for app engine
      return list(owner_query.fetch())
    #return owner_query.fetch()
  
  def query_by_alias(self, alias, sport):
    logger.info('NdbTeamDao:: DBHIT: query_by_alias for %s ' % alias)
    team_query = Team.query(Team.alias == alias, Team.sport == sport)
    team = team_query.fetch(1)
    return team[0] if team is not None and len(team) > 0 else None

  def query_by_team_alias(self, alias, user):
    logger.info('NdbTeamDao:: DBHIT: query_by_team_alias for %s ' % alias)
    team_query = Team.query(Team.alias == alias, Team.created_by == user.key)
    team = team_query.fetch(1)
    return team[0] if team is not None and len(team) > 0 else None  
  
  def persist(self, team, user_info):
    key = None
    if team is not None:
      curr_team = None
      if team.key is not None:
        curr_team = self.get_record(team.key.id())
      #If entry exists for the same team, udpate the data
      if curr_team is not None:
        self.copy_team_model(curr_team, team)        
        curr_team.updated_by = user_info.key
        
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_team.status = 1 #pending_approval status
          if not user_info.key in curr_team.owners:
            curr_team.owners.append(user_info.key)
        key = curr_team.put()
      else:
        #create a new team
        team.status = 0 #pending_creation status
        team.created_by = user_info.key
        team.updated_by = user_info.key
        if not user_has_role(user_info, 'admin'):
          team.owners = []
          team.owners.append(user_info.key)
        key = team.put()
      
      if key is not None:
        mc_delete(cache_keys.get_team_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_team_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.sport is not None:
      to_model.sport = from_model.sport    
    print 'to_model ' + str(to_model)

class MemPlayerDao(TeamDTO):

    def __init__(self, _playerDao):
     self.playerDao = _playerDao
        
    def get_record(self, id):
     return mc_wrap(cache_keys.get_player_cache_key(id), ENTITY_CACHE_EXPIRATION,
                     lambda x: self.playerDao.get_record(id))
    
    def query_by_owner(self, user, status='all'):
      return self.playerDao.query_by_owner(user, status)
  
    def query_by_all(self):
      return self.playerDao.query_by_all()
    
    def query_by_email(self, email):
      return self.playerDao.query_by_email(email)
  
    def persist(self, player, user_info):
      return self.playerDao.persist(player, user_info)
  
class NdbPlayerDao(TeamDTO):
    
  def get_record(self, player_id):
    logger.info('NdbplayerDao:: DBHIT: get_record for %s ' % player_id)
    return Player.get_by_id(long(player_id))
  
  def query_by_owner(self, user, status='all'):
    logger.info('NdbplayerDao:: DBHIT: query_by_owner for %s ' % user.email)
    owner_query = Player.query()
    if not user_has_role(user, 'admin'):
      owner_query = Player.query(ndb.OR(Player.owners == user.key, Player.created_by == user.key, Player.updated_by == user.key))    
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      owner_query = owner_query.filter(status == status_value)
    owner_query = owner_query.order(-Player.updated_on)
    return owner_query.fetch()

  def query_by_all(self):
    logger.info('NdbplayerDao:: DBHIT: get_all_record ')
    player_query = Player.query(Player.email != '')    
    return player_query.fetch()

  def query_by_email(self, email):
    logger.info('NdbPlayerDao:: DBHIT: query_by_email for %s ' % email)
    player_query = Player.query(Player.email == email)
    player = player_query.fetch(1)
    return player[0] if player is not None and len(player) > 0 else None

  def persist(self, player, user_info):
    key = None
    if player is not None:
      curr_player = None
      if player.key is not None:
        curr_player = self.get_record(player.key.id())
      #If entry exists for the same player, udpate the data
      if curr_player is not None:
        self.copy_player_model(curr_player, player)
        curr_player.updated_by = user_info.key
        
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_player.status = 1 #pending_approval status
          if not user_info.key in curr_player.owners:
            curr_player.owners.append(user_info.key)
        key = curr_player.put()
      else:
        #create a new player
        if player.name != '':
          player.status = 0 #pending_creation status
          player.created_by = user_info.key
          player.updated_by = user_info.key
          if not user_has_role(user_info, 'admin'):
            player.owners = []
            player.owners.append(user_info.key)
          key = player.put()
      
      if key is not None:
        mc_delete(cache_keys.get_player_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_player_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.email is not None:
      to_model.email = from_model.email
    if from_model.phone is not None:
      to_model.phone = from_model.phone
    if from_model.sport is not None:
      to_model.sport = from_model.sport
    print 'to_model ' + str(to_model)
