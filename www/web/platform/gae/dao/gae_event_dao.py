from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search 
import sys
sys.modules['ndb'] = ndb

from constants import SPORT_DICT, EVENT
from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils import cache_keys
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT
from models import Event, ContactInfo
from web.lib.utils import user_has_role
from web.dao.event_dao import EventDao
from web.utils.app_utils import round_to_date
from web.platform.gae.dao.gae_media_dao import NdbMediaDao
logger = logging.getLogger(__name__)
from web.utils.app_utils import normalize_sport_name

class EventDTO:
  parent_event = Event()
  child_events = []
  
class MemEventDao(EventDao):

    def __init__(self, _eventDao):
     self.eventDao = _eventDao
        
    def get_record(self, id):
      event = mc_wrap(cache_keys.get_event_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_record(id))
      return event

    def get_recent(self, city_name=None, sport=None, locality_name=None, no_records=4):
      return mc_wrap(cache_keys.get_recent_event_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_recent(city_name, sport, locality_name, no_records))

    def get_ongoing(self, city_name=None, sport=None, locality_name=None, no_records=4):
      return mc_wrap(cache_keys.get_ongoing_event_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_ongoing(city_name, sport, locality_name, no_records))
    
    def get_ongoing_future(self, city_name=None, sport=None, locality_name=None, no_records=4):
      return mc_wrap(cache_keys.get_ongoing_future_event_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_ongoing_future(city_name, sport, locality_name, no_records))
      
    def get_upcoming(self, city_name=None, sport=None, locality_name=None, no_records=8):
      return mc_wrap(cache_keys.get_upcoming_event_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_upcoming(city_name, sport, locality_name, no_records))

    def get_featured(self, city_name=None, sport=None, no_records=4):
      return mc_wrap(cache_keys.get_featured_event_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_featured(city_name, sport, no_records))

    def get_popular(self, city_name=None, sport=None, no_records=4):
      return mc_wrap(cache_keys.get_popular_event_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_popular(city_name, sport, no_records))

    def get_active(self, city_name=None, sport=None, no_records=4):
      return mc_wrap(cache_keys.get_active_event_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_active(city_name, sport, no_records))
    
    def get_recommend(self, locality=None, sport=None, no_records=4):
      return mc_wrap(cache_keys.get_recommend_event_cache_key(locality, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_recommend(locality, sport, no_records))

    def get_child_events(self, entity_id, no_records=-1):
      return mc_wrap(cache_keys.get_event_children_cache_key(entity_id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.eventDao.get_child_events(entity_id, 'desc', no_records))

    def get_business_events(self, business_key, sort_order='desc', no_records=-1):
      return self.eventDao.get_business_events(business_key, sort_order, no_records)
    
    def query_by_alias(self, alias):
      return self.eventDao.query_by_alias(alias)

    def query_by_owner(self, user, status='all'):
      return self.eventDao.query_by_owner(user, status)    
    
    def search(self, status='all', **params):
      return self.eventDao.search(self, status, **params)
    
    def status_change(self, event, user_info):
      return self.eventDao.status_change(event, user_info)
  
    def persist(self, event, user_info):
      return self.eventDao.persist(event, user_info)
  
class NdbEventDao(EventDao):
  mediaDao = NdbMediaDao()    
  
  def get_record(self, event_id):
    logger.info('NdbEventDao:: DBHIT: get_record for %s ' % event_id)
    return Event.get_by_id(long(event_id))
  
  def get_business_events(self, business_key, sort_order='desc', no_records=-1):
    event_query = Event.query(Event.business_id == business_key, Event.status == 2)
    if sort_order == 'desc':
      event_query = event_query.order(-Event.end_datetime)
    else:
      event_query = event_query.order(Event.end_datetime)
    if no_records > -1:
      return event_query.fetch(no_records)
    else:
      return event_query.fetch()

  def get_child_events(self, parent_event_key, sort_order='desc', no_records=-1):
    child_event_query = Event.query(Event.parent_event_id == parent_event_key, Event.status == 2)
    if sort_order == 'desc':
      child_event_query = child_event_query.order(-Event.end_datetime)
    else:
      child_event_query = child_event_query.order(Event.end_datetime)
    if no_records > -1:
      return child_event_query.fetch(no_records)
    else:
      return child_event_query.fetch()
    
  #Returns the past events which got ended before now.
  def get_recent(self, city_name=None, sport=None, locality_name=None, no_records=4):
    logger.info('NdbEventDao:: DBHIT: get_recent for city %s, sport %s, locality %s, %s records' % (city_name, sport, locality_name, no_records))
    #Get only the parent events, with status approved
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2, Event.end_datetime < round_to_date(datetime.now())) 
    if city_name is not None and city_name != '' and city_name != 'None':
      event_query = event_query.filter(Event.address.city == city_name.lower())
    if locality_name is not None and locality_name != '' and locality_name != 'None':
      event_query = event_query.filter(Event.address.locality == locality_name.lower())
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_sport(event_query, sport)    
    event_query = event_query.order(-Event.end_datetime)
    if no_records > -1:
      return event_query.fetch(no_records)
    else:
      return event_query.fetch()

  #Returns the events that are happening currently
  #TODO: fix the start time and end time range properly. AppEngine limits inequality queries on 2 properties. Needs to be explored
  def get_ongoing(self, city_name=None, sport=None, locality_name=None, no_records=4):
    logger.info('NdbEventDao:: DBHIT: get_ongoing for city %s, sport %s, locality %s, %s records' % (city_name, sport, locality_name, no_records))
     #Get only the parent events, with status approved
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2, Event.start_datetime <= round_to_date(datetime.now()))
    if city_name is not None and city_name != '' and city_name != 'None':
      event_query = event_query.filter(Event.address.city == city_name.lower())
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_sport(event_query, sport)
    if locality_name is not None and locality_name != '' and locality_name != 'None':
      event_query = event_query.filter(Event.address.locality == locality_name.lower())
    event_query = event_query.order(-Event.start_datetime)
    if no_records > -1:
      return event_query.fetch(no_records)
    else:
      return event_query.fetch()
  
  def get_ongoing_future(self, city_name=None, sport=None, locality_name=None, no_records=4):
    logger.info('NdbEventDao:: DBHIT: get_ongoing_future for city %s, sport %s, locality %s, %s records' % (city_name, sport, locality_name, no_records))
     #Get only the parent events, with status approved
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2, Event.end_datetime >= round_to_date(datetime.now()))
    if city_name is not None and city_name != '' and city_name != 'None':
      event_query = event_query.filter(Event.address.city == city_name.lower())
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_sport(event_query, sport)
    if locality_name is not None and locality_name != '' and locality_name != 'None':
      event_query = event_query.filter(Event.address.locality == locality_name.lower())
    event_query = event_query.order(Event.end_datetime)
    if no_records > -1:
      return event_query.fetch(no_records)
    else:
      return event_query.fetch()
  
  #Returns the events that will start after now
  def get_upcoming(self, city_name=None, sport=None, locality_name=None, no_records=8):
    logger.info('NdbEventDao:: DBHIT: get_upcoming for city %s, sport %s, locality %s, %s records' % (city_name, sport, locality_name, no_records))
    #Get only the parent events, with status approved
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2, Event.start_datetime > round_to_date(datetime.now()))
    if city_name is not None and city_name != '' and city_name != 'None':
      event_query = event_query.filter(Event.address.city == city_name.lower())
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_sport(event_query, sport)
    if locality_name is not None and locality_name != '' and locality_name != 'None':
      event_query = event_query.filter(Event.address.locality == locality_name.lower())
    event_query = event_query.order(-Event.start_datetime)
    if no_records > -1:
      return event_query.fetch(no_records)
    else:
      return event_query.fetch()

  def get_featured(self, city_name=None, sport=None, no_records=4):
    logger.info('NdbEventDao:: DBHIT: get_featured for %s records' % no_records)
    #Get only the parent events with status approved and featured = true
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2, Event.featured == True)
    if city_name is not None and city_name != '' and city_name != 'None':
      event_query = event_query.filter(Event.address.city == city_name.lower())
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_sport(event_query, sport, True)
    event_query = event_query.order(-Event.created_on)
    return event_query.fetch(no_records)

  def get_popular(self, city_name=None, sport=None, no_records=4):
    logger.info('NdbEventDao:: DBHIT: get_popular for %s records' % no_records)
    #Get only the parent events with status approved sort by rating count
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2)
    if city_name is not None and city_name != '' and city_name != 'None':
      event_query = event_query.filter(Event.address.city == city_name.lower())
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_sport(event_query, sport, True)
    event_query = event_query.order(-Event.review_stats.ratings_count, -Event.created_on) 
    return event_query.fetch(no_records)

  def get_active(self, city_name=None, sport=None, no_records=4):
    logger.info('NdbEventDao:: DBHIT: get_active for %s records' % no_records)
    #Get only the parent events with status approved sort by rating count
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2)
    if city_name is not None and city_name != '' and city_name != 'None':
      event_query = event_query.filter(Event.address.city == city_name.lower())
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_sport(event_query, sport)
    event_query = event_query.order(-Event.created_on) 
    if no_records > -1:
      return event_query.fetch(no_records)
    else: #return all. simulating -1 for app engine
      return event_query.fetch()        
  
  def get_recommend(self, locality=None, sport=None, no_records=4):
    logger.info('NdbEventDao:: DBHIT: get_recommend for %s, %s, %s ' % (locality, sport, no_records))
    #Get only the parent events with status approved sort by rating count
    event_query = Event.query(Event.parent_event_id == None, Event.status == 2)
    if locality is not None and locality != '' and locality != 'None':
      event_query = event_query.filter(ndb.OR(Event.address.locality == locality.lower() , Event.address.city == locality.lower()))    
    if sport is not None and sport != '' and sport != 'None':
      event_query = self.build_query_for_multisport(event_query, sport)
    event_query = event_query.order(-Event.created_on) 
    if no_records > -1:
      return event_query.fetch(no_records)
    else: #return all. simulating -1 for app engine
      return event_query.fetch()

  def query_by_alias(self, alias):
    logger.info('NdbEventDao:: DBHIT: query_by_alias for %s ' % alias)
    event_query = Event.query(Event.alias == alias)
    event = event_query.fetch(1)
    return event[0] if event is not None and len(event) > 0 else None

  def query_by_owner(self, user, status='all'):
    logger.info('NdbEventDao:: DBHIT: query_by_owner for %s ' % user.email)
    owner_query = Event.query()
    if not user_has_role(user, 'admin'):
      owner_query = Event.query(ndb.OR(Event.owners == user.key, Event.created_by == user.key, Event.updated_by == user.key))
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      owner_query = owner_query.filter(status == status_value)
    owner_query = owner_query.order(-Event.updated_on)
    return owner_query.fetch()
  
  def search(self, status='all', **params):
    logger.info('NdbEventDao:: DBHIT: search %s  ' % params)
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      logger.debug('status %d ' % (status_value))
      search_query = Event.query(Event.status == status_value)
    else:
      search_query = Event.query()
    for key, value in params.items():
      #Constructing named queries for structured properties the round about way.
      # TO explore a better way later.
      if '.' in key and value is not None:
        struct, attr = key.split('.')
        if struct == 'contactInfo':
          search_query = search_query.filter(getattr(Event.contact_info, attr) == value)
      else:
        if key == 'sport' and value is not None:
          search_query = self.build_query_for_sport(search_query, value, True)
        elif value is not None:
          search_query = search_query.filter(getattr(Event, key) == value)
    search_query = search_query.order(-Event.updated_on)
    logger.debug('printing query %s ' % search_query)
    return search_query.fetch()
  
  #Very hacky implementation to handle NOT IN query, as appengine does not support it.
  #TODO: Find a better way to handle this.
  def build_query_for_sport(self, query, sport, normalize=False):
    sport = normalize_sport_name(sport) if normalize else sport.lower()
    if sport == 'others':
      #sport_types = SPORT_DICT.keys()
      #query = query.filter(ndb.AND(Event.sport != sport_types[0], 
      #                             Event.sport != sport_types[1], 
      #                             Event.sport != sport_types[2], 
      #                             Event.sport != sport_types[3], 
      #                             Event.sport != sport_types[4]))
      #query = query.order(Event.sport)
      
      query = query.filter(Event.sport == sport.lower())
    else:
      query = query.filter(Event.sport == sport.lower())
    return query
  
  def build_query_for_multisport(self, query, sport):    
    sports = [x.strip() for x in sport.split(',')]
    if len(sports) > 0:
      multisports = []
      for sport in sports:
        multisports.append(Event.sport == sport)
      query = query.filter(ndb.query.OR(*multisports))
      logger.debug("Sports String : " + str(multisports))      
    return query

  def status_change(self, event, user_info):
    key = None
    if event is not None:      
      if event.key is not None:                
        event.updated_by = user_info.key
        # change the status from current status
        if user_has_role(user_info, 'admin'):
          if event.status == 1:
            event.status += 1 #active status
          elif event.status == 2:
            event.status -= 1 #deactive status
        else:
          if event.status == 0:
            event.status += 1 #enable status
          else:
            event.status -= event.status #disable status
        key = event.put()
      
      if key is not None:
        #update the search index
        self.update_search_index(key.id(), event)
        #TODO: Make sure all the caches that has this entity is deleted here
        mc_delete(cache_keys.get_event_cache_key(key.id()))
        mc_delete(cache_keys.get_recent_event_cache_key())
        mc_delete(cache_keys.get_ongoing_event_cache_key())
        mc_delete(cache_keys.get_ongoing_future_event_cache_key())
        mc_delete(cache_keys.get_upcoming_event_cache_key())
        if event.featured:
          mc_delete(cache_keys.get_featured_event_cache_key())
      return key
  
  def persist(self, event, user_info):
    key = None
    if event is not None:
      curr_event = None
      if event.key is not None:
        curr_event = self.get_record(event.key.id())
      #If entry exists for the same event, udpate the data
      if curr_event is not None:
        self.copy_event_model(curr_event, event)
        event.parent_event_id = None
        curr_event.updated_by = user_info.key
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_event.status = 1 #pending_approval status
          if not user_info.key in curr_event.owners:
            curr_event.owners.append(user_info.key)
        key = curr_event.put()
      else:
        # create a new event        
        event.created_by = user_info.key
        event.updated_by = user_info.key
        event.parent_event_id = None
        if not user_has_role(user_info, 'admin'):
          event.owners = []
          event.owners.append(user_info.key)
          event.status = 0 #pending_creation status
        else:
          event.status = 1 #pending_approval status
        key = event.put()
      
      if key is not None:
        #update the search index
        self.update_search_index(key.id(), event)
        #TODO: Make sure all the caches that has this entity is deleted here
        mc_delete(cache_keys.get_event_cache_key(key.id()))
        mc_delete(cache_keys.get_recent_event_cache_key())
        mc_delete(cache_keys.get_ongoing_event_cache_key())
        mc_delete(cache_keys.get_ongoing_future_event_cache_key())
        mc_delete(cache_keys.get_upcoming_event_cache_key())
        if event.featured:
          mc_delete(cache_keys.get_featured_event_cache_key())
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_event_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.sport is not None:
      to_model.sport = from_model.sport 
    if from_model.description is not None:
      to_model.description = from_model.description
    if from_model.start_datetime is not None:
      to_model.start_datetime = from_model.start_datetime
    if from_model.end_datetime is not None:
      to_model.end_datetime = from_model.end_datetime
    if from_model.address.line1 is not None:
      to_model.address.line1 = from_model.address.line1
    if from_model.address.line2 is not None:
      to_model.address.line2 = from_model.address.line2
    if from_model.address.locality is not None:
      to_model.address.locality = from_model.address.locality    
    if from_model.address.city is not None:
      to_model.address.city = from_model.address.city
    if from_model.address.pin is not None:
      to_model.address.pin = from_model.address.pin
    if from_model.address.latlong is not None:
      to_model.address.latlong = from_model.address.latlong
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
    to_model.featured = from_model.featured
    print 'to_model ' + str(to_model)

  def update_search_index(self, id, event):
    event_doc = search.Document(
        # As search documents cannot be updated and can only be replaced, for every create or update, we will replace the search document completely.
        # Hence using the datastore id for the search id as well. Retrieving the entity also becomes easier this way. 
        doc_id = str(id),
        # Store only the fields that are required to be searched/sorted upon. For retrievel, we will retrieve the id from search and use that to query the entity from the datastore.
        fields=[
           search.TextField(name='name', value=event.name),
           search.TextField(name='caption', value=event.caption),
           search.TextField(name='sport', value=event.sport),
           search.TextField(name='locality', value=event.address.locality),
           search.TextField(name='locality_id', value=event.address.locality_id),
           search.TextField(name='city', value=event.address.city),
           search.DateField(name='start_datetime', value=event.start_datetime),
           search.DateField(name='end_datetime', value=event.end_datetime),
           search.NumberField(name='status', value=event.status),
           search.DateField(name='updated_on', value=datetime.date(event.updated_on)),
           search.GeoField(name='latlong', value=search.GeoPoint(event.address.latlong.lat, event.address.latlong.lon))
           ])  
    
    try:
      index = search.Index(name=EVENT)
      index.put(event_doc)
    except search.Error:
      logger.exception('Storing event %s in search index failed' % id)
