# standard library imports
import logging
import time

import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import ndb

from web.lib import utils
import cms_utils
from web.utils.app_utils import get_latlong_from_address
from web.lib.basehandler import BaseHandler
from web.handlers.cms import cms_forms as forms
from models import Match, Team, Player, Locality, Event, Playground, TrainingCentre
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import role_required
from web.lib.decorators import user_required
#import xlrd
import csv
import os
#from csv import excel_tab
import urllib
import unicodedata
from google.appengine.api import urlfetch
from xml.dom import minidom
from datetime import datetime

logger = logging.getLogger(__name__)

class ImportTeamHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):  
  
  eventDao =  DaoFactory.create_rw_eventDao()
  matchDao =  DaoFactory.create_rw_matchDao()
  teamDao =  DaoFactory.create_rw_teamDao()
  playerDao =  DaoFactory.create_rw_playerDao()
  
  @user_required
  def get(self):
    params = {}
    
    event_id = self.request.get('event_id')    
    upload_field = self.request.get('importfile')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    logger.info('Continue Url: ' + str(continue_url))
    
    if upload_field != '':
      upload_files = self.get_uploads('importfile')
      logger.info('Upload Datas: ' + str(upload_files))
      blob_info = upload_files[0]
      start_record = 1
      upload_count = self.process_csv(blob_info, start_record, event_id)
      self.add_message(str(upload_count) + ' entities created successfully.', 'success')
      if continue_url:
        return self.redirect(continue_url)
      else:
        return self.redirect_to('dashboard')
    
    upload_url = self.uri_for('import-team')    
    params['title'] = 'Import Team'
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    return self.render_template('/cms/import.html', **params)

  @user_required
  def post(self):
    if not self.form.validate():
      return self.get()
    
    start_record = int(str(self.request.get('linenum')))
    upload_field = self.request.get('importfile')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    if upload_field != '':
      upload_files = self.get_uploads('importfile')  # 'file' is file upload field in the form
      logger.info('Upload Datas: ' + str(upload_files))
      blob_info = upload_files[0]
      start_record = start_record if start_record != '' else 1
      upload_count = self.process_csv(blob_info, start_record)
      self.add_message(str(upload_count) + ' entities created successfully.', 'success')
      if continue_url:
        return self.redirect(continue_url)
      else:
        return self.redirect_to('import-team')
    logger.error('Empty upload file field select correct file')
    message = ('Empty upload file field select correct file')
    self.add_message(message, 'error')
    return self.redirect_to('import-team')

  def process_csv(self, blob_info, start_record, event_id=None):
    update = {}  
    upload_count = 0
    row_count = 0
      
    blob_reader = blobstore.BlobReader(blob_info.key())
    datareader = csv.reader(blob_reader)
    
    for row in datareader:
      row_count += 1
      if row_count >= (start_record + 1): #to skip the header row
        logger.info('Starting to parse %s, %s' % (row_count, row[1]))
        entity_type = row[0].lower()
        update['name'] = utils.stringify(row[1])
        # Name is mandatory for all entities
        if update['name'] == '':
          logger.error('Name is empty. Skipping this record')
          continue        
        alias_name = utils.slugify(update['name'].lower())
        
        # Event Id check for matches
        if event_id is not None and len(event_id) > 1:
          event_data = self.eventDao.get_record(event_id)          
          event_alias_name = event_data.alias
        else:
          event_alias_name = ''

        try:          
          update['sport'] = utils.stringify(row[2]).lower()
          
          if entity_type == 'match':
            update['start_datetime'] = datetime.strptime(row[3],'%d-%m-%Y %I:%M%p')
            update['end_datetime'] = datetime.strptime(row[4],'%d-%m-%Y %I:%M%p')
            update['result'] = utils.stringify(row[5])
            event_alias_name = utils.slugify(row[6].lower()) if row[6] != '' else event_alias_name
            update['participant_type'] = utils.stringify(row[7]).lower()
          elif entity_type == 'player':
            update['email'] = utils.stringify(row[3])
            update['phone'] = utils.stringify(row[4])
            update['teamName'] = utils.stringify(row[5])
            team_alias_name = utils.slugify(update['teamName'].lower())
          
          logger.debug('Constructed Structure for upload ' + str(update))
          logger.info('Entity type to be created, ' + entity_type)
          
          if entity_type == 'match':
            import_data = self.form_to_dao_match(alias_name, **update)
          elif entity_type == 'team':
            import_data = self.form_to_dao_team(alias_name, **update)
          elif entity_type == 'player':
            import_data = self.form_to_dao_player(alias_name, **update)             
            
          logger.debug('Populated File Data ' + str(import_data))
          
          if entity_type == 'match':
            event = self.eventDao.query_by_alias(event_alias_name)
            if event is not None:
              match_exist = self.matchDao.query_by_alias(alias_name, event.key, update['sport'])
              if match_exist is None:
                import_data.event_id = event.key
                key = self.matchDao.persist(import_data, self.user_info)
                upload_count += 1
                logger.info('New Match Created for %s with key %s' % (alias_name, key))
              else:
                logger.error('Already Exist of %s:%s' % (entity_type, update['name']))
            else:              
              logger.error('Event Name %s doesnot exist' %(event_alias_name))
          elif entity_type == 'team':
            team_exist = self.teamDao.query_by_alias(alias_name, update['sport'])
            logger.info('Team Exist Data: ' + str(team_exist))
            if team_exist is None:              
              key = self.teamDao.persist(import_data, self.user_info)
              upload_count += 1
              logger.info('New Team Created for %s with key %s' % (alias_name, key))
            else:
              logger.error('Already Exist of %s:%s' % (entity_type, update['name']))
          elif entity_type == 'player':
            player_exist = self.playerDao.query_by_email(update['email'])
            logger.info('Player Exist Data: ' + str(player_exist))
            if player_exist is None:
              team_exist = self.teamDao.query_by_team_alias(team_alias_name, self.user_info)
              logger.info('Exist Team for player: ' + str(team_exist))
              if team_exist is None:
                team_import_data = self.form_to_dao_team_auto(team_alias_name, **update)
                team_key = self.teamDao.persist(team_import_data, self.user_info)
                logger.info('New Team Created for %s with key %s' % (team_alias_name, team_key))
                import_data.teams = team_key                
              else:
                import_data.teams = team_exist.key
              key = self.playerDao.persist(import_data, self.user_info)
              upload_count += 1
              logger.info('New Player Created for %s with key %s' % (alias_name, key))      
            else:
              logger.error('Already Exist of %s:%s' % (entity_type, update['name']))          
        
          if key is not None:
            logger.info(str(entity_type) + ' succesfully created/updated')
          else:
            logger.error('Already Exist of %s:%s' % (entity_type, update['name']))
  
        except StandardError as e:
          #skipping to next record
          logger.error('Error occured, %s, for %s' % (str(e), alias_name))
      else:
        logger.info("skipping record number, %s " % row_count)
    return upload_count
    

  @webapp2.cached_property
  def form(self):
    return forms.ImportForm(self)  
  
  def form_to_dao_match(self, alias_name, **update):
    try:
      match = Match()
      match.name = update['name']
      #Create an automatic alias for the match
      match.alias = alias_name      
      match.sport = update['sport']
      match.participant_type = update['participant_type']
      match.start_datetime = update['start_datetime']
      match.end_datetime = update['end_datetime']
      match.result = update['result']      
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return match

  def form_to_dao_team(self, alias_name, **update):
    try:
      team = Team()
      team.name = update['name']
      #Create an automatic alias for the team
      team.alias = alias_name      
      team.sport = update['sport']
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return team
  
  def form_to_dao_team_auto(self, team_alias_name, **update):
    try:
      team = Team()
      team.name = update['teamName']
      #Create an automatic alias for the team
      team.alias = team_alias_name      
      team.sport = update['sport']
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return team

  def form_to_dao_player(self, alias_name, **update):
    try:
      player = Player()
      player.name = update['name']      
      player.email = update['email']
      player.phone = update['phone']
      player.sport = update['sport']
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return player

class SaveLocalityHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  importDao =  DaoFactory.create_rw_importDao()
  
  @user_required
  def get(self):
    params = {}    
    upload_url = self.uri_for('save-locality')
    params['title'] = 'Save Locality'
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    return self.render_template('/cms/save_locality.html', **params)
  
  @user_required
  def post(self):
    params = {}
    locality_count = 0
    
    if not self.form.validate():      
      return self.get()
    
    lat = self.request.get('lat')
    long = self.request.get('long')
    radius = self.request.get('radius')
    limit = self.request.get('limit')
    api_key = self.request.get('key')    
    
    feed_url = 'http://www.geoplugin.net/extras/nearby.gp?lat='+lat+'&long='+long+'&limit='+limit+'&radius='+radius+'&format=xml'
    logging.info('feed url %s' % feed_url)
    root = self.parse(feed_url)
    for item in root.getElementsByTagName('geoPlugin_nearby'):
      try:
        place_name = unicodedata.normalize('NFKD', unicode(item.getElementsByTagName('geoplugin_place')[0].firstChild.data)).encode('ascii','ignore')
        logger.info('Place: %s' % place_name)
        
        newfeed_url = 'https://maps.googleapis.com/maps/api/place/autocomplete/xml?types=(regions)&input='+urllib.quote(place_name)+'&key='+api_key
        logging.info('newfeed url %s' % newfeed_url)
        newroot = self.parse(newfeed_url)
        auto_status = newroot.getElementsByTagName('status')[0].firstChild.data
        logger.info('Auto Status: %s ' % auto_status)
        if auto_status == 'OK':
          for items in newroot.getElementsByTagName('prediction'):
            try:            
              place_id = items.getElementsByTagName('place_id')[0].firstChild.data
              place_name = items.getElementsByTagName('value')[0].firstChild.data #description
              logger.info('Place Name: %s Place Id: %s ' %(place_name, place_id))              
              locality_count = self.process_locality(place_name, place_id, api_key)           
            except IndexError, ValueError:
              pass
        else:
          logger.error('Error: %s' % auto_status)
      except IndexError, ValueError:
        pass
        
    self.add_message(str(locality_count) + ' localities created successfully.', 'success')      
    #logger.error('Empty upload file field select correct file')
    #message = ('Empty upload file field select correct file')
    #self.add_message(message, 'error')
    return self.redirect_to('save-locality')    
    
  @webapp2.cached_property
  def form(self):
    return forms.SaveLocalityForm(self)

class SearchUpdateHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):  
  eventDao =  DaoFactory.create_rw_eventDao()
  playgroundDao  = DaoFactory.create_rw_playgroundDao()
  trainingCentreDao = DaoFactory.create_rw_trainingCentreDao()
  
  @user_required
  def get(self):
    params = {}
    upload_url = self.uri_for('search-update')
    params['title'] = 'Search Update'
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    return self.render_template('/cms/search_update.html', **params)
  
  @user_required
  def post(self):
    params = {}
    datas = []
    datas_count = 0
    type = self.request.get('type')
    logger.info('Type: %s' % type)
    
    if type != 'None':
      if type == 'event':
        datas = Event.query().fetch()
      elif type == 'playground':
        datas = Playground.query().fetch()
      elif type == 'trainingcentre':
        datas = TrainingCentre.query().fetch()
        
      for data in datas:        
        if data.address.latlong is None:
          latitude, longitude = get_latlong_from_address(data.address)
          if latitude is not None and longitude is not None:
            data.address.latlong = ndb.GeoPt(latitude,longitude)
            logger.info('New Lat Long: ' + str(data.address.latlong))
        logger.info('Populated Data: ' + str(data))
        
        if type == 'event':
          key = self.eventDao.persist(data, self.user_info)
        elif type == 'playground':
          key = self.playgroundDao.persist(data, self.user_info)
        elif type == 'trainingcentre':
          key = self.trainingCentreDao.persist(data, self.user_info)       
        
        if key is not None:
          datas_count += 1
          logger.info(str(key.id()) + ' succesfully search updated')
      logger.info('%s %s Entities Updated Search Successfully' %(datas_count,type))
      message = ('%s %s Entities Updated Search Successfully' %(datas_count,type))
      self.add_message(message, 'success')
      return self.redirect_to('search-update')
  
    logger.error('Select anyone of Type')
    message = ('Select anyone of Type')
    self.add_message(message, 'error')
    return self.redirect_to('search-update')
