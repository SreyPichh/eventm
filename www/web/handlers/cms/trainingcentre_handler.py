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
from models import TrainingCentre, Media, Business
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import role_required, user_required

logger = logging.getLogger(__name__)

class ManageTrainingCentreHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):

  businessDao =  DaoFactory.create_rw_businessDao()
  trainingCentreDao = DaoFactory.create_rw_trainingCentreDao()
  mediaDao = DaoFactory.create_rw_mediaDao()
  
  #@role_required('business')
  @user_required
  def get(self, business_id=None, trainingcentre_id=None):
    params = {}

    upload_url = self.uri_for('select-for-trainingcentre')
    continue_url = self.request.get('continue').encode('ascii', 'ignore')    
    status = self.request.get('status')
    tc_status = status if status != '' else None
    params['title'] = 'Create New Training Centre'
    
    if business_id is not None  and len(business_id) > 1:      
      self.form.business_id = business_id
      params['continue_url'] = continue_url
      if trainingcentre_id is not None  and len(trainingcentre_id) > 1:
        trainingcentre = self.trainingCentreDao.get_record(trainingcentre_id)
        params['title'] = 'Update - ' + str(trainingcentre.name)
        if tc_status is not None:
          logger.info('current status: %s' % tc_status)
          key = self.trainingCentreDao.status_change(trainingcentre, self.user_info)
          if key is not None:
            updated_tc = self.trainingCentreDao.get_record(long(key.id()))
            logger.info('updated status : %s' % updated_tc.status)
            if tc_status == str(updated_tc.status):
              logger.info('trainingcentre status could not be changed.')
              message = ('trainingcentre status could not be changed.')
              self.add_message(message, 'error')
            else:
              logger.info('trainingcentre status succesfully changed.')
              message = ('trainingcentre status succesfully changed.')
              self.add_message(message, 'success')
            return self.redirect(continue_url)
        else:
          upload_url = self.uri_for('edit-trainingcentre', business_id = business_id, trainingcentre_id = trainingcentre_id)        
          all_media = self.mediaDao.get_all_media(trainingcentre.key, constants.TRAINING_CENTRE)
          current_media = []
          for photo in all_media:
            current_media.append({'name': photo.name, 'url':images.get_serving_url(photo.link), 'status': photo.status, 'primary': photo.primary})
          params['current_media'] = current_media
          self.form = cms_utils.dao_to_form_locality_info(trainingcentre, forms.TrainingCentreForm(self, trainingcentre))
          self.form = cms_utils.dao_to_form_contact_info(trainingcentre, self.form)          
        
        params['media_upload_url'] = blobstore.create_upload_url(upload_url)
        return self.render_template('/cms/create_trainingcenter.html', **params)
      else:
        upload_url = self.uri_for('create-trainingcentre', business_id = business_id)
        params['media_upload_url'] = blobstore.create_upload_url(upload_url)
        return self.render_template('/cms/create_trainingcenter.html', **params)
        
    params['continue_url'] = upload_url
    params['entity_name'] = 'Training Centre'
    params['owner_business'] = self.businessDao.query_by_owner(self.user_info)
    return self.render_template('/cms/select_business.html', **params)

  #@role_required('business')
  @user_required
  def post(self, business_id=None, trainingcentre_id=None):
    params = {}

    if not self.form.validate():
      if business_id is not None and len(business_id) > 0:
        if trainingcentre_id is not None and len(trainingcentre_id) > 0:
          return self.get(business_id, trainingcentre_id)
        else:
          return self.get(business_id)
      else:
        return self.get()    
    
    save = self.request.get('save')
    next = self.request.get('next')
    next_tab = next if next != '' else save
    locality_id = self.request.get('locality_id')
    
    trainingcentre = self.form_to_dao(trainingcentre_id)
    
    if locality_id is not None:
      logger.info('Locality Id: %s ' % locality_id)
      locality_count = self.process_locality(trainingcentre.address.locality, locality_id, constants.PLACES_API_KEY)    
      trainingcentre.address.locality_id = locality_id
      
    logger.debug('trainingcentre populated ' + str(trainingcentre))
    if business_id != None and business_id != 'user':
      business = self.businessDao.get_record(business_id)
      business_key = business.key
    else:
      business = self.create_or_update_business(trainingcentre)
      business_key = self.businessDao.persist(business, self.user_info)
        
    if business_key is not None:
      logger.info('Business succesfully created for trainingcentre, ' + business.name)
      trainingcentre.business_id = business_key
      key = self.trainingCentreDao.persist(trainingcentre, self.user_info)
      logger.debug('key ' + str(key))

      if key is not None:
        self.upload_photos(key)
        logger.info('trainingcentre succesfully created/updated')
        message = ('trainingcentre succesfully created/updated.')
        self.add_message(message, 'success')
        if next_tab is not None:
          if next_tab != 'save':
            redirect_url = self.uri_for('edit-trainingcentre', business_id = trainingcentre.business_id.id(), trainingcentre_id = key.id())
            redirect_url = redirect_url + next_tab
            logger.info('Redirect Url %s' % redirect_url)
            return self.redirect(redirect_url)
          else:
            redirect_url = self.uri_for('tc-details', city_name = trainingcentre.address.city, locality_name = trainingcentre.address.locality, entity_id = key.id(), entity_alias = trainingcentre.alias)
            return self.redirect(redirect_url)
            #return self.redirect_to('dashboard', **params)
    
    logger.error('trainingcentre creation failed')
    message = ('trainingcentre creation failed.')
    self.add_message(message, 'error')
    self.form = forms.TrainingCentreForm(self, trainingcentre)
    return self.render_template('/cms/create_trainingcentre.html', **params)

          
  @webapp2.cached_property
  def form(self):
    return forms.TrainingCentreForm(self)

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
        media_obj.entity_type = constants.TRAINING_CENTRE
        self.mediaDao.persist(media_obj)
        logger.info('Link to picture file ' + media_obj.name + ', ' + images.get_serving_url(media_obj.link))
    
  def form_to_dao(self, trainingcentre_id):
    trainingcentre = None
    if trainingcentre_id is not None  and len(trainingcentre_id) > 1:
      trainingcentre = self.trainingCentreDao.get_record(long(trainingcentre_id))
    else:
      trainingcentre = TrainingCentre()
    trainingcentre.name = self.form.name.data
    trainingcentre.sport = self.form.sport.data
    #Create an automatic alias for the trainingcentre
    trainingcentre.alias = utils.slugify(self.form.name.data)
    trainingcentre.description = self.form.description.data
    trainingcentre.featured = self.form.featured.data
    self.form.address.locality.data = self.form.locality.data   #for locality from basic info to address
    self.form.address.city.data = self.form.city.data   #for city from basic info to address
    trainingcentre = cms_utils.form_to_dao_address(self.form, trainingcentre)
    trainingcentre = cms_utils.form_to_dao_contact_info(self.form, trainingcentre)
    return trainingcentre
  
  def create_or_update_business(self, trainingcentre):
    if trainingcentre.business_id is not None:
      business = self.businessDao.get_record(long(trainingcentre.business_id.id()))
    else:
      business = Business()
    business.name = trainingcentre.name
    business.description = trainingcentre.description
    business.alias = trainingcentre.alias
    business.contact_info = trainingcentre.contact_info
    return business

class UploadTrainingCentreCoverHandler(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):
  
  def post(self):
    upload_files = self.get_uploads("cover_image")
    id = self.request.get("tc_id")
    tc = TrainingCentre.get_by_id(long(id))    
    redirect_url = self.request.get("continue").encode('ascii', 'ignore')    
    if upload_files is not None and len(upload_files) > 0:
      blob_info = upload_files[0]
      tc.cover = blob_info.key()
      tc.put()
      mc_delete(cache_keys.get_trainingcentre_cache_key(long(id)))
      logger.info('Cover image link: ' + images.get_serving_url(tc.cover))
      
    return self.redirect(redirect_url)

class EnquireTrainingCentreHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  trainingCentreDao = DaoFactory.create_rw_trainingCentreDao()
  
  @user_required
  def post(self):
    params = {}
    
    enq_id = self.request.get("enq_id")
    enq_date = self.request.get("enq_date")
    enq_time = self.request.get("enq_time")
    
    data = self.trainingCentreDao.get_record(long(enq_id))
    enq_datetime = enq_date+' '+enq_time
    redirect_url = self.request.get("continue").encode('ascii', 'ignore')   
    
    sent_email = self.send_enquiry_email(constants.TRAINING_CENTRE, data, enq_datetime)
    
    if sent_email > 0:
      logger.info('Enquiry sent successfully to training centre owner.')
      self.add_message('Enquiry sent successfully to training centre owner.', 'success')
    else:
      logger.info('Error occured on Enquiry.')
      self.add_message('Error occured on Enquiry.', 'warning')
    return self.redirect(redirect_url)
