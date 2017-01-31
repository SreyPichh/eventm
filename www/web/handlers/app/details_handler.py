# standard library imports
import logging
import constants
from web.utils.app_utils import get_default_city, get_event_state
from web.lib.basehandler import BaseHandler
from web.dao.dao_factory import DaoFactory
from google.appengine.api import images
from google.appengine.ext import blobstore

logger = logging.getLogger(__name__)

class PlaygroundDetailsHandler(BaseHandler):

  playgroundDao =  DaoFactory.create_ro_playgroundDao()
  mediaDao =  DaoFactory.create_ro_mediaDao()
  
  def get(self, city_name, locality_name, entity_id, entity_alias):
    logger.debug('Playground details for city %s, locality %s, id %s, alias %s ' % (city_name, locality_name, entity_id, entity_alias))
    if self.request.query_string != '':
      query_string = '?' + self.request.query_string
    else:
      query_string = ''
    continue_url = self.request.path_url + query_string
    
    if entity_id is None:
      message = ('Invalid Playground ID.')
      self.add_message(message, 'warning')
      self.redirect_to('home')
    else:
      playground = self.playgroundDao.get_record(entity_id)
      if playground is None:
        message = ('Playground could not be retrieved.')
        self.add_message(message, 'warning')
        self.redirect_to('home')
      else:
        params = {}
        params['playground'] = playground
        params['types'] = constants.PLAYGROUND
        params['sport'] = playground.sport
        params['city_name'] = playground.address.city
        params['locality_name'] = playground.address.locality
        params['media'] = self.mediaDao.get_active_media(playground.key, playground.sport, constants.PLAYGROUND)
        params['continue_url'] = continue_url
        params['upload_cover_url'] = blobstore.create_upload_url(self.uri_for('upload-playground-cover', **{'continue': continue_url}))
        params['enquire_url'] = self.uri_for('enquire-playground', **{'continue': continue_url})
        params['title'] = playground.name
        all_media = self.mediaDao.get_all_media(playground.key, constants.PLAYGROUND)
        current_media = []
        for photo in all_media:
          current_media.append({'name': photo.name, 'url':images.get_serving_url(photo.link), 'status': photo.status, 'primary': photo.primary})
        params['current_media'] = current_media
        if playground.cover:
          params['pg_cover'] = images.get_serving_url(playground.cover)
        return self.render_template('/app/pg_details1.html', **params)
        
class TrainingCentreDetailsHandler(BaseHandler):

  trainingcentreDao =  DaoFactory.create_ro_trainingCentreDao()  
  mediaDao =  DaoFactory.create_ro_mediaDao()
  
  def get(self, city_name, locality_name, entity_id, entity_alias):
    logger.debug('Training Centre details for city %s, locality %s, id %s, alias %s ' % (city_name, locality_name, entity_id, entity_alias))
    if self.request.query_string != '':
      query_string = '?' + self.request.query_string
    else:
      query_string = ''
    continue_url = self.request.path_url + query_string
    
    if entity_id is None:
      message = ('Invalid Training Centre ID.')
      self.add_message(message, 'warning')
      self.redirect_to('home')
    else:
      tc = self.trainingcentreDao.get_record(entity_id)      
      if tc is None:
        message = ('Training Centre could not be retrieved.')
        self.add_message(message, 'warning')
        return
      else:
        params = {}
        params['tc'] = tc
        params['types'] = constants.TRAINING_CENTRE
        params['sport'] = tc.sport
        params['city_name'] = tc.address.city
        params['locality_name'] = tc.address.locality
        params['media'] = self.mediaDao.get_active_media(tc.key, tc.sport, constants.TRAINING_CENTRE)
        params['continue_url'] = continue_url
        params['upload_cover_url'] = blobstore.create_upload_url(self.uri_for('upload-trainingcentre-cover', **{'continue': continue_url}))
        params['enquire_url'] = self.uri_for('enquire-trainingcentre', **{'continue': continue_url})
        params['title'] = tc.name        
        all_media = self.mediaDao.get_all_media(tc.key, constants.TRAINING_CENTRE)
        current_media = []
        for photo in all_media:
          current_media.append({'name': photo.name, 'url':images.get_serving_url(photo.link), 'status': photo.status, 'primary': photo.primary})
        params['current_media'] = current_media
        if tc.cover:
          params['tc_cover'] = images.get_serving_url(tc.cover)
          
        return self.render_template('/app/tc_details1.html', **params)
        
class EventDetailsHandler(BaseHandler):

  eventDao =  DaoFactory.create_ro_eventDao()
  mediaDao =  DaoFactory.create_ro_mediaDao()
  matchDao = DaoFactory.create_ro_matchDao()
  teamDao = DaoFactory.create_rw_teamDao()
  registerDao = DaoFactory.create_rw_registerDao()  
  
  def get(self, city_name, entity_id, entity_alias):
    logger.debug('Event details for city %s, id %s, alias %s ' % (city_name, entity_id, entity_alias))
    if self.request.query_string != '':
      query_string = '?' + self.request.query_string
    else:
      query_string = ''
    continue_url = self.request.path_url + query_string
    
    if entity_id is None:
      message = ('Invalid Event ID.')
      self.add_message(message, 'warning')
      self.redirect_to('home')
    else:
      event = self.eventDao.get_record(entity_id)
      if event is None:
        message = ('Event could not be retrieved.')
        self.add_message(message, 'warning')
        return
      else:
        past_events = []
        future_events = []
        other_events = self.eventDao.get_business_events(event.business_id)
        if other_events and len(other_events) > 0:
          for other_event in other_events:
            if other_event.key.id() != event.key.id(): 
              if get_event_state(other_event) == 'past':
                past_events.append(other_event)
              else:
                future_events.append(other_event)
                 
        event_media = self.mediaDao.get_primary_media(other_events, constants.EVENT)
                 
        params = {}        
        params['event'] = event
        params['types'] = constants.EVENT
        params['sport'] = event.sport
        params['city_name'] = event.address.city
        params['locality_name'] = event.address.locality
        params['past_events'] = past_events if len(past_events) > 0 else None 
        params['future_events'] = future_events if len(future_events) > 0 else None
        params['event_media'] = event_media
        params['media'] = self.mediaDao.get_active_media(event.key, event.sport, constants.EVENT)
        params['matches'] = self.matchDao.get_matches_for_event(event.key, self.user_info)
        params['continue_url'] = continue_url
        params['event_state'] = get_event_state(event)
        params['title'] = event.name
        
        if self.user_info:
          register_url = self.uri_for('event-register')
          params['teams'] = self.teamDao.query_by_owner(self.user_info)
          event_reg = self.registerDao.query_by_reg_user_id(event.key, self.user_info)
          logger.info('Event Registered Details: ' + str(event_reg))
          
          if event_reg:
            params['reg_type'] = event_reg.reg_type
            register_url = self.uri_for('edit-event-register', record_id = event_reg.key.id(), **{'continue': continue_url})            
            if event_reg.team_id:
              params['reg_teams'] = [x.id() for x in event_reg.team_id]
              logger.info('Event Registered Teams : ' + str(params['reg_teams']))
            if event_reg.player_id:
              params['reg_players'] = [x.id() for x in event_reg.player_id]
              logger.info('Event Registered Players : ' + str(params['reg_players']))
          params['register_url'] = register_url
          
        if event.sport == "cricket":
          return self.render_template('/app/event_details_cricket.html', **params)
        else:
          return self.render_template('/app/event_details.html', **params)
    