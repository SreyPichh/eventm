# standard library imports
import logging
import json

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
import webapp2

from web.lib import utils
import cms_utils
from web.lib.basehandler import BaseHandler
from web.lib.decorators import role_required
from web.handlers.cms import cms_forms as forms
from models import Business, ContactInfo
from web.dao.dao_factory import DaoFactory

logger = logging.getLogger(__name__)


class ManageBusinessHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):

  businessDao =  DaoFactory.create_rw_businessDao()

  @role_required('business')
  def get(self, business_id=None):
    params = {}
    params['title'] = 'Create New Business'
    
    upload_url = self.uri_for('create-business')
    if business_id is not None  and len(business_id) > 1:
      upload_url = self.uri_for('edit-business', business_id = business_id)
      business = self.businessDao.get_record(business_id)
      params['title'] = 'Update - ' + str(business.name)
      if business.logo:
        params['current_logo'] = images.get_serving_url(business.logo)
      self.form = cms_utils.dao_to_form_contact_info(business, forms.BusinessForm(self, business))

    logger.debug('upload_url' + upload_url)
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    return self.render_template('/cms/create_business.html', **params)

  @role_required('business')
  def post(self, business_id=None):
    params = {}

    if not self.form.validate():
      if business_id is not None  and len(business_id) > 1:
        return self.get(business_id)
      else:
        return self.get()

    business = self.form_to_dao(business_id)
    upload_files = self.get_uploads('logo')  # 'logo' is file upload field in the form
    if upload_files is not None and len(upload_files) > 0:
      blob_info = upload_files[0]
      business.logo = blob_info.key()
      logger.info('Link to logo ' + images.get_serving_url(business.logo))
      
    logger.debug('business populated ' + str(business))
    key = self.businessDao.persist(business, self.user_info)
    logger.debug('key ' + str(key))
    if key is not None:
      logger.info('Business succesfully created/updated')
      message = ('Business succesfully created/updated.')
      self.add_message(message, 'success')
      return self.redirect_to('dashboard', **params)
    else:
      logger.error('business creation failed')
      message = ('Business creation failed.')
      self.add_message(message, 'error')
      self.form = forms.BusinessForm(self, business)
      return self.render_template('/cms/create_business.html', **params)
      
  @webapp2.cached_property
  def form(self):
    return forms.BusinessForm(self)
    
  def form_to_dao(self, business_id):
    business = None
    if business_id is not None  and len(business_id) > 1:
      business = self.businessDao.get_record(long(business_id))
      logger.debug('business ' + str(business))
    else:
      business = Business()
    logger.debug('business 2 ' + str(business))
    business.name = self.form.name.data
    #Create an automatic alias for the business
    business.alias = utils.slugify(self.form.name.data)
    business.description = self.form.description.data
    return cms_utils.form_to_dao_contact_info(self.form, business)