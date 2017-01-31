from models import Playground, User

class PlaygroundDao(object):
    
  def get_record(self, id):
    pass
  
  def get_recent(self, city_name=None, sport=None, no_records=8):
    pass
  
  def get_featured(self, city_name=None, sport=None, no_records=8):
    pass
  
  def get_popular(self, city_name=None, sport=None, no_records=8):
    pass
  
  def query_by_alias(self, alias):
    pass
    
  def query_by_owner(self, user, status='all'):
    pass
  
  def search(self, status='all', **params):
    pass
  
  def persist(self, Playground, User):
    pass
        