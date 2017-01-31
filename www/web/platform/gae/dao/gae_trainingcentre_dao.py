from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search 
import sys
sys.modules['ndb'] = ndb

from constants import SPORT_DICT, TRAINING_CENTRE
from web.utils.memcache_utils import mc_wrap, mc_delete, mc_get
from web.utils import cache_keys
from web.dao.trainingcentre_dao import TrainingCentreDao
from web.platform.gae.dao.gae_media_dao import NdbMediaDao
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT, PAGE_SIZE
from models import TrainingCentre, ReviewStats, Address, ContactInfo
from web.lib.utils import user_has_role
from web.utils.app_utils import normalize_sport_name
logger = logging.getLogger(__name__)
from google.appengine.datastore.datastore_query import Cursor

class MemTrainingCentreDao(TrainingCentreDao):

    def __init__(self, _trainingCentreDao):
      self.trainingCentreDao = _trainingCentreDao
        
    def get_record(self, id):
      trainingCentre = mc_wrap(cache_keys.get_trainingcentre_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.trainingCentreDao.get_record(id))
      return trainingCentre
    
    def get_search_keys(self, id):      
      return self.trainingCentreDao.get_search_keys(id)
    
    def get_suggest_keys(self, id):      
      return self.trainingCentreDao.get_suggest_keys(id)
  
    def get_recent(self, city_name=None, sport=None, no_records=8):
      return mc_wrap(cache_keys.get_recent_trainingcentre_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.trainingCentreDao.get_recent(city_name, sport, no_records))

    def get_featured(self, city_name=None, sport=None, no_records=4):
      return mc_wrap(cache_keys.get_featured_trainingcentre_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.trainingCentreDao.get_featured(city_name, sport, no_records))

    def get_popular(self, city_name=None, sport=None, no_records=8):
      return mc_wrap(cache_keys.get_popular_trainingcentre_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.trainingCentreDao.get_popular(city_name, sport, no_records))

    def get_active(self, city_name=None, sport=None, no_records=10):
      return mc_wrap(cache_keys.get_active_trainingcentre_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.trainingCentreDao.get_active(city_name, sport, no_records))
    
    def get_recommend(self, locality=None, sport=None, no_records=8):
      return mc_wrap(cache_keys.get_recommend_trainingcentre_cache_key(locality, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.trainingCentreDao.get_recommend(locality, sport, no_records))
    
    def query_by_alias(self, alias):
      return self.trainingCentreDao.query_by_alias(alias)

    def query_by_owner(self, user, status='all'):
      return self.trainingCentreDao.query_by_owner(user, status)    
      
    def search(self, status='all', curs=None, **params):
      return self.trainingCentreDao.search(self, status, curs, **params)

    def persist(self, trainingCentre, user_info):
      return self.trainingCentreDao.persist(trainingCentre, user_info)
  
class NdbTrainingCentreDao(TrainingCentreDao):
  mediaDao = NdbMediaDao()
    
  def get_record(self, trainingCentre_id):
    logger.info('NdbTrainingCentreDao:: DBHIT: get_record for %s ' % trainingCentre_id)
    return TrainingCentre.get_by_id(long(trainingCentre_id))
  
  def get_search_keys(self, id):
      logger.info('NdbTrainingCentreDao:: DBHIT: get_search_keys for trainingcentre')
      return mc_wrap(cache_keys.get_search_keys_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: None)
      
  def get_suggest_keys(self, id):
      logger.info('NdbTrainingCentreDao:: DBHIT: get_suggest_keys for trainingcentre')
      return mc_wrap(cache_keys.get_suggest_keys_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: None)
      
  def get_recent(self, city_name=None, sport=None, no_record=8):
      logger.info('NdbTrainingCentreDao:: DBHIT: get_recent for %s ' % no_record)
      trainingCentre_query = TrainingCentre.query(TrainingCentre.status == 2)
      if city_name is not None:
        trainingCentre_query = trainingCentre_query.filter(TrainingCentre.address.city == city_name)
      if sport is not None:
        trainingCentre_query = self.build_query_for_sport(trainingCentre_query, sport, True)
      trainingCentre_query = trainingCentre_query.order(-TrainingCentre.created_on)
      return trainingCentre_query.fetch(no_record)

  def get_featured(self, city_name=None, sport=None, no_record=4):
      logger.info('NdbTrainingCentreDao:: DBHIT: get_featured for %s ' % no_record)
      trainingCentre_query = TrainingCentre.query(TrainingCentre.status == 2, TrainingCentre.featured == True)
      if city_name is not None:
        trainingCentre_query = trainingCentre_query.filter(TrainingCentre.address.city == city_name)
      if sport is not None:
        trainingCentre_query = self.build_query_for_sport(trainingCentre_query, sport, True)
      trainingCentre_query = trainingCentre_query.order(-TrainingCentre.created_on)
      return trainingCentre_query.fetch(no_record)

  def get_popular(self, city_name=None, sport=None, no_record=8):
      logger.info('NdbTrainingCentreDao:: DBHIT: get_popular for %s ' % no_record)
      trainingCentre_query = TrainingCentre.query(TrainingCentre.status == 2)
      if city_name is not None:
        trainingCentre_query = trainingCentre_query.filter(TrainingCentre.address.city == city_name)
      if sport is not None:
        trainingCentre_query = self.build_query_for_sport(trainingCentre_query, sport, True)
      trainingCentre_query = trainingCentre_query.order(-TrainingCentre.review_stats.ratings_count, -TrainingCentre.created_on)
      return trainingCentre_query.fetch(no_record)

  def get_active(self, city_name=None, sport=None, no_record=10):
      logger.info('NdbTrainingCentreDao:: DBHIT: get_active for %s ' % city_name)
      trainingCentre_query = TrainingCentre.query(TrainingCentre.status == 2)
      if city_name is not None:
        trainingCentre_query = trainingCentre_query.filter(TrainingCentre.address.city == city_name)
      if sport is not None:
        trainingCentre_query = self.build_query_for_sport(trainingCentre_query, sport, False)
      trainingCentre_query = trainingCentre_query.order(-TrainingCentre.created_on)
      if no_record > -1:
        return trainingCentre_query.fetch(no_record)
      else: #return all. simulating -1 for app engine
        return trainingCentre_query.fetch()        
  
  def get_recommend(self, locality=None, sport=None, no_record=8):
      logger.info('NdbTrainingCentreDao:: DBHIT: get_recommend for %s, %s, %s ' % (locality, sport, no_record))
      trainingCentre_query = TrainingCentre.query(TrainingCentre.status == 2)
      if locality is not None and locality != '' and locality != 'None':
        trainingCentre_query = trainingCentre_query.filter(ndb.OR(TrainingCentre.address.locality == locality.lower() , TrainingCentre.address.city == locality.lower()))      
      if sport is not None and sport != '' and sport != 'None':
        trainingCentre_query = self.build_query_for_multisport(trainingCentre_query, sport)
      trainingCentre_query = trainingCentre_query.order(-TrainingCentre.created_on)
      if no_record > -1:
        return trainingCentre_query.fetch(no_record)
      else: #return all. simulating -1 for app engine
        return trainingCentre_query.fetch()
  
  def query_by_alias(self, alias):
      logger.info('NdbTrainingCentreDao:: DBHIT: query_by_alias for %s ' % alias)
      trainingCentre_query = TrainingCentre.query(TrainingCentre.alias == alias)
      trainingCentre = trainingCentre_query.fetch(1)
      return trainingCentre[0] if trainingCentre is not None and len(trainingCentre) > 0 else None

  def query_by_owner(self, user, status='all'):
    logger.info('NdbTrainingCentreDao:: DBHIT: query_by_owner for %s ' % user.email)    
    owner_query = TrainingCentre.query()
    if not user_has_role(user, 'admin'):
      owner_query = TrainingCentre.query(ndb.OR(TrainingCentre.owners == user.key, TrainingCentre.created_by == user.key, TrainingCentre.updated_by == user.key))    
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      owner_query = owner_query.filter(status == status_value)
    owner_query = owner_query.order(-TrainingCentre.updated_on)
    return owner_query.fetch()
  
  def search(self, status='all', curs=None, **params):
    logger.info('NdbTrainingCentreDao:: DBHIT: search %s  ' % params)
    #Using Search API for name searches.
    #TODO: Use search for name, locality, city, sport and geopt
    if ('name' in params): 
      return self.search_index(status, **params)
    else:
      return self.search_datastore(status, curs, **params)
  
  def search_datastore(self, status='all', curs=None, **params):    
    if status != 'all':
      status_value = STATUS_DICT.get(status)      
      logger.debug('status %d ' % (status_value))
      search_query = TrainingCentre.query(TrainingCentre.status == status_value)
    else:
      search_query = TrainingCentre.query()
    for key, value in params.items():
      #Constructing named queries for structured properties the round about way.
      # TO explore a better way later.
      if '.' in key and value is not None:
        struct, attr = key.split('.')
        if struct == 'address':
          search_query = search_query.filter(getattr(TrainingCentre.address, attr) == value)
        elif struct == 'contactInfo':
          search_query = search_query.filter(getattr(TrainingCentre.contact_info, attr) == value)
      else:
        if key == 'sport' and value is not None:
          search_query = self.build_query_for_sport(search_query, value, True)
        elif value is not None:
          search_query = search_query.filter(getattr(TrainingCentre, key) == value)
    #search_query = search_query.order(-TrainingCentre.updated_on)
    logger.debug('NdbTrainingCentreDao:: DBHIT: search query ' + str(search_query))
    #return search_query.fetch()
    
    search_forward = search_query.order(-TrainingCentre.updated_on)
    search_reverse = search_query.order(TrainingCentre.updated_on)
    
    # Fetch a page going forward.
    logger.info('NdbTrainingCentreDao:: DBHIT: Cursor ' + str(curs))
    if curs is not None:
        curs = Cursor(urlsafe=curs)
        next_data, next_curs, next_more = search_forward.fetch_page(PAGE_SIZE, start_cursor=curs)
        prev_data, prev_curs, prev_more = search_reverse.fetch_page(PAGE_SIZE, start_cursor=next_curs.reversed())
    else:
        next_data, next_curs, next_more = search_forward.fetch_page(PAGE_SIZE)
        if next_curs is not None:
            prev_data, prev_curs, prev_more = search_reverse.fetch_page(PAGE_SIZE, start_cursor=next_curs.reversed())
        else:
            prev_data = None
            prev_curs = None
            prev_more = None

    return (next_data, next_curs, next_more, prev_data, prev_curs, prev_more) 
  
  def search_index(self, user_ip, status, **params):
    logger.debug('Search Param Results: ' + str(params))
    #locality = params['address.locality']   #TODO: Hardcoded for testing. To be made generic.    
    
    trainingcenters = []
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      logger.debug('Status %d ' % (status_value))
      
    query_str = 'status:'+str(status_value)
      
    for key, value in params.items():
      if '.' in key and value is not None:
        struct, attr = key.split('.')
        if struct == 'address':
          if attr == 'city':
            query_str += ' AND city:'+str(value)
          if attr == 'locality':
            query_str += ' AND locality:'+str(value)          
      if key == 'sport' and value is not None:
        query_str += ' AND sport:'+str(value)
    
    try:
      index = search.Index(TRAINING_CENTRE)      
      sortopts = search.SortOptions(expressions=[
          search.SortExpression(expression='name', direction='ASCENDING')])
      search_query = search.Query(
          query_string=query_str,
          options=search.QueryOptions(
              limit=100,
              sort_options=sortopts))
      search_results = index.search(search_query)
      #logger.debug('Dao Search Result : ' + str(search_results))
            
    except search.Error:
      logger.exception("NdbTrainingCentreDao:: Search query failed for trainingcenters")
      #Retrieve the doc_id from the search results and then use that to query the datastore to fetch the entity
    
    keys = []
    for doc in search_results:
      keys.append(ndb.Key(TrainingCentre, long(doc.doc_id)))    
    
    cache_id = TRAINING_CENTRE+'_'+str(user_ip)    
    get_keys = mc_get(cache_keys.get_search_keys_cache_key(cache_id))    
    if get_keys is not None:
      del_keys = mc_delete(cache_keys.get_search_keys_cache_key(cache_id))
    add_keys = mc_wrap(cache_keys.get_search_keys_cache_key(cache_id), ENTITY_CACHE_EXPIRATION,
                      lambda x: keys)
    logger.info('No of Training Centers Added to cache : %s' % len(add_keys))
    return keys

  def search_index_suggest(self, user_ip, status, **params):
    logger.debug('Suggest Search Param Results: ' + str(params))
    #locality = params['address.locality']   #TODO: Hardcoded for testing. To be made generic.    
    
    suggest_trainingcenters = []
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      logger.debug('Status %d ' % (status_value))
      
    query_str = 'status:'+str(status_value)
      
    for key, value in params.items():      
      if key == 'latlong' and value is not None:
        query_str += ' AND distance(latlong, geopoint('+str(value)+')) < 5000'
      if '.' in key and value is not None:
        struct, attr = key.split('.')
        if struct == 'address':          
          if attr == 'locality':
            query_str += ' NOT locality:'+str(value)
            
    try:
      index = search.Index(TRAINING_CENTRE)          
      
      sortopts = search.SortOptions(expressions=[
          search.SortExpression(expression='name', direction='ASCENDING')])
      search_query = search.Query(
          query_string=query_str,
          options=search.QueryOptions(
              limit=PAGE_SIZE,
              sort_options=sortopts))
      search_results = index.search(search_query)
      #logger.debug('Suggest Search Result:' + str(search_results))
      
    except search.Error:
      logger.exception("NdbTrainingCentreDao:: Search query failed for suggest trainingcenters")
      #Retrieve the doc_id from the search results and then use that to query the datastore to fetch the entity
    
    keys = []    
    for doc in search_results:
      keys.append(ndb.Key(TrainingCentre, long(doc.doc_id)))
    
    #suggest_trainingcenters = ndb.get_multi(keys)    
    #return suggest_trainingcenters
    cache_id = 'suggest_'+str(TRAINING_CENTRE)+'_'+str(user_ip)
    get_keys = mc_get(cache_keys.get_suggest_keys_cache_key(cache_id))    
    if get_keys is not None:
      del_keys = mc_delete(cache_keys.get_suggest_keys_cache_key(cache_id))
    add_keys = mc_wrap(cache_keys.get_suggest_keys_cache_key(cache_id), ENTITY_CACHE_EXPIRATION,
                      lambda x: keys)
    logger.info('No of Suggest Training Centers Added to cache : %s' % len(add_keys))
    return keys
    
  #Very hacky implementation to handle NOT IN query, as appengine does not support it.
  #TODO: Find a better way to handle this.
  def build_query_for_sport(self, query, sport, normalize=False):
    sport = normalize_sport_name(sport) if normalize else sport.lower()
    if sport == 'others':
      sport_types = SPORT_DICT.keys()
      query = query.filter(ndb.AND(TrainingCentre.sport != sport_types[0], 
                                   TrainingCentre.sport != sport_types[1], 
                                   TrainingCentre.sport != sport_types[2], 
                                   TrainingCentre.sport != sport_types[3], 
                                   TrainingCentre.sport != sport_types[4]))
      query = query.order(TrainingCentre.sport)
    else:
      query = query.filter(TrainingCentre.sport == sport.lower())
    return query
  
  def build_query_for_multisport(self, query, sport):    
    sports = [x.strip() for x in sport.split(',')]
    if len(sports) > 0:
      multisports = []
      for sport in sports:
        multisports.append(TrainingCentre.sport == sport)
      query = query.filter(ndb.query.OR(*multisports))
      logger.debug("Sports String : " + str(multisports))      
    return query

  def status_change(self, trainingCentre, user_info):
    key = None
    if trainingCentre is not None:      
      if trainingCentre.key is not None:                
        trainingCentre.updated_by = user_info.key
        # change the status from current status
        if user_has_role(user_info, 'admin'):
          if trainingCentre.status == 1:
            trainingCentre.status += 1 #active status
          elif trainingCentre.status == 2:
            trainingCentre.status -= 1 #deactive status
        else:
          if trainingCentre.status == 0:
            trainingCentre.status += 1 #enable status
          else:
            trainingCentre.status -= trainingCentre.status #disable status
        key = trainingCentre.put()
      
      if key is not None:
        #update the search index
        self.update_search_index(key.id(), trainingCentre)        
        mc_delete(cache_keys.get_trainingcentre_cache_key(key.id()))
        mc_delete(cache_keys.get_recent_trainingcentre_cache_key())
      return key
  
  def persist(self, trainingCentre, user_info):
    key = None
    if trainingCentre is not None:
      curr_trainingCentre = None
      if trainingCentre.key is not None:
        curr_trainingCentre = self.get_record(trainingCentre.key.id())
      #If entry exists for the same trainingCentre, udpate the data
      if curr_trainingCentre is not None:
        self.copy_trainingCentre_model(curr_trainingCentre, trainingCentre)
        curr_trainingCentre.updated_by = user_info.key
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_trainingCentre.status = 1 #pending_approval status
          if not user_info.key in curr_trainingCentre.owners:
            curr_trainingCentre.owners.append(user_info.key)
        key = curr_trainingCentre.put()
      else:
        trainingCentre.status = 0 #pending_creation status
        trainingCentre.created_by = user_info.key
        trainingCentre.updated_by = user_info.key
        if not user_has_role(user_info, 'admin'):
          trainingCentre.owners = []
          trainingCentre.owners.append(user_info.key)
        key = trainingCentre.put()
      
      if key is not None:
        #update the search index
        self.update_search_index(key.id(), trainingCentre)
        #TODO: Make sure all the caches that has this entity is deleted here
        mc_delete(cache_keys.get_trainingcentre_cache_key(key.id()))
        mc_delete(cache_keys.get_recent_trainingcentre_cache_key())
        if trainingCentre.featured:
          mc_delete(cache_keys.get_featured_trainingcentre_cache_key())
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_trainingCentre_model(self, to_model, from_model):
    print 'from model ' + str(from_model)
    if from_model.name is not None:
      to_model.name = from_model.name 
    if from_model.sport is not None:
      to_model.sport = from_model.sport 
    if from_model.description is not None:
      to_model.description = from_model.description    
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

  def update_search_index(self, id, tc):
    tc_doc = search.Document(
      # As search documents cannot be updated and can only be replaced, for every create or update, we will replace the search document completely.
      # Hence using the datastore id for the search id as well. Retrieving the entity also becomes easier this way. 
      doc_id = str(id),
      # Store only the fields that are required to be searched upon. For retrievel, we will retrieve the id from search and use that to query the entity from the datastore.
      fields=[
       search.TextField(name='name', value=tc.name),
       search.TextField(name='caption', value=tc.caption),
       search.TextField(name='sport', value=tc.sport),
       search.TextField(name='locality', value=tc.address.locality),
       search.TextField(name='locality_id', value=tc.address.locality_id),
       search.TextField(name='city', value=tc.address.city),
       search.NumberField(name='status', value=tc.status),
       search.DateField(name='updated_on', value=datetime.date(tc.updated_on)),
       search.GeoField(name='latlong', value=search.GeoPoint(tc.address.latlong.lat, tc.address.latlong.lon))
       ])  
    
    try:
      index = search.Index(name=TRAINING_CENTRE)
      index.put(tc_doc)
    except search.Error:
      logger.exception('Storing training centre %s in search index failed' % id)
