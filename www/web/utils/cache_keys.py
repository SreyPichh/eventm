# TODO: All list cache keys to contain city name and sport name
def get_business_cache_key(business_id):
  return '%s:get_business' % business_id

def get_playground_cache_key(playground_id):
  return '%s:get_playground' % playground_id
  

def get_recent_playground_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'recent_playgrounds_' + city_name + '_' + sport

def get_popular_playground_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'popular_playgrounds_' + city_name + '_' + sport

def get_featured_playground_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'featured_playgrounds_' + city_name + '_' + sport

def get_active_playground_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'active_playgrounds_' + city_name + '_' + sport

def get_recommend_playground_cache_key(locality = None, sport = None):
  locality = '' if locality is None else locality  
  sport = '' if sport is None else sport
  return 'recommend_playgrounds_' + locality + '_' + sport

def get_trainingcentre_cache_key(trainingcentre_id):
  return '%s:get_trainingcentre' % trainingcentre_id

def get_recent_trainingcentre_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'recent_tc_' + city_name + '_' + sport

def get_popular_trainingcentre_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'popular_tc_' + city_name + '_' + sport

def get_featured_trainingcentre_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'featured_tc_' + city_name + '_' + sport

def get_active_trainingcentre_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'active_tc_' + city_name + '_' + sport

def get_recommend_trainingcentre_cache_key(locality = None, sport = None):
  locality = '' if locality is None else locality  
  sport = '' if sport is None else sport
  return 'recommend_tc_' + locality + '_' + sport
  
def get_event_cache_key(event_id):
  return '%s:get_event' % event_id

def get_childevent_cache_key(childevent_id):
  return '%s:get_childevent' % childevent_id
  
def get_recent_event_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'recent_events_' + city_name + '_' + sport

def get_ongoing_event_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'ongoing_events_' + city_name + '_' + sport

def get_ongoing_future_event_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'ongoing_future_events_' + city_name + '_' + sport
  
def get_upcoming_event_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'upcoming_events_' + city_name + '_' + sport

def get_popular_event_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'popular_events_' + city_name + '_' + sport

def get_featured_event_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'featured_events_' + city_name + '_' + sport

def get_active_event_cache_key(city_name = None, sport = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'active_events_' + city_name + '_' + sport

def get_recommend_event_cache_key(locality = None, sport = None):
  locality = '' if locality is None else locality  
  sport = '' if sport is None else sport
  return 'recommend_events_' + locality + '_' + sport

def get_recent_with_children_event_cache_key(sport = None, city_name = None, locality_name = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'recent_with_children_' + city_name + '_' + sport

def get_future_with_children_event_cache_key(sport = None, city_name = None, locality_name = None):
  city_name = '' if city_name is None else city_name
  sport = '' if sport is None else sport
  return 'future_with_children_' + city_name + '_' + sport

def get_event_children_cache_key(entity_id):
  return '%s:event_children' % entity_id

def get_media_cache_key(media_id):
  return '%s:get_media' % media_id

def get_localities_cache_key(city_name):
  return 'localities_%s' % city_name

def get_match_cache_key(match_id):
  return '%s:match' % match_id

def get_matches_for_event_cache_key(event_id):
  return '%s:event_matches' % event_id
  
def get_team_cache_key(team_id):
  return '%s:team' % team_id
  
def get_player_cache_key(player_id):
  return '%s:player' % player_id
  
def get_all_player_cache_key():
  return 'All:player'

def get_locality_cache_key(locality_id):
  return '%s:locality' % locality_id

def get_user_cache_key(user_id):
  return '%s:get_user' % user_id
  
def get_sports_cache_key(city_name):
  return 'sports_%s' % city_name

def get_search_keys_cache_key(id):
  return '%s:get_search_keys' % id

def get_suggest_keys_cache_key(id):
  return '%s:get_suggest_keys' % id

def get_register_cache_key(register_id):
  return '%s:get_register' % register_id
  
def get_bulkdata_cache_key(bulkdata_id):
  return '%s:get_bulkdata' % bulkdata_id