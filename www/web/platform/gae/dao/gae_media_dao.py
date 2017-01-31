from datetime import datetime
import logging
from google.appengine.ext import ndb
from google.appengine.api import images
import sys
sys.modules['ndb'] = ndb

import constants
from web.utils.memcache_utils import mc_wrap, mc_delete
from web.utils import cache_keys
from web.dao.media_dao import MediaDao
from settings import ENTITY_CACHE_EXPIRATION
from models import Media
from web.utils.app_utils import get_default_media
logger = logging.getLogger(__name__)

class MemMediaDao(MediaDao):

    def __init__(self, _mediaDao):
     self.mediaDao = _mediaDao
        
    def get_record(self, id):
      media = mc_wrap(cache_keys.get_media_cache_key(id), ENTITY_CACHE_EXPIRATION,
                      lambda x: self.mediaDao.get_record(id))
      return media
    
    def get_primary_media(self, entities, type):
      return self.mediaDao.get_primary_media(entities, type)
    
    def get_active_media(self, key, sport, type):
      return self.mediaDao.get_active_media(key, sport, type)

    def get_all_media(self, key, type):
      return self.mediaDao.get_all_media(key, type)

    def persist(self, media, user_info):
      return self.mediaDao.persist(media, user_info)
  
class NdbMediaDao(MediaDao):
    
  def get_record(self, media_id):
    logger.info('NdbMediaDao:: DBHIT: get_record for %s ' % media_id)
    return Media.get_by_id(long(media_id))
  
  # Get the primary media for the list of medias as a map, with media id as the key and media as the value
  def get_primary_media(self, entities, type):
      logger.info('NdbMediaDao:: DBHIT: get_primary_media for %s' % type)
      media_map = dict()
      entity_ids = map(lambda entity: entity.key, entities)
      if entity_ids is not None and len(entity_ids) > 0:
        #Assigning a default pic to all the entities
        #Then they will be replaced with primary media, if they have.
        for entity in entities:
          media_map[entity.key] = get_default_media(type, entity.sport)

        logger.debug('entity ids before dedupe %s ' % len(entity_ids))
        entity_ids = list(set(entity_ids)) #Dedupe entity ids. Not doing this at entities level, as they are not hashable
        logger.debug('entity ids after dedupe %s ' % len(entity_ids))
        media_query = Media.query(Media.entity_id.IN(entity_ids), Media.entity_type == type, Media.primary == True)
        media_list = media_query.fetch()

        for media in media_list:
          media_map[media.entity_id] = media.url
      
      return media_map
      
  def get_active_media(self, key, sport, type):
      logger.info('NdbMediaDao:: DBHIT: get_active_media for %s ' % type )
      media_query = Media.query(Media.entity_id == key, Media.entity_type == type, Media.status == True)
      media = media_query.fetch()
      if media is None or len(media) == 0:
        default_pic_url = get_default_media(type, sport)
        default_pic = Media()
        default_pic.url = default_pic_url
        media.append(default_pic)
      return media

  def get_all_media(self, key, type):
      logger.info('NdbMediaDao:: DBHIT: get_active_media for %s ' % type )
      media_query = Media.query(Media.entity_id == key, Media.entity_type == type)
      return media_query.fetch()
    
  def persist(self, media):
    key = None
    if media is not None:
      key = media.put()
      
    if key is not None:
      mc_delete(cache_keys.get_media_cache_key(key.id()))
    return key
  
