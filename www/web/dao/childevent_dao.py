from models import Event, User

class ChildEventDao(object):
    
  def get_record(self, id):
    pass
  
  def query_by_alias(self, alias):
    pass
    
  def query_by_owner(self, user, status='all'):
    pass
  
  def search(self, value, key='name', status='all'):
    pass
  
  def persist(self, Event, User):
    pass