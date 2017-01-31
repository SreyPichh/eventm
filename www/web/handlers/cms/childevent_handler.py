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
from web.lib.decorators import role_required
#from web.utils.cache_keys import get_business_cache_key

logger = logging.getLogger(__name__)

class ManageChildEventHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):

  childeventDao =  DaoFactory.create_rw_childeventDao()
  eventDao = DaoFactory.create_rw_eventDao()
  mediaDao = DaoFactory.create_rw_mediaDao()

  @role_required('business')
  def get(self, event_id=None, childevent_id=None):
    params = {}
  
    upload_url = self.uri_for('select-for-childevent')
    if event_id is not None  and len(event_id) > 1:      
      self.form.parent_event_id = event_id
      if childevent_id is not None  and len(childevent_id) > 1:
        upload_url = self.uri_for('edit-child-event', event_id = event_id, childevent_id = childevent_id)
        childevent = self.childeventDao.get_record(childevent_id)
        all_media = self.mediaDao.get_all_media(childevent.key, constants.EVENT)
        current_media = []
        for photo in all_media:
          current_media.append({'name': photo.name, 'url':images.get_serving_url(photo.link), 'status': photo.status, 'primary': photo.primary})
        params['current_media'] = current_media
        self.form = cms_utils.dao_to_form_contact_info(childevent, forms.ChildEventForm(self, childevent))        
        
        params['media_upload_url'] = blobstore.create_upload_url(upload_url)
        return self.render_template('/cms/create_childevent.html', **params)
      else:
        upload_url = self.uri_for('create-child-event', event_id = event_id)
        params['media_upload_url'] = blobstore.create_upload_url(upload_url)
        return self.render_template('/cms/create_childevent.html', **params)
        
    params['continue_url'] = upload_url
    params['entity_name'] = 'Child Event'
    params['owner_event'] = self.eventDao.query_by_owner(self.user_info)
    return self.render_template('/cms/select_event.html', **params)

  @role_required('business')
  def post(self, event_id=None, childevent_id=None):
    params = {}

    if not self.form.validate():
      if event_id is not None and len(event_id) > 0:
        if childevent_id is not None and len(childevent_id) > 0:
          return self.get(event_id, childevent_id)
        else:
          return self.get(event_id)
      else:
        return self.get()

    childevent = self.form_to_dao(childevent_id)
    logger.debug('childevent populated ' + str(childevent))
    event = self.eventDao.get_record(event_id)
    event_key = event.key

    if event_key is not None:
      logger.info('Event succesfully created for childevent')
      childevent.parent_event_id = event_key
      key = self.childeventDao.persist(childevent, self.user_info)
      logger.debug('key ' + str(key))

      if key is not None:
        self.upload_photos(key)
        logger.info('childevent succesfully created/updated')
        message = ('childevent succesfully created/updated.')
        self.add_message(message, 'success')
        return self.redirect_to('dashboard', **params)
    
    logger.error('childevent creation failed')
    message = ('childevent creation failed.')
    self.add_message(message, 'error')
    self.form = forms.ChildEventForm(self, childevent)
    return self.render_template('/cms/create_childevent.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.ChildEventForm(self)
    
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
        media_obj.event_id = key
        self.mediaDao.persist(media_obj)
        logger.info('Link to picture file ' + media_obj.name + ', ' + images.get_serving_url(media_obj.link))
    
  def form_to_dao(self, childevent_id):
    childevent = None
    if childevent_id is not None  and len(childevent_id) > 1:
      childevent = self.childeventDao.get_record(long(childevent_id))
    else:
      childevent = Event()
    childevent.name = self.form.name.data
    #Create an automatic alias for the childevent
    childevent.alias = utils.slugify(self.form.name.data)
    childevent.description = self.form.description.data
    childevent.start_datetime = self.form.start_datetime.data
    childevent.end_datetime = self.form.end_datetime.data
    childevent = cms_utils.form_to_dao_contact_info(self.form, childevent)
    return childevent
    
    