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
from models import Playground, Business, Media, MasterData
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import user_required
from datetime import datetime, date, time

logger = logging.getLogger(__name__)

class ManageBulkDataHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):

  bulkdataDao =  DaoFactory.create_rw_bulkdataDao()
  businessDao = DaoFactory.create_rw_businessDao()
  mediaDao = DaoFactory.create_rw_mediaDao()

  @user_required
  def get(self, masterdata_id=None):
    params = {}
  
    upload_url = self.uri_for('create-bulk-data')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    status = self.request.get('status')
    pg_status = status if status != '' else None
    params['title'] = 'Create Bulk Data'
    params['weekdays'] = constants.DAYS_LIST
    
    if masterdata_id is not None  and len(masterdata_id) > 1:
      masterdata = self.playgroundDao.get_record(masterdata_id)
      params['title'] = 'Update - ' + str(masterdata.name)
      params['continue_url'] = continue_url
      if pg_status is not None:
        logger.info('current status: %s' % pg_status)
        key = self.playgroundDao.status_change(masterdata, self.user_info)
        if key is not None:
          updated_pg = self.playgroundDao.get_record(long(key.id()))
          logger.info('updated status : %s' % updated_pg.status)
          if pg_status == str(updated_pg.status):
            logger.info('masterdata status could not be changed.')
            message = ('masterdata status could not be changed.')
            self.add_message(message, 'error')
          else:
            logger.info('masterdata status succesfully changed.')
            message = ('masterdata status succesfully changed.')
            self.add_message(message, 'success')
          return self.redirect(continue_url)
      else:
        upload_url = self.uri_for('edit-masterdata', masterdata_id = masterdata_id)      
        all_media = self.mediaDao.get_all_media(masterdata.key, constants.PLAYGROUND)
        current_media = []
        for photo in all_media:
          current_media.append({'name': photo.name, 'url':images.get_serving_url(photo.link), 'status': photo.status, 'primary': photo.primary})
        params['current_media'] = current_media
        self.form = cms_utils.dao_to_form_locality_info(masterdata, forms.BulkPlaygroundForm(self, masterdata))
        self.form = cms_utils.dao_to_form_contact_info(masterdata, self.form)        
      
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    return self.render_template('/cms/create_bulk_data.html', **params)

  @user_required
  def post(self, masterdata_id=None):
    params = {}

    if not self.form.validate():
      if masterdata_id is not None  and len(masterdata_id) > 1:
        return self.get(masterdata_id)
      else:
        return self.get()
    
    save = self.request.get('save')
    next = self.request.get('next')
    next_tab = next if next != '' else save
    locality_id = self.request.get('locality_id')
    
    masterdata = self.form_to_dao(masterdata_id)
    
    if locality_id is not None:
      logger.info('Locality Id: %s ' % locality_id)
      locality_count = self.process_locality(masterdata.address.locality, locality_id, constants.PLACES_API_KEY)    
      masterdata.address.locality_id = locality_id
      
    logger.debug('masterdata populated ' + str(masterdata))
    key = self.bulkdataDao.persist(masterdata, self.user_info)
    logger.debug('key ' + str(key))
    
    if key is not None:
      self.upload_photos(key)
      logger.info('masterdata succesfully created/updated')
      message = ('masterdata succesfully created/updated.')
      self.add_message(message, 'success')
      return self.redirect_to('create-bulk-data', **params)
    
    logger.error('masterdata creation failed')
    message = ('masterdata creation failed.')
    self.add_message(message, 'error')
    self.form = forms.MasterDataForm(self, masterdata)
    return self.render_template('/cms/create_bulk_data.html', **params)

  @webapp2.cached_property
  def form(self):
    return forms.MasterDataForm(self)
    
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
    
  def form_to_dao(self, masterdata_id):
    masterdata = None
    if masterdata_id is not None  and len(masterdata_id) > 1:
      masterdata = self.playgroundDao.get_record(long(masterdata_id))
    else:
      masterdata = MasterData()
    masterdata.pg_name = self.form.pg_name.data
    masterdata.sport = self.form.sport.data.lower()
    
    masterdata.public = self.form.public.data
    masterdata.booking_days = self.form.booking_days.data
    masterdata.regular_time = self.form.regular_time.data
    masterdata.ground_type = self.form.ground_type.data.lower()
    masterdata.surface_type = self.form.surface_type.data.lower()
    masterdata.tot_fields = self.form.tot_fields.data
    masterdata.ground_rules = self.form.ground_rules.data.lower()
    
    masterdata.tc_name = self.form.tc_name.data
    masterdata.tc_open_days = self.form.tc_open_days.data.lower()
    masterdata.age_limit = self.form.age_limit.data
    masterdata.tc_participants = self.form.tc_participants.data
    
    masterdata.se_name = self.form.se_name.data
    if self.form.start_datetime.data is not None:
      masterdata.start_datetime = datetime(*(self.form.start_datetime.data.timetuple()[:6]))
    if self.form.end_datetime.data is not None:
      masterdata.end_datetime = datetime(*(self.form.end_datetime.data.timetuple()[:6]))
    
    masterdata = cms_utils.form_to_dao_address(self.form, masterdata)
    masterdata = cms_utils.form_to_dao_contact_pg(self.form, masterdata)
    masterdata = cms_utils.form_to_dao_contact_tc(self.form, masterdata)
    masterdata = cms_utils.form_to_dao_contact_se(self.form, masterdata)
    return masterdata
       
  
  def create_or_update_business(self, playground):
    if playground.business_id is not None:
      business = self.businessDao.get_record(long(playground.business_id.id()))
    else:
      business = Business()
    business.name = playground.name
    business.alias = playground.alias
    business.description = playground.description    
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
