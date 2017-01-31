from models import TrainingCentre, User

class TrainingCentreDao(object):
    
  def get_record(self, id):
    pass
  
  def get_recent(self, city_name=None, sport=None, no_records=14):
    pass
  
  def get_featured(self, city_name=None, sport=None, no_records=14):
    pass
  
  def get_popular(self, city_name=None, sport=None, no_records=14):
    pass
  
  def query_by_alias(self, alias):
    pass
    
  def query_by_owner(self, user, status='all'):
    pass
  
  def search(self, value, key='name', status='all'):
    pass
  
  def persist(self, TrainingCentre, User):
    pass
        