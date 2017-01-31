from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import search 
import sys
sys.modules['ndb'] = ndb

from constants import SPORT_DICT, PLAYGROUND
from web.utils.memcache_utils import mc_wrap, mc_delete, mc_get
from web.utils import cache_keys
from web.dao.playground_dao import PlaygroundDao
from web.platform.gae.dao.gae_media_dao import NdbMediaDao
from settings import ENTITY_CACHE_EXPIRATION, STATUS_DICT, PAGE_SIZE
from models import Playground, ReviewStats, Address, ContactInfo
from web.lib.utils import user_has_role
from web.utils.app_utils import normalize_sport_name
logger = logging.getLogger(__name__)
from google.appengine.datastore.datastore_query import Cursor

class MemPlaygroundDao(PlaygroundDao):

    def __init__(self, _playgroundDao):
     self.playgroundDao = _playgroundDao
        
    def get_record(self, id):
      playground = mc_wrap(cache_keys.get_playground_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.playgroundDao.get_record(id))
      return playground    
    
    def get_search_keys(self, id):      
      return self.playgroundDao.get_search_keys(id)
    
    def get_suggest_keys(self, id):      
      return self.playgroundDao.get_suggest_keys(id)
  
    def get_recent(self, city_name=None, sport=None, no_records=8):
      return mc_wrap(cache_keys.get_recent_playground_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.playgroundDao.get_recent(city_name, sport, no_records))

    def get_featured(self, city_name=None, sport=None, no_records=6):
      return mc_wrap(cache_keys.get_featured_playground_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.playgroundDao.get_featured(city_name, sport, no_records))

    def get_popular(self, city_name=None, sport=None, no_records=8):
      return mc_wrap(cache_keys.get_popular_playground_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.playgroundDao.get_popular(city_name, sport, no_records))

    def get_active(self, city_name=None, sport=None, no_records=8):
      return mc_wrap(cache_keys.get_active_playground_cache_key(city_name, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.playgroundDao.get_active(city_name, sport, no_records))
    
    def get_recommend(self, locality=None, sport=None, no_records=8):
      return mc_wrap(cache_keys.get_recommend_playground_cache_key(locality, sport), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.playgroundDao.get_recommend(locality, sport, no_records))
      
    def query_by_alias(self, alias):
      return self.playgroundDao.query_by_alias(alias)

    def query_by_owner(self, user, status='all'):
      return self.playgroundDao.query_by_owner(user, status)

    def search(self, status='all', curs=None, **params):
      return self.playgroundDao.search(self, status, curs, **params)

    def persist(self, playground, user_info):
      return self.playgroundDao.persist(playground, user_info)
  
class NdbPlaygroundDao(PlaygroundDao):
  mediaDao = NdbMediaDao()

  def get_record(self, playground_id):
    logger.info('NdbPlaygroundDao:: DBHIT: get_record for %s ' % playground_id)
    return Playground.get_by_id(long(playground_id))  
  
  def get_search_keys(self, id):
      logger.info('NdbPlaygroundDao:: DBHIT: get_search_keys for playground')
      return mc_wrap(cache_keys.get_search_keys_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: None)
      
  def get_suggest_keys(self, id):
      logger.info('NdbPlaygroundDao:: DBHIT: get_suggest_keys for playground')
      return mc_wrap(cache_keys.get_suggest_keys_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: None)
      
  def get_recent(self, city_name=None, sport=None, no_record=8):
      logger.info('NdbPlaygroundDao:: DBHIT: get_recent for %s, %s, %s ' % (city_name, sport, no_record))
      playground_query = Playground.query(Playground.status == 2)
      if city_name is not None:
        playground_query = playground_query.filter(Playground.address.city == city_name.lower())
      if sport is not None:
        playground_query = self.build_query_for_sport(playground_query, sport, True)
      playground_query = playground_query.order(-Playground.created_on)
      return list(playground_query.fetch(no_record))

  def get_featured(self, city_name=None, sport=None, no_record=8):
      logger.info('NdbPlaygroundDao:: DBHIT: get_featured for %s, %s, %s ' % (city_name, sport, no_record))
      playground_query = Playground.query(Playground.status == 2, Playground.featured == True)
      if city_name is not None:
        playground_query = playground_query.filter(Playground.address.city == city_name.lower())
      if sport is not None:
        playground_query = self.build_query_for_sport(playground_query, sport, True)
      playground_query = playground_query.order(-Playground.created_on)
      return list(playground_query.fetch(no_record))

  def get_popular(self, city_name=None, sport=None, no_record=8):
      logger.info('NdbPlaygroundDao:: DBHIT: get_popular for %s, %s, %s ' % (city_name, sport, no_record))
      playground_query = Playground.query(Playground.status == 2)
      if city_name is not None:
        playground_query = playground_query.filter(Playground.address.city == city_name.lower())
      if sport is not None:
        playground_query = self.build_query_for_sport(playground_query, sport, True)
      playground_query = playground_query.order(-Playground.review_stats.ratings_count, -Playground.created_on)
      return list(playground_query.fetch(no_record))

  def get_active(self, city_name=None, sport=None, no_record=8):
      logger.info('NdbPlaygroundDao:: DBHIT: get_active for %s, %s, %s ' % (city_name, sport, no_record))
      playground_query = Playground.query(Playground.status == 2)
      if city_name is not None:
        playground_query = playground_query.filter(Playground.address.city == city_name.lower())
      if sport is not None:
        playground_query = self.build_query_for_sport(playground_query, sport)
      playground_query = playground_query.order(-Playground.created_on)
      if no_record > -1:
        return list(playground_query.fetch(no_record))
      else: #return all. simulating -1 for app engine
        return list(playground_query.fetch())
  
  def get_recommend(self, locality=None, sport=None, no_record=8):
      logger.info('NdbPlaygroundDao:: DBHIT: get_recommend for %s, %s, %s ' % (locality, sport, no_record))
      playground_query = Playground.query(Playground.status == 2)
      if locality is not None and locality != '' and locality != 'None':       
        playground_query = playground_query.filter(ndb.OR(Playground.address.locality == locality.lower() , Playground.address.city == locality.lower()))    
      if sport is not None and sport != '' and sport != 'None':
        playground_query = self.build_query_for_multisport(playground_query, sport)
      playground_query = playground_query.order(-Playground.created_on)      
      if no_record > -1:
        return list(playground_query.fetch(no_record))
      else: #return all. simulating -1 for app engine
        return list(playground_query.fetch())
    
  def query_by_alias(self, alias):
      logger.info('NdbPlaygroundDao:: DBHIT: query_by_alias for %s ' % alias)
      playground_query = Playground.query(Playground.alias == alias)
      playground = playground_query.fetch(1)
      return playground[0] if playground is not None and len(playground) > 0 else None

  def query_by_owner(self, user, status='all'):
    logger.info('NdbPlaygroundDao:: DBHIT: query_by_owner for %s ' % user.email)
    owner_query = Playground.query()
    if not user_has_role(user, 'admin'):
      owner_query = Playground.query(ndb.OR(Playground.owners == user.key, Playground.created_by == user.key, Playground.updated_by == user.key))
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      owner_query = owner_query.filter(status == status_value)
    owner_query = owner_query.order(-Playground.updated_on)
    return owner_query.fetch()
  
  def search(self, status='all', curs=None, **params):
    logger.info('NdbPlaygroundDao:: DBHIT: search %s  ' % params)
    #Using Search API for name searches.
    #TODO: Use search for name, locality, city, sport and geopt
    if ('name' in params): 
      return self.search_index(status, **params)
    else:
      return self.search_datastore(status, curs, **params)
      
  def search_datastore(self, status, curs, **params):
    if status != 'all':
      status_value = STATUS_DICT.get(status)
      logger.debug('status %d ' % (status_value))
      search_query = Playground.query(Playground.status == status_value)
    else:
      search_query = Playground.query()
    for key, value in params.items():
      #Constructing named queries for structured properties the round about way.
      # TO explore a better way later.
      if '.' in key and value is not None:
        struct, attr = key.split('.')
        if struct == 'address':
          search_query = search_query.filter(getattr(Playground.address, attr) == value)
        elif struct == 'contactInfo':
          search_query = search_query.filter(getattr(Playground.contact_info, attr) == value)
      else:
        if key == 'sport' and value is not None:
          search_query = self.build_query_for_sport(search_query, value, True)        
        elif value is not None:
          search_query = search_query.filter(getattr(Playground, key) == value)     
    #search_query = search_query.order(-Playground.updated_on)
    logger.info('NdbPlaygroundDao:: DBHIT: search query  ' + str(search_query))
    #return search_query.fetch()
    
    search_forward = search_query.order(-Playground.updated_on)
    search_reverse = search_query.order(Playground.updated_on)
    
    # Fetch a page going forward.
    logger.info('NdbPlaygroundDao:: DBHIT: Cursor ' + str(curs))
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
        
    # Fetch the same page going backward.
    #if next_curs is not None:
     #   rev_cursor = next_curs.reversed()
      #  prev_data, prev_curs, prev_more = search_reverse.fetch_page(6, start_cursor=rev_cursor)
    #else:
        #curs = Cursor(urlsafe=curs)
        #prev_data, prev_curs, prev_more = search_reverse.fetch_page(6, start_cursor=curs)        

    return (next_data, next_curs, next_more, prev_data, prev_curs, prev_more)
  
  def search_index(self, user_ip, status, **params):
    logger.debug('Search Param Results: ' + str(params))
    #locality = params['address.locality']   #TODO: Hardcoded for testing. To be made generic.    
    
    playgrounds = []
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
      index = search.Index(PLAYGROUND)      
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
      logger.exception("NdbPlaygroundDao:: Search query failed for playgrounds")
      #Retrieve the doc_id from the search results and then use that to query the datastore to fetch the entity
    
    keys = []
    for doc in search_results:
      keys.append(ndb.Key(Playground, long(doc.doc_id)))
    
    cache_id = PLAYGROUND+'_'+str(user_ip)
    get_keys = mc_get(cache_keys.get_search_keys_cache_key(cache_id))    
    if get_keys is not None:
      del_keys = mc_delete(cache_keys.get_search_keys_cache_key(cache_id))
    add_keys = mc_wrap(cache_keys.get_search_keys_cache_key(cache_id), ENTITY_CACHE_EXPIRATION,
                      lambda x: keys)
    logger.info('No of Playground Added to cache : %s' % len(add_keys))    
    return keys
    
  def search_index_suggest(self, user_ip, status, **params):
    logger.debug('Suggest Search Param Results: ' + str(params))
    #locality = params['address.locality']   #TODO: Hardcoded for testing. To be made generic.    
    
    suggest_playgrounds = []
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
      index = search.Index(PLAYGROUND)          
      
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
      logger.exception("NdbPlaygroundDao:: Search query failed for suggest playgrounds")
      #Retrieve the doc_id from the search results and then use that to query the datastore to fetch the entity
    
    keys = []    
    for doc in search_results:
      keys.append(ndb.Key(Playground, long(doc.doc_id)))
    
    #suggest_playgrounds = ndb.get_multi(keys)    
    #return suggest_playgrounds
    cache_id = 'suggest_'+str(PLAYGROUND)+'_'+str(user_ip)
    get_keys = mc_get(cache_keys.get_suggest_keys_cache_key(cache_id))    
    if get_keys is not None:
      del_keys = mc_delete(cache_keys.get_suggest_keys_cache_key(cache_id))
    add_keys = mc_wrap(cache_keys.get_suggest_keys_cache_key(cache_id), ENTITY_CACHE_EXPIRATION,
                      lambda x: keys)
    logger.info('No of Suggest Playground Added to cache : %s' % len(add_keys))
    return keys
    
  #Very hacky implementation to handle NOT IN query, as appengine does not support it.
  #TODO: Find a better way to handle this.
  def build_query_for_sport(self, query, sport, normalize=False):
    sport = normalize_sport_name(sport) if normalize else sport.lower()
    if sport == 'others':
      sport_types = SPORT_DICT.keys()
      query = query.filter(ndb.AND(Playground.sport != sport_types[0], 
                                   Playground.sport != sport_types[1], 
                                   Playground.sport != sport_types[2], 
                                   Playground.sport != sport_types[3], 
                                   Playground.sport != sport_types[4]))
      query = query.order(Playground.sport)
    else:
      query = query.filter(Playground.sport == sport.lower())
    return query
  
  def build_query_for_multisport(self, query, sport):    
    sports = [x.strip() for x in sport.split(',')]
    if len(sports) > 0:
      multisports = []
      for sport in sports:
        multisports.append(Playground.sport == sport)
      query = query.filter(ndb.query.OR(*multisports))
      logger.debug("Sports String : " + str(multisports))      
    return query

  def status_change(self, playground, user_info):
    key = None
    if playground is not None:      
      if playground.key is not None:                
        playground.updated_by = user_info.key
        # change the status from current status
        if user_has_role(user_info, 'admin'):
          if playground.status == 1:
            playground.status += 1 #active status
          elif playground.status == 2:
            playground.status -= 1 #deactive status
        else:
          if playground.status == 0:
            playground.status += 1 #enable status
          else:
            playground.status -= playground.status #disable status
        key = playground.put()
      
      if key is not None:
        #update the search index
        self.update_search_index(key.id(), playground)
        mc_delete(cache_keys.get_playground_cache_key(key.id()))
      return key
  
  def persist(self, playground, user_info):
    key = None
    if playground is not None:
      curr_playground = None
      if playground.key is not None:
        curr_playground = self.get_record(playground.key.id())
      #If entry exists for the same playground, udpate the data
      if curr_playground is not None:
        self.copy_playground_model(curr_playground, playground)
        curr_playground.updated_by = user_info.key
        # change the status to pending approval after every edit, unless the current user is an admin
        if not user_has_role(user_info, 'admin'):
          curr_playground.status = 1 #pending_approval status
          if not user_info.key in curr_playground.owners:
            curr_playground.owners.append(user_info.key)
        key = curr_playground.put()
      else:
        #create a new playground
        playground.status = 0 #pending_creation status
        playground.created_by = user_info.key
        playground.updated_by = user_info.key
        playground.review_stats = ReviewStats()
        playground.review_stats.reviews_count = 0
        playground.review_stats.ratings_count = 0
        if not user_has_role(user_info, 'admin'):
          playground.owners = []
          playground.owners.append(user_info.key)
        key = playground.put()
      
      logger.debug("Playground persisted in datastore, %s " % key)
      if key is not None:
        self.update_search_index(key.id(), playground)
        #TODO: Make sure all the caches that has this entity is deleted here
        mc_delete(cache_keys.get_playground_cache_key(key.id()))
      return key
  
  #does a complete replace of the model data except the alias, business_id as that cannot be changed
  def copy_playground_model(self, to_model, from_model):
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
    
  def update_search_index(self, id, playground):
    playground_doc = search.Document(
      # As search documents cannot be updated and can only be replaced, for every create or update, we will replace the search document completely.
      # Hence using the datastore id for the search id as well. Retrieving the entity also becomes easier this way. 
      doc_id = str(id),
      # Be vey cautious on what fields are indexed, as that impacts the cost and search performance.
      # Store only the fields that are required to be searched upon. For retrievel, we will retrieve the id from search and use that to query the entity from the datastore.
      fields=[
       search.TextField(name='name', value=playground.name),
       search.TextField(name='caption', value=playground.caption),
       search.TextField(name='sport', value=playground.sport),
       search.TextField(name='locality', value=playground.address.locality),
       search.TextField(name='locality_id', value=playground.address.locality_id),
       search.TextField(name='city', value=playground.address.city),
       search.NumberField(name='status', value=playground.status),
       search.DateField(name='updated_on', value=datetime.date(playground.updated_on)),
       search.GeoField(name='latlong', value=search.GeoPoint(playground.address.latlong.lat, playground.address.latlong.lon))
       ])
    
    try:
      index = search.Index(name=PLAYGROUND)
      index.put(playground_doc)
      logger.debug("Successfully stored playground in search index %s " % id)
    except search.Error:
      logger.exception('Storing playground %s in search index failed' % id)
  
  def split_keys(self, arr, size):
     arrs = []
     num = 0
     while len(arr) > size:
         pice = arr[:size]
         
         num += 1
         id = 'page'+str(num)
         logger.info("Search Key Id: %s " % id)
         logger.debug("Search Keys: " + str(pice))
         
         prev_data = self.get_search_page(id)
         logger.debug('mc_prev_data: ' + str(prev_data))
         
         del_data = mc_delete(cache_keys.get_search_page_cache_key(id))
         logger.debug('mc_del_data: ' + str(del_data))
         
         final_data = mc_wrap(cache_keys.get_search_page_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: pice)
         logger.debug('mc_final_data: ' + str(final_data))
         
         arrs.append(pice)
         arr   = arr[size:]
     arrs.append(arr)
     return arrs
 