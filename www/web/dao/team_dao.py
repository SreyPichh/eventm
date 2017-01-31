from models import Team, User

class TeamDao(object):
    
  def get_record(self, id):
    pass
  
  def query_by_owner(self, user):
    pass
  
  def query_by_alias(self, alias, sport):
    pass

  def query_by_team_alias(self, alias, user):
    pass

  def persist(self, Team, User):
    pass

class PlayerDao(object):
    
  def get_record(self, id):
    pass
    
  def query_by_all(self):
    pass

  def query_by_email(self, email):
    pass

  def persist(self, Player):
    pass