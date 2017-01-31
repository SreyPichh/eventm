# standard library imports
import logging
import json

import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import ndb

import constants
import cms_utils
from web.lib import utils
from web.utils import cache_keys
from web.utils.memcache_utils import mc_delete
from web.lib.basehandler import BaseHandler
from web.handlers.cms import cms_forms as forms
from models import Playground, Business, Media
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import user_required

logger = logging.getLogger(__name__)

class ManagePlaygroundHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):

  playgroundDao =  DaoFactory.create_rw_playgroundDao()
  businessDao = DaoFactory.create_rw_businessDao()
  mediaDao = DaoFactory.create_rw_mediaDao()

  @user_required
  def get(self, playground_id=None):
    params = {}
  
    upload_url = self.uri_for('create-playground')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    status = self.request.get('status')
    pg_status = status if status != '' else None
    params['title'] = 'Create New Playground'
    
    if playground_id is not None  and len(playground_id) > 1:
      playground = self.playgroundDao.get_record(playground_id)
      params['title'] = 'Update - ' + str(playground.name)
      params['continue_url'] = continue_url
      if pg_status is not None:
        logger.info('current status: %s' % pg_status)
        key = self.playgroundDao.status_change(playground, self.user_info)
        if key is not None:
          updated_pg = self.playgroundDao.get_record(long(key.id()))
          logger.info('updated status : %s' % updated_pg.status)
          if pg_status == str(updated_pg.status):
            logger.info('playground status could not be changed.')
            message = ('playground status could not be changed.')
            self.add_message(message, 'error')
          else:
            logger.info('playground status succesfully changed.')
            message = ('playground status succesfully changed.')
            self.add_message(message, 'success')
          return self.redirect(continue_url)
      else:
        upload_url = self.uri_for('edit-playground', playground_id = playground_id)      
        all_media = self.mediaDao.get_all_media(playground.key, constants.PLAYGROUND)
        current_media = []
        for photo in all_media:
          current_media.append({'name': photo.name, 'url':images.get_serving_url(photo.link), 'status': photo.status, 'primary': photo.primary})
        params['current_media'] = current_media
        self.form = cms_utils.dao_to_form_locality_info(playground, forms.PlaygroundForm(self, playground))
        self.form = cms_utils.dao_to_form_contact_info(playground, self.form)        
      
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    return self.render_template('/cms/create_playground.html', **params)

  @user_required
  def post(self, playground_id=None):
    params = {}

    if not self.form.validate():
      if playground_id is not None  and len(playground_id) > 1:
        return self.get(playground_id)
      else:
        return self.get()
    
    save = self.request.get('save')
    next = self.request.get('next')
    next_tab = next if next != '' else save
    locality_id = self.request.get('locality_id')
    
    playground = self.form_to_dao(playground_id)
    
    if locality_id is not None:
      logger.info('Locality Id: %s ' % locality_id)
      locality_count = self.process_locality(playground.address.locality, locality_id, constants.PLACES_API_KEY)    
      playground.address.locality_id = locality_id
      
    logger.debug('playground populated ' + str(playground))
    business = self.create_or_update_business(playground)
    business_key = self.businessDao.persist(business, self.user_info)

    if business_key is not None:
      logger.info('Business succesfully created for playground, ' + business.name)
      playground.business_id = business_key
      key = self.playgroundDao.persist(playground, self.user_info)
      logger.debug('key ' + str(key))

      if key is not None:
        self.upload_photos(key)
        logger.info('playground succesfully created/updated')
        message = ('playground succesfully created/updated.')
        self.add_message(message, 'success')
        if next_tab is not None:
          if next_tab != 'save':
            redirect_url = self.uri_for('edit-playground', playground_id = key.id())
            redirect_url = redirect_url + next_tab
            logger.info('Redirect Url %s' % redirect_url)
            return self.redirect(redirect_url)
          else:
            redirect_url = self.uri_for('pg-details', city_name = playground.address.city, locality_name = playground.address.locality, entity_id = key.id(), entity_alias = playground.alias)
            return self.redirect(redirect_url)
            #return self.redirect_to('dashboard', **params)
    
    logger.error('playground creation failed')
    message = ('playground creation failed.')
    self.add_message(message, 'error')
    self.form = forms.PlaygroundForm(self, playground)
    return self.render_template('/cms/create_playground.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.PlaygroundForm(self)
    
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
        media_obj.entity_type = constants.PLAYGROUND
        self.mediaDao.persist(media_obj)
        logger.info('Link to picture file ' + media_obj.name + ', ' + images.get_serving_url(media_obj.link))
    
  def form_to_dao(self, playground_id):
    playground = None
    if playground_id is not None  and len(playground_id) > 1:
      playground = self.playgroundDao.get_record(long(playground_id))
    else:
      playground = Playground()
    playground.name = self.form.name.data
    playground.sport = self.form.sport.data.lower()
    #Create an automatic alias for the playground
    playground.alias = utils.slugify(self.form.name.data)
    playground.description = self.form.description.data
    playground.featured = self.form.featured.data
    self.form.address.locality.data = self.form.locality.data   #for locality from basic info to address
    self.form.address.city.data = self.form.city.data   #for city from basic info to address
    playground = cms_utils.form_to_dao_address(self.form, playground)
    playground = cms_utils.form_to_dao_contact_info(self.form, playground)
    return playground
       
  
  def create_or_update_business(self, playground):
    if playground.business_id is not None:
      business = self.businessDao.get_record(long(playground.business_id.id()))
    else:
      business = Business()
    business.name = playground.name
    business.description = playground.description
    business.alias = playground.alias
    business.contact_info = playground.contact_info
    return business

class UploadPlaygroundCoverHandler(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):
  
  def post(self):
    upload_files = self.get_uploads("cover_image")
    id = self.request.get("pg_id")
    pg = Playground.get_by_id(long(id))    
    redirect_url = self.request.get("continue").encode('ascii', 'ignore')    
    if upload_files is not None and len(upload_files) > 0:
      blob_info = upload_files[0]
      pg.cover = blob_info.key()
      pg.put()
      mc_delete(cache_keys.get_playground_cache_key(long(id)))
      logger.info('Cover image link: ' + images.get_serving_url(pg.cover))
      
    return self.redirect(redirect_url)

class EnquirePlaygroundHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  playgroundDao =  DaoFactory.create_rw_playgroundDao()
  
  @user_required
  def post(self):
    params = {}
    
    enq_id = self.request.get("enq_id")
    enq_date = self.request.get("enq_date")
    enq_time = self.request.get("enq_time")
    
    data = self.playgroundDao.get_record(long(enq_id))
    enq_datetime = enq_date+' '+enq_time
    redirect_url = self.request.get("continue").encode('ascii', 'ignore')   
    
    sent_email = self.send_enquiry_email(constants.PLAYGROUND, data, enq_datetime)
    
    if sent_email > 0:
      logger.info('Enquiry sent successfully to playground owner.')
      self.add_message('Enquiry sent successfully to playground owner.', 'success')
    else:
      logger.info('Error occured on Enquiry.')
      self.add_message('Error occured on Enquiry.', 'warning')
    return self.redirect(redirect_url)
