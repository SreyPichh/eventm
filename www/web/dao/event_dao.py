from models import Event, User

class EventDao(object):
    
  def get_record(self, id):
    pass
  
  def get_recent(self, city_name=None, sport=None, locality=None, no_records=4):
    pass
  
  def get_ongoing(self, city_name=None, sport=None, locality=None, no_records=4):
    pass
  
  def get_upcoming(self, city_name=None, sport=None, locality=None, no_records=8):
    pass
  
  def get_featured(self, city_name=None, sport=None, no_records=4):
    pass
  
  def get_popular(self, city_name=None, sport=None, no_records=4):
    pass
  
  def get_child_events(self, entity_key, sort_order='asc', no_records=-1):
    pass
  
  def query_by_alias(self, alias):
    pass
    
  def query_by_owner(self, user, status='all'):
    pass
  
  def search(self, value, key='name', status='all'):
    pass
  
  def persist(self, Event, User):
    pass