from models import Register, User

class RegisterDao(object):
    
  def get_record(self, id):
    pass  
  
  def query_by_user(self, user):
    pass
  
  def query_by_reg_user_id(self, reg_id, user, status):
    pass

  def persist(self, Register, User):
    pass