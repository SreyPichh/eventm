# standard library imports
import logging
import constants
from web.lib.basehandler import BaseHandler
from web.dao.dao_factory import DaoFactory
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT, PAGE_SIZE

from google.appengine.ext import ndb
import sys
sys.modules['ndb'] = ndb

logger = logging.getLogger(__name__)

class GenericSearchHandler(BaseHandler):
  
  def get(self, city_name=None, locality_name=None):
    return self.post(city_name, locality_name)
    
  def post(self, city_name=None, locality_name=None):
    type = str(self.request.get('type'))    
    if type == '' or type == 'None':
      return self.redirect_to('home')
    elif type == constants.EVENT:
      search_handler = EventSearchHandler(self.request, self.response)
    elif type == constants.PLAYGROUND:
      search_handler = PlaygroundSearchHandler(self.request, self.response)
    elif type == constants.TRAINING_CENTRE:
      search_handler = TrainingCentreSearchHandler(self.request, self.response)
    return search_handler.dispatch()

class PlaygroundSearchHandler(BaseHandler):

  playgroundDao =  DaoFactory.create_rw_playgroundDao()
  mediaDao =  DaoFactory.create_ro_mediaDao()
  importDao =  DaoFactory.create_rw_importDao()
  
  def get(self, city_name=None, locality_name=None):
    return self.post(city_name, locality_name)
    
  def post(self, city_name=None, locality_name=None):
    city_str = str(self.request.get('city-name'))
    locality_nav = str(self.request.get('nav-locality'))
    locality_home = str(self.request.get('pg-locality'))
    locality_str = locality_nav if locality_nav != '' else locality_home
    locality_id_nav = str(self.request.get('nav-locality_id'))
    locality_id_home = str(self.request.get('pg-locality_id'))
    locality_id_str = locality_id_nav if locality_id_nav != '' else locality_id_home
    
    name = str(self.request.get('name'))
    sport = str(self.request.get('sport'))
    pg_sport = str(self.request.get('pg-sport'))
    sport = pg_sport if pg_sport != '' and pg_sport != 'None' else sport
    city = city_name if city_name is not None else city_str
    locality = locality_name if locality_name is not None else locality_str
    logger.debug('playground search :: city %s, sport %s, locality %s' % (city, sport, locality))
    
    nav_type_str = str(self.request.get('nav'))
    nav_type = nav_type_str if nav_type_str != '' and nav_type_str != 'None' else None
    curs_str = str(self.request.get('page'))
    curs = curs_str if curs_str != '' and curs_str != 'None' else None
    remote_ip = self.request.remote_addr
     
    params = {}
    search_params = {}
    playgrounds = []
    playground_list = []
    playground_media = []
    
    if name != '' and name  != 'None': 
      search_params['name'] = name
    if sport != '' and sport  != 'None': 
      search_params['sport'] = sport
    if city != '' and city != 'None':
      params['city_name'] = city
      search_params['address.city'] = city
    if locality != '' and locality != 'None' and locality != 'all':
      search_params['address.locality'] = locality
      #logger.debug('Search Params : ' + str(search_params))
    
    page_id = 1
    if curs is not None:
      page_id = int(curs)
    else:
      playground_search = self.playgroundDao.search_index(remote_ip, 'approved', **search_params)
    
    playground_keys = self.playgroundDao.get_search_keys(constants.PLAYGROUND+'_'+str(remote_ip))
    
    total_entries = len(playground_keys)
    logger.debug('NO of playgrounds matched the search %s ' % total_entries)
    
    if total_entries > 0:
      total_pages = (total_entries/PAGE_SIZE)+1
      params['page_range'] = range(1, total_pages+1)
      
      offset = (page_id * PAGE_SIZE) - PAGE_SIZE
      limit = offset + PAGE_SIZE    
      playground_list = playground_keys[offset:limit]    
      playgrounds = ndb.get_multi(playground_list)   
      playground_media = self.mediaDao.get_primary_media(playgrounds, constants.PLAYGROUND)      
      logger.debug('Displayed Page No.%s Playgrounds from %s to %s' % (page_id, offset+1, limit))
    
    suggest_params = {}
    if len(playground_keys) < PAGE_SIZE and (locality_id_str != '' or locality != '' or curs is not None):
      suggest_playground_keys = []
      if curs is None:
        if locality_id_str != '': 
          locality_data = self.importDao.query_by_place_id(locality_id_str)
        elif locality != '':
          locality_data = self.importDao.query_by_place_name(locality.title())
    
        if locality_data:
          suggest_params['latlong'] = locality_data.latlong
          suggest_params['address.locality'] = locality_data.name
          suggest_playground_keys = self.playgroundDao.search_index_suggest(remote_ip, 'approved', **suggest_params)          
      else:
        suggest_playground_keys = self.playgroundDao.get_suggest_keys('suggest_'+str(constants.PLAYGROUND)+'_'+str(remote_ip))
        
      if suggest_playground_keys is not None:
        suggest_playgrounds = ndb.get_multi(suggest_playground_keys)
        params['suggest_playgrounds'] = suggest_playgrounds
        logger.debug('No of Suggested Search Result : %s' % len(suggest_playground_keys))
        #logger.debug('Suggested Search Result keys : ' + str(suggest_playground_keys))
        suggest_playground_media = self.mediaDao.get_primary_media(suggest_playgrounds, constants.PLAYGROUND)
        #logger.debug('Suggest Media: ' + str(suggest_playground_media))
        if len(suggest_playground_media) > 0:
          if len(playground_media) > 0:
            playground_media.update(suggest_playground_media)
          else:
            playground_media = suggest_playground_media
    
    params['types'] = constants.PLAYGROUND
    params['sport'] = sport
    params['locality_name'] = locality
    params['playgrounds'] = playgrounds
    params['playground_media'] = playground_media
    params['title'] = constants.PLAYGROUND
    logger.debug('Param Results: ' + str(params))
    return self.render_template('/app/search_results.html', **params)
    
class TrainingCentreSearchHandler(BaseHandler):

  trainingCentreDao =  DaoFactory.create_rw_trainingCentreDao()
  mediaDao =  DaoFactory.create_ro_mediaDao()

  def get(self, city_name=None, locality_name=None):
    return self.post(city_name, locality_name)
    
  def post(self, city_name=None, locality_name=None):
    city_str = str(self.request.get('city-name'))    
    locality_nav = str(self.request.get('nav-locality'))    
    locality_home = str(self.request.get('tc-locality'))
    locality_str = locality_nav if locality_nav != '' else locality_home
    locality_id_nav = str(self.request.get('nav-locality_id'))
    locality_id_home = str(self.request.get('tc-locality_id'))
    locality_id_str = locality_id_nav if locality_id_nav != '' else locality_id_home
    
    name = str(self.request.get('name'))
    sport = str(self.request.get('sport'))
    tc_sport = str(self.request.get('tc-sport'))
    sport = tc_sport if tc_sport != '' and tc_sport != 'None' else sport
    city = city_name if city_name is not None else city_str
    locality = locality_name if locality_name is not None else locality_str
    logger.debug('training center search :: city %s, sport %s, locality %s' % (city, sport, locality))
    
    nav_type_str = str(self.request.get('nav'))
    nav_type = nav_type_str if nav_type_str != '' and nav_type_str != 'None' else None
    curs_str = str(self.request.get('page'))
    curs = curs_str if curs_str != '' and curs_str != 'None' else None
    remote_ip = self.request.remote_addr
    
    params = {}
    search_params = {}
    trainingcenters = []
    tc_list = []
    tc_media = []
    
    if name != '' and name  != 'None':
      search_params['name'] = name
    if sport != '' and sport  != 'None': 
      search_params['sport'] = sport
    if city != '' and city != 'None':
      params['city_name'] = city
      search_params['address.city'] = city
    if locality != '' and locality != 'None' and locality != 'all':
      search_params['address.locality'] = locality
      #logger.debug('Search Params : ' + str(search_params))    
    
    page_id = 1
    if curs is not None:
      page_id = int(curs)
    else:
      tc_search = self.trainingCentreDao.search_index(remote_ip, 'approved', **search_params)
                
    tc_keys = self.trainingCentreDao.get_search_keys(constants.TRAINING_CENTRE+'_'+str(remote_ip))
    
    total_entries = len(tc_keys)
    logger.info('NO of Training Centers matched the search %s ' % total_entries)
    
    if total_entries > 0:
      total_pages = (total_entries/PAGE_SIZE)+1
      params['page_range'] = range(1, total_pages+1)
      
      offset = (page_id * PAGE_SIZE) - PAGE_SIZE
      limit = offset + PAGE_SIZE    
      tc_list = tc_keys[offset:limit]    
      trainingcenters = ndb.get_multi(tc_list)
      tc_media = self.mediaDao.get_primary_media(trainingcenters, constants.TRAINING_CENTRE)      
      logger.info('Displayed Page No.%s Training Centers from %s to %s' % (page_id, offset+1, limit))
    
    suggest_params = {}
    if len(tc_keys) < PAGE_SIZE and (locality_id_str != '' or locality != '' or curs is not None):
      suggest_tc_keys = []
      if curs is None:
        if locality_id_str != '': 
          locality_data = self.importDao.query_by_place_id(locality_id_str)
        elif locality != '':
          locality_data = self.importDao.query_by_place_name(locality.title())
        
        if locality_data:
          suggest_params['latlong'] = locality_data.latlong
          suggest_params['address.locality'] = locality_data.name          
          suggest_tc_keys = self.trainingCentreDao.search_index_suggest(remote_ip, 'approved', **suggest_params)          
      else:
        suggest_tc_keys = self.trainingCentreDao.get_suggest_keys('suggest_'+str(constants.TRAINING_CENTRE)+'_'+str(remote_ip))
      
      if suggest_tc_keys is not None:
        suggest_trainingcenters = ndb.get_multi(suggest_tc_keys)
        params['suggest_trainingcenters'] = suggest_trainingcenters
        logger.info('No of Suggested Search Result : %s' % len(suggest_tc_keys))
        #logger.debug('Suggested Search Result keys : ' + str(suggest_tc_keys))      
        suggest_tc_media = self.mediaDao.get_primary_media(suggest_trainingcenters, constants.TRAINING_CENTRE)
        #logger.debug('Suggest Media: ' + str(suggest_tc_media))
        if len(suggest_tc_media) > 0:
          if len(tc_media) > 0:
            tc_media.update(suggest_tc_media)
          else:
            tc_media = suggest_tc_media
    
    params['types'] = constants.TRAINING_CENTRE
    params['sport'] = sport
    params['locality_name'] = locality    
    params['trainingcenters'] = trainingcenters
    params['trainingcenters_media'] = tc_media
    params['title'] = constants.TRAINING_CENTRE
    #logger.debug('Param Results: ' + str(params))
    return self.render_template('/app/search_results.html', **params)

class EventSearchHandler(BaseHandler):

  eventDao =  DaoFactory.create_rw_eventDao()
  mediaDao =  DaoFactory.create_ro_mediaDao()

  def get(self, city_name=None, locality_name=None):
    return self.post(city_name, locality_name)
    
  def post(self, city_name=None, locality_name=None):
    city_str = str(self.request.get('city-name'))
    sport = str(self.request.get('sport'))
    #locality_str = str(self.request.get('se-locality'))
    locality_nav = str(self.request.get('nav-locality'))
    locality_home = str(self.request.get('se-locality'))
    locality_str = locality_nav if locality_nav != '' else locality_home
    #logger.debug('sporting event search :: locality_nav %s, locality_home %s, locality_str %s' % (locality_nav, locality_home, locality_str))
    
    se_sport = str(self.request.get('se-sport'))
    sport = se_sport if se_sport != '' and se_sport != 'None' else sport
    city = city_name if city_name is not None else city_str
    locality = locality_name if locality_name is not None else locality_str
    logger.debug('sporting event search :: city %s, sport %s, locality %s' % (city, sport, locality))

    recent_events = self.eventDao.get_recent(city, sport, locality, -1)
    ongoing_events = self.eventDao.get_ongoing(city, sport, locality, -1)
    ongoing_events_future = self.eventDao.get_ongoing_future(city, sport, locality, -1)
    future_events = self.eventDao.get_upcoming(city, sport, locality, -1)
    logger.debug(' recent_events %s ' % len(recent_events))
    logger.debug(' future_events %s ' % len(future_events))
    logger.debug(' ongoing_events %s ' % len(ongoing_events))
    logger.debug(' ongoing_events_future %s ' % len(ongoing_events_future))
    
    ongoing_upcoming_events = []
    ongoing_upcoming_events = [val for val in ongoing_events if val in ongoing_events_future]
    logger.debug(' ongoing_upcoming_events %s ' % len(ongoing_upcoming_events))
    
    for event in future_events:
      ongoing_upcoming_events.append(event)
    #for event in ongoing_events:
      #ongoing_upcoming_events.append(event)
      
    temp_events = []
    for event in recent_events:
      temp_events.append(event)
    for event in ongoing_upcoming_events:
      temp_events.append(event)
      
    event_media = self.mediaDao.get_primary_media(temp_events, constants.EVENT)
    logger.debug(' event_media %s ' % len(event_media))

    params = {}
    params['types'] = constants.EVENT
    params['sport'] = sport    
    params['locality_name'] = locality
    if city != '' and city != 'None':
      params['city_name'] = city
    
    params['recent_events'] = recent_events
    params['future_events'] = ongoing_upcoming_events
    logger.debug(' future_events %s ' % len(ongoing_upcoming_events))
    params['event_media'] = event_media
    params['title'] = constants.EVENT
    #logger.debug('Params to template ' + str(params))
    
    return self.render_template('/app/events_home.html', **params)
  