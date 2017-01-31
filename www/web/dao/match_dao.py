from models import Match, User

class MatchDao(object):
    
  def get_record(self, id):
    pass
  
  def query_by_owner(self, user, status='all'):
    pass

  def get_matches_for_event(self, event_key, no_records=-1):
    pass
  
  def persist(self, Match, User):
    pass