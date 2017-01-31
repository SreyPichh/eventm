# standard library imports
import logging
import json

import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import ndb

import constants
import cms_utils
from web.lib import utils
from web.lib.basehandler import BaseHandler
from web.handlers.cms import cms_forms as forms
from models import Team, Player, User, Media
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import user_required

logger = logging.getLogger(__name__)

class ManageTeamHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
  teamDao = DaoFactory.create_rw_teamDao()
  playerDao = DaoFactory.create_rw_playerDao()
  profileDao = DaoFactory.create_rw_profileDao()
  
  @user_required
  def get(self, team_id=None):
    params = {}
    
    import_url = self.uri_for('import-team')
    params['import_url'] = blobstore.create_upload_url(import_url)
    upload_url = self.uri_for('create-team')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    params['continue_url'] = continue_url
    #params['continue_url'] = continue_url if continue_url != '' else upload_url    
    #params['players'] = self.playerDao.query_by_owner(self.user_info)
    params['players'] = self.profileDao.query_by_all(self.user_info)
    params['title'] = 'Create New Team'
    
    if team_id is not None  and len(team_id) > 1:
      upload_url = self.uri_for('edit-team', team_id = team_id)
      team = self.teamDao.get_record(team_id)
      params['title'] = 'Update - ' + str(team.name)
      if team.logo:
        params['current_logo'] = images.get_serving_url(team.logo)
      self.form = forms.TeamForm(self, team)
      players = []
      for x in xrange(len(team.players)):
        players.append(team.players[x].id())
      params['sel_players'] = players
      params['media_upload_url'] = blobstore.create_upload_url(upload_url)
      return self.render_template('/cms/create_team.html', **params)
    else:
      params['media_upload_url'] = blobstore.create_upload_url(upload_url)
      return self.render_template('/cms/create_team.html', **params)        
    
    params['entity_name'] = 'Team'
    params['owner_teams'] = self.teamDao.query_by_owner(self.user_info)
    return self.render_template('/cms/dashboard.html', **params)

  @user_required
  def post(self, team_id=None):
    params = {}

    if not self.form.validate():
      if team_id is not None and len(team_id) > 0:
        return self.get(team_id)
      else:
        return self.get()
    
    upload_files = self.get_uploads('logo')  # 'logo' is file upload field in the form
    logger.debug('upload_files ' + str(upload_files))
    
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    team = self.form_to_dao(team_id)    
    if upload_files is not None and len(upload_files) > 0:
      blob_info = upload_files[0]
      team.logo = blob_info.key()
      team.logo_url = images.get_serving_url(blob_info.key())
      logger.info('Link to logo ' + images.get_serving_url(team.logo))
      
    logger.debug('team populated ' + str(team))
    key = self.teamDao.persist(team, self.user_info)
    logger.debug('key ' + str(key))

    if key is not None:      
      logger.info('team succesfully created/updated')
      message = ('team succesfully created/updated.')
      self.add_message(message, 'success')
      redirect_url = self.uri_for('view-team', team_id = key.id())
      if continue_url:
        return self.redirect(continue_url)
      else:
        return self.redirect(redirect_url)
    
    logger.error('team creation failed')
    message = ('team creation failed.')
    self.add_message(message, 'error')
    self.form = forms.TeamForm(self)
    return self.render_template('/cms/create_team.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.TeamForm(self) 

  def upload_players(self):
    players = []
    new_player_count = len(self.form.new_player)
    logger.info('No of New players %s' % new_player_count)
    for x in xrange(new_player_count):      
      player_obj = Player()
      player_obj.name = self.form.new_player.__getitem__(x).data['name']
      player_obj.email = self.form.new_player.__getitem__(x).data['email']
      #player_obj.phone = self.form.new_player.__getitem__(x).data['phone']
      player_obj.sport = self.form.sport.data
      #player_obj.teams = key
      logger.info('New Player Data: ' + str(player_obj))
      if player_obj.email != '':
        player_exist = self.playerDao.query_by_email(player_obj.email)
        logger.info('Exist Player Data: ' + str(player_exist))
        if player_exist is None:
          key = self.playerDao.persist(player_obj, self.user_info)
          players.append(key)
          logger.info('Add New Player %s' % player_obj.name)
        else:
          players.append(player_exist.key)
          logger.info('Skipped Already Exist of Player %s' % player_obj.name)
      else:
        logger.info('Skipped Empty Player Data')
    return players
    
  def form_to_dao(self, team_id):
    team = None
    players = []
    if team_id is not None  and len(team_id) > 1:
      team = self.teamDao.get_record(long(team_id))    
    else:
      team = Team()      
    team.name = self.form.name.data
    team.alias = utils.slugify(self.form.name.data)
    team.sport = self.form.sport.data
    team.category = self.form.category.data
    
    players = self.upload_players()
    sel_player = self.request.get_all('player')
    logger.debug('sel_player:  ' + str(sel_player))
    if len(sel_player) > 0:      
      players_count = len(sel_player)
      logger.debug('No of Selected Players %s' % players_count)
      for x in xrange(players_count):
        players.append(self.profileDao.get_record(sel_player[x]).key)
    
    logger.info('Total No of Players Mapped %s' % len(players))        
    logger.debug('Total Players Data: ' + str(players))    
    team.players = players
    return team

class ViewTeamHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
  teamDao = DaoFactory.create_rw_teamDao()
  playerDao = DaoFactory.create_rw_playerDao()
  profileDao = DaoFactory.create_rw_profileDao()
  mediaDao =  DaoFactory.create_ro_mediaDao()
  eventDao =  DaoFactory.create_rw_eventDao()
  
  @user_required
  def get(self, team_id=None):
    params = {}
    
    params['players'] = self.profileDao.query_by_all(self.user_info)
    if team_id is not None and len(team_id) > 1:
      team_info = self.teamDao.get_record(long(team_id))                  
      logger.debug('team_info : ' + str(team_info))
      #if team_info.logo:
        #params['team_logo'] = images.get_serving_url(team_info.logo)                 
      if team_info.players:
        players = []
        sel_players = []
        #for player in team_info.players:
        for x in xrange(len(team_info.players)):          
          players.append(self.profileDao.get_record(long(team_info.players[x].id())))
          sel_players.append(team_info.players[x].id())                
        logger.debug('team_players : ' + str(players))
        params['team_players'] = players
        params['sel_players'] = sel_players
        
      if team_info.owners:
        owners = []
        for owner in team_info.owners:            
          owners.append(self.user_model.get_by_id(long(owner.id())))
        params['team_owners'] = owners
        logger.debug('team_owners : ' + str(owners))
      
      params['user_info'] = self.user_info
      params['team_info'] = team_info
      params['title'] = str(team_info.name) + ' Team'
      upload_url = self.uri_for('edit-team-logo')
      params['media_upload_url'] = blobstore.create_upload_url(upload_url)
      upload_gallery_url = self.uri_for('upload-team-gallery')
      params['upload_gallery_url'] = blobstore.create_upload_url(upload_gallery_url)
      params['team_gallery'] = self.mediaDao.get_all_media(team_info.key, constants.TEAM)
      recommend_events = self.eventDao.get_recommend(self.user_info.locality, self.user_info.sport, 4)
      params['recommend_events'] = recommend_events
      event_media = self.mediaDao.get_primary_media(recommend_events, constants.EVENT)
      params['event_media'] = event_media
      
      return self.render_template('/cms/team_detail.html', **params)
  
  @webapp2.cached_property
  def form(self):
    return forms.TeamForm(self) 

class EditTeamPlayerHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
  teamDao = DaoFactory.create_rw_teamDao()
  playerDao = DaoFactory.create_rw_playerDao()
  profileDao = DaoFactory.create_rw_profileDao()
  
  @user_required
  def post(self, team_id=None):
    params = {}    
    
    team = self.form_to_dao(team_id)    
    logger.debug('team populated ' + str(team))
    key = self.teamDao.persist(team, self.user_info)
    logger.debug('key ' + str(key))

    if key is not None:      
      logger.info('team succesfully created/updated')
      message = ('team succesfully created/updated.')
      self.add_message(message, 'success')
      redirect_url = self.uri_for('view-team', team_id = key.id())
      if redirect_url:
        return self.redirect(redirect_url)
      else:
        return self.redirect_to('dashboard', **params)
    
    logger.error('team creation failed')
    message = ('team creation failed.')
    self.add_message(message, 'error')    
    return self.render_template('/cms/team_detail.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.TeamForm(self) 

  def upload_players(self):
    players = []
    new_player_count = len(self.form.new_player)
    logger.info('No of New players %s' % new_player_count) 
    sport = self.request.get('sport')
    
    for x in xrange(new_player_count):
      player_obj = Player()
      player_obj.name = self.form.new_player.__getitem__(x).data['name']
      player_obj.email = self.form.new_player.__getitem__(x).data['email']
      #player_obj.phone = self.form.new_player.__getitem__(x).data['phone']
      player_obj.sport = sport
      
      logger.info('New Player Data: ' + str(player_obj))
      if player_obj.email != '':
        player_exist = self.playerDao.query_by_email(player_obj.email)
        logger.info('Exist Player Data: ' + str(player_exist))
        if player_exist is None:
          key = self.playerDao.persist(player_obj, self.user_info)
          players.append(key)
          logger.info('Add New Player %s' % player_obj.name)
        else:
          players.append(player_exist.key)
          logger.info('Skipped Already Exist of Player %s' % player_obj.name)
      else:
        logger.info('Skipped Empty Player Data')
    return players
    
  def form_to_dao(self, team_id):
    team = None
    players = []
    if team_id is not None  and len(team_id) > 1:
      team = self.teamDao.get_record(long(team_id))    
    else:
      team = Team()   
    
    players = self.upload_players()
    sel_player = self.request.get_all('player')
    logger.debug('sel_player:  ' + str(sel_player))
    if len(sel_player) > 0:      
      players_count = len(sel_player)
      logger.debug('No of Selected Players %s' % players_count)
      for x in xrange(players_count):
        players.append(self.profileDao.get_record(sel_player[x]).key)
    
    logger.info('Total No of Players Mapped %s' % len(players))        
    logger.debug('Total Players Data: ' + str(players))    
    team.players = players
    return team

class EditTeamNameHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    team = Team.get_by_id(long(id))
    team.name = utils.stringify(self.request.get("value"))
    team.alias = utils.slugify(self.request.get("value"))
    logger.info('Id: %s Value: %s' % (id, team.name))
    team.put()
    logger.debug('Team Data: ' + str(team))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditTeamSportHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    team = Team.get_by_id(long(id))
    team.sport = utils.stringify(self.request.get("value"))    
    logger.info('Id: %s Value: %s' % (id, team.sport))
    team.put()
    logger.debug('Team Data: ' + str(team))    
    return

class EditTeamPreferDaysHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    team = Team.get_by_id(long(id))
    sel_days = self.request.get_all("value[]")    
    if len(sel_days) > 0:
      if 'None' in sel_days:
        sel_days.remove('None')
      team.prefer_days = ', '.join(sel_days)
    else:
      team.prefer_days = ''        
    logger.info('Id: %s Value: %s' % (id, team.prefer_days))
    team.put()
    logger.debug('Team Data: ' + str(team))    
    return

class EditTeamEventsNumHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    team = Team.get_by_id(long(id))
    team.events_num = utils.stringify(self.request.get("value"))    
    logger.info('Id: %s Value: %s' % (id, team.events_num))
    team.put()
    logger.debug('Team Data: ' + str(team))    
    return

class EditTeamCategoryHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    team = Team.get_by_id(long(id))
    team.category = utils.stringify(self.request.get("value"))    
    logger.info('Id: %s Value: %s' % (id, team.category))
    team.put()
    logger.debug('Team Data: ' + str(team))    
    return

class EditTeamLogoHandler(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):  
  
  def post(self):    
    upload_files = self.get_uploads('file')
    id = self.request.get("team_id")    
    team = Team.get_by_id(long(id))
    logger.debug('team detail : ' + str(team))
    logger.debug('upload_files : ' + str(upload_files))
    redirect_url = self.uri_for('view-team', team_id=id)
    if upload_files is not None and len(upload_files) > 0:
      blob_info = upload_files[0]
      team.logo = blob_info.key()
      team.logo_url = images.get_serving_url(blob_info.key())
      team.put()
      logger.info('Link to image ' + images.get_serving_url(team.logo))
    
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return self.redirect(redirect_url)

class UploadTeamGalleryHandler(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):  
  
  def post(self):
    upload_files = self.get_uploads('gallery_images')
    id = self.request.get("team_id")
    team = Team.get_by_id(long(id))
    redirect_url = self.uri_for('view-team', team_id = id )
    logger.info('Uploaded files: ' + str(upload_files))
    #logger.info('Get Request: ' + str(self.request.get()))
    if upload_files is not None and len(upload_files) > 0:
      files_count = len(upload_files)
      logger.info('no of files uploaded ' + str(files_count))
      for x in xrange(files_count):
        blob_info = upload_files[x]
        media_obj = Media()
        #media_obj.name = self.form.media.__getitem__(x).data['name']
        media_obj.type = constants.PHOTO
        media_obj.status = True
        #media_obj.primary = self.form.media.__getitem__(x).data['primary']
        media_obj.link = blob_info.key()
        media_obj.url = images.get_serving_url(blob_info.key())
        media_obj.entity_id = team.key
        media_obj.entity_type = constants.TEAM
        logger.info('Upload file detail: ' + str(media_obj))
        #self.mediaDao.persist(media_obj)
        media_obj.put()
        logger.info('Link to picture file ' + images.get_serving_url(media_obj.link))    
    return self.redirect(redirect_url)

class ManagePlayerHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
  teamDao = DaoFactory.create_rw_teamDao()
  playerDao = DaoFactory.create_rw_playerDao()

  @user_required
  def get(self, player_id=None):
    params = {}
  
    import_url = self.uri_for('import-team')
    params['import_url'] = blobstore.create_upload_url(import_url)
    upload_url = self.uri_for('create-player')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    params['continue_url'] = continue_url
    #params['continue_url'] = continue_url if continue_url != '' else upload_url
    params['teams'] = self.teamDao.query_by_owner(self.user_info)
    params['title'] = 'Create New Player'
    
    if player_id is not None  and len(player_id) > 1:
      upload_url = self.uri_for('edit-player', player_id = player_id)
      player = self.playerDao.get_record(player_id)
      params['title'] = 'Update - ' + str(player.name)
      self.form = forms.NewPlayerForm(self, player)
      teams = []
      for x in xrange(len(player.teams)):
        teams.append(player.teams[x].id())
      params['sel_teams'] = teams
      return self.render_template('/cms/create_player.html', **params)
    else:      
      return self.render_template('/cms/create_player.html', **params)
    
    params['entity_name'] = 'Player'
    params['all_players'] = self.playerDao.query_by_all(self.user_info)
    return self.render_template('/cms/dashboard.html', **params)

  @user_required
  def post(self, player_id=None):
    params = {}

    if not self.form.validate():
      if player_id is not None and len(player_id) > 0:        
        return self.get(player_id)
      else:
        return self.get()
    
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    player = self.form_to_dao(player_id)
    logger.debug('player populated ' + str(player))
    
    team_alias_name = utils.slugify(self.request.get('teamName'))
    if team_alias_name != '':
      team_exist = self.teamDao.query_by_team_alias(team_alias_name, self.user_info)
      logger.info('Exist Team for player: ' + str(team_exist))
      if team_exist is None:
        team_import_data = self.form_to_dao_team_auto(player)
        team_key = self.teamDao.persist(team_import_data, self.user_info)
        logger.info('New Team Created for %s with key %s' % (team_alias_name, team_key))
        player.teams = team_key
      else:
        player.teams = team_exist.key
                
    key = self.playerDao.persist(player, self.user_info)
    logger.debug('key ' + str(key))

    if key is not None:      
      logger.info('player succesfully created/updated')
      message = ('player succesfully created/updated.')
      self.add_message(message, 'success')
      if continue_url:
        return self.redirect(continue_url)
      else:
        return self.redirect_to('dashboard', **params)
    
    logger.error('player creation failed')
    message = ('player creation failed.')
    self.add_message(message, 'error')
    self.form = forms.NewPlayerForm(self)
    return self.render_template('/cms/create_player.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.NewPlayerForm(self)

  @webapp2.cached_property
  def importform(self):
    return forms.ImportTeamForm(self)

  def form_to_dao(self, player_id):
    player = None
    if player_id is not None  and len(player_id) > 1:
      player = self.playerDao.get_record(long(player_id))
    else:
      player = Player()
    player.name = self.form.name.data
    player.email = self.form.email.data
    #player.phone = self.form.phone.data
    player.sport = self.form.sport.data
    sel_team = self.request.get_all('team')
    logger.debug('sel_team:  ' + str(sel_team))
    if len(sel_team) > 0:        
      teams = []        
      teams_count = len(sel_team)
      logger.debug('Teams Count: ' + str(teams_count))
      for x in xrange(teams_count):
        teams.append(self.teamDao.get_record(sel_team[x]).key)
      logger.debug('Teams ' + str(teams))        
      player.teams = teams
    return player

  def form_to_dao_team_auto(self, player):
    try:
      team = Team()
      team.name = self.form.teamName.data
      #Create an automatic alias for the team
      team.alias = utils.slugify(self.form.teamName.data)
      team.sport = self.form.sport.data
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return team
