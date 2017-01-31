# standard library imports
import logging
import json

import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import ndb

import constants
from web.lib import utils
import cms_utils
from web.lib.basehandler import BaseHandler
from web.handlers.cms import cms_forms as forms
from models import Event, Business, ContactInfo, CustomInfo, Media
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import role_required, user_required
from web.utils.cache_keys import get_business_cache_key
from datetime import datetime, date, time

logger = logging.getLogger(__name__)

class ManageEventHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):

  businessDao = DaoFactory.create_rw_businessDao()
  eventDao =  DaoFactory.create_rw_eventDao()
  mediaDao = DaoFactory.create_rw_mediaDao()
  
  #@role_required('business')
  @user_required
  def get(self, business_id=None, event_id=None):
    params = {}
  
    upload_url = self.uri_for('select-for-event')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    params['continue_url'] = continue_url if continue_url != '' else upload_url
    status = self.request.get('status')
    event_status = status if status != '' else None
    params['title'] = 'Create New Event'
    
    if business_id is not None  and len(business_id) > 1:      
      self.form.business_id = business_id
      if event_id is not None  and len(event_id) > 1:        
        event = self.eventDao.get_record(event_id)
        params['title'] = 'Update - ' + str(event.name)
        if event_status is not None:
          logger.info('current status: %s' % event_status)
          key = self.eventDao.status_change(event, self.user_info)
          if key is not None:
            updated_event = self.eventDao.get_record(long(key.id()))
            logger.info('updated status : %s' % updated_event.status)
            if event_status == str(updated_event.status):
              logger.info('event status could not be changed.')
              message = ('event status could not be changed.')
              self.add_message(message, 'error')
            else:
              logger.info('event status succesfully changed.')
              message = ('event status succesfully changed.')
              self.add_message(message, 'success')
            return self.redirect(continue_url)
        else:
          upload_url = self.uri_for('edit-event', business_id = business_id, event_id = event_id)
          all_media = self.mediaDao.get_all_media(event.key, constants.EVENT)
          current_media = []
          for photo in all_media:
            current_media.append({'name': photo.name, 'url':images.get_serving_url(photo.link), 'status': photo.status, 'primary': photo.primary})
          params['current_media'] = current_media
          logger.debug('event detail ' + str(event))
          self.form = cms_utils.dao_to_form_city_info(event, forms.EventForm(self, event))
          self.form = cms_utils.dao_to_form_contact_info(event, self.form)
        
          params['media_upload_url'] = blobstore.create_upload_url(upload_url)
          return self.render_template('/cms/create_event.html', **params)
      else:
        upload_url = self.uri_for('create-event', business_id = business_id)
        params['media_upload_url'] = blobstore.create_upload_url(upload_url)
        return self.render_template('/cms/create_event.html', **params)        
    
    params['entity_name'] = 'Event'
    params['owner_business'] = self.businessDao.query_by_owner(self.user_info)    
    logger.info('Result Params : ' + str(params['entity_name']))
    return self.render_template('/cms/select_business.html', **params)

  #@role_required('business')
  @user_required
  def post(self, business_id=None, event_id=None):
    params = {}

    if not self.form.validate():
      if business_id is not None and len(business_id) > 0:
        if event_id is not None and len(event_id) > 0:
          return self.get(business_id, event_id)
        else:
          return self.get(business_id)
      else:
        return self.get()
    
    save = self.request.get('save')
    next = self.request.get('next')
    next_tab = next if next != '' else save
    locality_id = self.request.get('locality_id')
    
    event = self.form_to_dao(event_id)
    
    if locality_id is not None and len(locality_id) > 0:
      logger.info('Locality Id: %s ' % locality_id)
      locality_count = self.process_locality(event.address.locality, locality_id, constants.PLACES_API_KEY)    
      event.address.locality_id = locality_id      
    else:
      event.address.locality = ''
      event.address.locality_id = ''
      
    logger.debug('event populated ' + str(event))
    if business_id != None and business_id != 'user':
      business = self.businessDao.get_record(business_id)
      business_key = business.key
    else:
      business = self.create_or_update_business(event)
      business_key = self.businessDao.persist(business, self.user_info)
    
    if business_key is not None:
      logger.info('Business succesfully created for event, ' + business.name)
      event.business_id = business_key
      key = self.eventDao.persist(event, self.user_info)
      logger.debug('key ' + str(key))

      if key is not None:
        self.upload_photos(key)
        logger.info('event succesfully created/updated')
        message = ('event succesfully created/updated.')
        self.add_message(message, 'success')
        if next_tab is not None:
          if next_tab != 'save':
            redirect_url = self.uri_for('edit-event', business_id = event.business_id.id(), event_id = key.id())
            redirect_url = redirect_url + next_tab
            logger.info('Url %s' % redirect_url)
            return self.redirect(redirect_url)
          else:
            redirect_url = self.uri_for('event-details', city_name = event.address.city, entity_id = key.id(), entity_alias = event.alias)
            return self.redirect(redirect_url)
            #return self.redirect_to('dashboard', **params)
    
    logger.error('event creation failed')
    message = ('event creation failed.')
    self.add_message(message, 'error')
    self.form = forms.EventForm(self, event)
    return self.render_template('/cms/create_event.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.EventForm(self)
    
  def upload_photos(self, key):
    upload_files = self.get_uploads()  
    if upload_files is not None and len(upload_files) > 0:
      files_count = len(upload_files)
      logger.info('no of files uploaded ' + str(files_count))
      for x in xrange(files_count):
        blob_info = upload_files[x]
        media_obj = Media()
        media_obj.name = self.form.media.__getitem__(x).data['name']
        media_obj.type = constants.PHOTO
        media_obj.status = self.form.media.__getitem__(x).data['status']
        media_obj.primary = self.form.media.__getitem__(x).data['primary']
        media_obj.link = blob_info.key()
        media_obj.url = images.get_serving_url(blob_info.key())
        media_obj.entity_id = key
        media_obj.entity_type = constants.EVENT
        self.mediaDao.persist(media_obj)
        logger.info('Link to picture file ' + media_obj.name + ', ' + images.get_serving_url(media_obj.link))
    
  def form_to_dao(self, event_id):
    event = None
    if event_id is not None  and len(event_id) > 1:
      event = self.eventDao.get_record(long(event_id))
    else:
      event = Event()
    event.name = self.form.name.data
    event.sport = self.form.sport.data
    #Create an automatic alias for the event
    event.alias = utils.slugify(self.form.name.data)
    event.caption = self.form.caption.data
    event.description = self.form.description.data
    event.featured = self.form.featured.data    
    event.start_datetime = datetime(*(self.form.start_datetime.data.timetuple()[:6]))
    event.end_datetime = datetime(*(self.form.end_datetime.data.timetuple()[:6]))
    self.form.address.city.data = self.form.city.data   #for city from basic info to address
    event = cms_utils.form_to_dao_address(self.form, event)
    event = cms_utils.form_to_dao_contact_info(self.form, event)
    return event
  
  def create_or_update_business(self, event):
    if event.business_id is not None:
      business = self.businessDao.get_record(long(event.business_id.id()))
    else:
      business = Business()
    business.name = event.name
    business.description = event.description
    business.alias = event.alias
    business.contact_info = event.contact_info
    return business
