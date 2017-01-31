from web.platform.gae.dao.gae_business_dao import MemBusinessDao, NdbBusinessDao
from web.platform.gae.dao.gae_playground_dao import MemPlaygroundDao, NdbPlaygroundDao
from web.platform.gae.dao.gae_trainingcentre_dao import MemTrainingCentreDao, NdbTrainingCentreDao
from web.platform.gae.dao.gae_event_dao import MemEventDao, NdbEventDao
from web.platform.gae.dao.gae_childevent_dao import MemChildEventDao, NdbChildEventDao
from web.platform.gae.dao.gae_media_dao import MemMediaDao, NdbMediaDao
from web.platform.gae.dao.gae_match_dao import MemMatchDao, NdbMatchDao
from web.platform.gae.dao.gae_team_dao import MemTeamDao, NdbTeamDao, MemPlayerDao, NdbPlayerDao
from web.platform.gae.dao.gae_import_dao import MemImportDao, NdbImportDao
from web.platform.gae.dao.gae_profile_dao import MemProfileDao, NdbProfileDao
from web.platform.gae.dao.gae_register_dao import MemRegisterDao, NdbRegisterDao
from web.platform.gae.dao.gae_bulkdata_dao import MemBulkDataDao, NdbBulkDataDao

class DaoFactory(object):
    @staticmethod
    def create_rw_businessDao():
        return NdbBusinessDao()
    
    @staticmethod
    def create_ro_businessDao():
        return MemBusinessDao(DaoFactory.create_rw_businessDao())
    
    @staticmethod
    def create_rw_playgroundDao():
        return NdbPlaygroundDao()
    
    @staticmethod
    def create_ro_playgroundDao():
        return MemPlaygroundDao(DaoFactory.create_rw_playgroundDao())

    @staticmethod
    def create_rw_trainingCentreDao():
        return NdbTrainingCentreDao()
    
    @staticmethod
    def create_ro_trainingCentreDao():
        return MemTrainingCentreDao(DaoFactory.create_rw_trainingCentreDao())
    
    @staticmethod
    def create_rw_eventDao():
        return NdbEventDao()
    
    @staticmethod
    def create_ro_eventDao():
        return MemEventDao(DaoFactory.create_rw_eventDao())
    
    @staticmethod
    def create_rw_childeventDao():
        return NdbChildEventDao()
    
    @staticmethod
    def create_ro_childeventDao():
        return MemChildEventDao(DaoFactory.create_rw_childeventDao())
      
    @staticmethod
    def create_rw_mediaDao():
        return NdbMediaDao()
    
    @staticmethod
    def create_ro_mediaDao():
        return MemMediaDao(DaoFactory.create_rw_mediaDao())
      
    @staticmethod
    def create_rw_matchDao():
      return NdbMatchDao()
    
    @staticmethod
    def create_ro_matchDao():
      return MemMatchDao(DaoFactory.create_rw_matchDao())
  
    @staticmethod
    def create_rw_teamDao():
      return NdbTeamDao()
    
    @staticmethod
    def create_ro_teamDao():
      return MemTeamDao(DaoFactory.create_rw_teamDao())
  
    @staticmethod
    def create_rw_playerDao():
      return NdbPlayerDao()
    
    @staticmethod
    def create_ro_playerDao():
      return MemPlayerDao(DaoFactory.create_rw_playerDao())
    
    @staticmethod
    def create_rw_importDao():
      return NdbImportDao()
    
    @staticmethod
    def create_ro_importDao():
      return MemImportDao(DaoFactory.create_rw_importDao())
    
    @staticmethod
    def create_rw_profileDao():
      return NdbProfileDao()
    
    @staticmethod
    def create_ro_profileDao():
      return MemProfileDao(DaoFactory.create_rw_profileDao())
    
    @staticmethod
    def create_rw_registerDao():
      return NdbRegisterDao()
    
    @staticmethod
    def create_ro_registerDao():
      return MemRegisterDao(DaoFactory.create_rw_registerDao())
  
    @staticmethod
    def create_rw_bulkdataDao():
      return NdbBulkDataDao()
    
    @staticmethod
    def create_ro_bulkdataDao():
      return MemBulkDataDao(DaoFactory.create_rw_bulkdataDao())
