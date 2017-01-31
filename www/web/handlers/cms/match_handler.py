# standard library imports
import logging
import json

import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import ndb

import constants
from web.lib import utils
import cms_utils
from web.lib.basehandler import BaseHandler
from web.handlers.cms import cms_forms as forms
from models import Match
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import role_required

logger = logging.getLogger(__name__)

class ManageMatchHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
  eventDao = DaoFactory.create_rw_eventDao()
  matchDao = DaoFactory.create_rw_matchDao()
  teamDao = DaoFactory.create_rw_teamDao()
  playerDao = DaoFactory.create_rw_playerDao()
  
  @role_required('business')
  def get(self, event_id=None, match_id=None):
    params = {}
           
    import_url = self.uri_for('import-team')
    params['import_url'] = blobstore.create_upload_url(import_url)
    upload_url = self.uri_for('select-for-match')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    #params['continue_url'] = continue_url if continue_url != '' else upload_url
    status = self.request.get('status')
    match_status = status if status != '' else None
    params['title'] = 'Create New Match'
    
    if event_id is not None  and len(event_id) > 1:      
      self.form.event_id = event_id
      params['event_id'] = event_id
      params['teams'] = self.teamDao.query_by_owner(self.user_info)
      params['players'] = self.playerDao.query_by_owner(self.user_info)
      params['continue_url'] = continue_url
      #logger.debug('teams:  ' + str(params['teams']))
      if match_id is not None  and len(match_id) > 1:
        match = self.matchDao.get_record(match_id)
        params['title'] = 'Update - ' + str(match.name)
        participants = []
        for x in xrange(len(match.participants)):
          participants.append(match.participants[x].id())
        params['participants'] = participants
        logger.info('select participants: ' + str(params['participants']))
        if match_status is not None:
          logger.info('current status: %s' % match_status)
          key = self.matchDao.status_change(match, self.user_info)
          if key is not None:
            updated_match = self.matchDao.get_record(long(key.id()))
            logger.info('updated status : %s' % updated_match.status)
            if match_status == str(updated_match.status):
              logger.info('match status could not be changed.')
              message = ('match status could not be changed.')
              self.add_message(message, 'error')
            else:
              logger.info('match status succesfully changed.')
              message = ('match status succesfully changed.')
              self.add_message(message, 'success')
            return self.redirect(continue_url)
        else:
          upload_url = self.uri_for('edit-match', event_id = event_id, match_id = match_id)          
          params['media_upload_url'] = blobstore.create_upload_url(upload_url)
          self.form = forms.MatchForm(self, match)
          return self.render_template('/cms/create_match.html', **params)
      else:
        upload_url = self.uri_for('create-match', event_id = event_id)
        params['media_upload_url'] = blobstore.create_upload_url(upload_url)
        return self.render_template('/cms/create_match.html', **params)        
    
    params['continue_url'] = upload_url
    params['entity_name'] = 'Match'
    params['owner_event'] = self.eventDao.query_by_owner(self.user_info)
    return self.render_template('/cms/select_event.html', **params)

  @role_required('business')
  def post(self, event_id=None, match_id=None):
    params = {}

    if not self.form.validate():
      if event_id is not None and len(event_id) > 0:
        if match_id is not None and len(match_id) > 0:
          return self.get(event_id, match_id)
        else:
          return self.get(event_id)
      else:
        return self.get()
    
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    
    match = self.form_to_dao(match_id)
    logger.debug('match populated ' + str(match))
    event = self.eventDao.get_record(event_id)
    event_key = event.key

    if event_key is not None:
      logger.info('Event succesfully created for match')
      match.event_id = event_key      
      key = self.matchDao.persist(match, self.user_info)
      logger.debug('key ' + str(key))

      if key is not None:
        logger.info('match succesfully created/updated')
        message = ('match succesfully created/updated.')
        self.add_message(message, 'success')        
        if continue_url:
          return self.redirect(continue_url)
        else:
          return self.redirect_to('dashboard', **params)
    
    logger.error('match creation failed')
    message = ('match creation failed.')
    self.add_message(message, 'error')
    self.form = forms.MatchForm(self, event)
    return self.render_template('/cms/create_match.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.MatchForm(self)
  
  def form_to_dao(self, match_id):
    match = None
    if match_id is not None  and len(match_id) > 1:
      match = self.matchDao.get_record(long(match_id))
    else:
      match = Match()
    match.name = self.form.name.data
    match.sport = self.form.sport.data
    #Create an automatic alias for the match
    match.alias = utils.slugify(self.form.name.data)    
    match.start_datetime = self.form.start_datetime.data
    match.end_datetime = self.form.end_datetime.data
    match.result = self.form.result.data
    match.summary = self.form.summary.data
    match.participant_type = self.form.participant_type.data
    sel_team = self.request.get_all('team')
    sel_player = self.request.get_all('player')
    logger.debug('sel_team:  ' + str(sel_team))
    logger.debug('sel_player:  ' + str(sel_player))
    
    if match.participant_type == 'team':      
      if len(sel_team) > 0:        
        teams = []        
        teams_count = len(sel_team)
        logger.debug('Teams Count: ' + str(teams_count))
        for x in xrange(teams_count):
          teams.append(self.teamDao.get_record(sel_team[x]).key)        
        logger.debug('Participants ' + str(teams))        
        match.participants = teams        
    else:    
      if len(sel_player) > 0:        
        players = []        
        players_count = len(sel_player)
        logger.debug('Teams Count: ' + str(players_count))
        for x in xrange(players_count):
          players.append(self.playerDao.get_record(sel_player[x]).key)        
        logger.debug('Participants ' + str(players))        
        match.participants = players
    return match

