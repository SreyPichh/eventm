# standard library imports
import logging
import constants
from web.utils.app_utils import get_default_city
from web.lib.basehandler import BaseHandler
from web.dao.dao_factory import DaoFactory

logger = logging.getLogger(__name__)

class CityHomeHandler(BaseHandler):

  mediaDao =  DaoFactory.create_ro_mediaDao()
  eventDao =  DaoFactory.create_ro_eventDao()
  playgroundDao =  DaoFactory.create_ro_playgroundDao()
  trainingcentreDao =  DaoFactory.create_ro_trainingCentreDao()  

  def get(self, city_name=None, sport=None):
    params = {}
    logger.debug('home for city %s, and sport %s ' % (city_name, sport))
    if city_name is None:
      city_name = get_default_city()
    # if sport is not None and sport != 'None' and sport != '':
    #     return self.render_template('/cms/dashboard.html')
    recent_playgrounds = self.playgroundDao.get_recent(city_name, sport)  
    featured_playgrounds = self.playgroundDao.get_featured(city_name, sport)
    popular_playgrounds = self.playgroundDao.get_popular(city_name, sport)
    logger.debug(' recent_playgrounds %s ' % len(recent_playgrounds))
    logger.debug(' featured_playgrounds %s ' % len(featured_playgrounds))
    logger.debug(' popular_playgrounds %s ' % len(popular_playgrounds))
    playgrounds = recent_playgrounds + featured_playgrounds + popular_playgrounds
    playground_media = self.mediaDao.get_primary_media(playgrounds, constants.PLAYGROUND)
    logger.debug(' playground_media %s ' % len(playground_media))
    
    recent_trainingcentres = self.trainingcentreDao.get_recent(city_name, sport)
    featured_trainingcentres = self.trainingcentreDao.get_featured(city_name, sport) 
    popular_trainingcentres = self.trainingcentreDao.get_popular(city_name, sport)
    logger.debug(' recent_trainingcentres %s ' % len(recent_trainingcentres))
    logger.debug(' featured_trainingcentres %s ' % len(featured_trainingcentres))
    logger.debug(' popular_trainingcentres %s ' % len(popular_trainingcentres))
    trainingcentres = recent_trainingcentres + featured_trainingcentres + popular_trainingcentres
    trainingcentre_media = self.mediaDao.get_primary_media(trainingcentres, constants.TRAINING_CENTRE)
    logger.debug(' trainingcentre_media %s ' % len(trainingcentre_media))
    
    recent_events = self.eventDao.get_recent(city_name, sport)
    featured_events = self.eventDao.get_featured(city_name, sport)
    ongoing_events = self.eventDao.get_ongoing(city_name, sport)
    upcoming_events = self.eventDao.get_upcoming(city_name, sport)
    logger.debug(' recent_events %s ' % len(recent_events))
    logger.debug(' featured_events %s ' % len(featured_events))
    logger.debug(' ongoing_events %s ' % len(ongoing_events))
    logger.debug(' upcoming_events %s ' % len(upcoming_events))
    events = recent_events + featured_events + ongoing_events + upcoming_events
    event_media = self.mediaDao.get_primary_media(events, constants.EVENT)
    logger.debug(' event_media %s ' % len(event_media))
    
    params['recent_playgrounds'] = recent_playgrounds
    params['featured_playgrounds'] = featured_playgrounds
    params['popular_playgrounds'] = popular_playgrounds
    params['playground_media'] = playground_media
    
    params['recent_events'] = recent_events
    params['featured_events'] = featured_events
    params['ongoing_events'] = ongoing_events
    params['upcoming_events'] = upcoming_events
    params['event_media'] = event_media
    
    params['recent_trainingcentres'] = recent_trainingcentres
    params['featured_trainingcentres'] = featured_trainingcentres
    params['popular_trainingcentres'] = popular_trainingcentres
    params['trainingcentre_media'] = trainingcentre_media
    
    params['city_name'] = city_name
    params['sport'] = sport
    params['home'] = 'true'
    params['title'] = 'Sports Home'
    
    return self.render_template('/app/homenew.html', **params)