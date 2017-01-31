# standard library imports
import logging
import time

import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import ndb

from web.lib import utils
import cms_utils
from web.utils.app_utils import get_latlong_from_address
from web.lib.basehandler import BaseHandler
from web.handlers.cms import cms_forms as forms
from models import Playground, TrainingCentre, Address, Business, ContactInfo, CustomInfo, Event, Media
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import role_required
from web.lib.decorators import user_required
#import xlrd
import csv
import os
#from csv import excel_tab
from datetime import datetime

import urllib
import constants

logger = logging.getLogger(__name__)

class ImportHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
  eventDao =  DaoFactory.create_rw_eventDao()
  businessDao = DaoFactory.create_rw_businessDao()
  playgroundDao  = DaoFactory.create_rw_playgroundDao()
  trainingCentreDao = DaoFactory.create_rw_trainingCentreDao()  
  
  @user_required
  def get(self):
    params = {}
  
    upload_url = self.uri_for('import')
    params['title'] = 'Import'
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    return self.render_template('/cms/import.html', **params)

  @user_required
  def post(self):
    if not self.form.validate():
      return self.get()
    
    start_record = int(str(self.request.get('linenum')))
    upload_files = self.get_uploads('importfile')  # 'file' is file upload field in the form
    blob_info = upload_files[0]
    upload_count = self.process_csv(blob_info, start_record)
    self.add_message(str(upload_count) + ' entities created successfully.', 'success')    
    return self.redirect_to('import')
    
  def process_csv(self, blob_info, start_record):
    update = {}  
    upload_count = 0
    row_count = 0
      
    blob_reader = blobstore.BlobReader(blob_info.key())
    datareader = csv.reader(blob_reader)
    
    for row in datareader:
      row_count += 1
      if row_count >= (start_record + 1): #to skip the header row
        logger.info('Starting to parse %s, %s' % (row_count, row[1]))
        entity_type = row[0].lower()
        update['name'] = utils.stringify(row[1])
        # Name is mandatory for all entities
        if update['name'] == '':
          logger.error('Name is empty. Skipping this record')
          continue
        
        update['locality'] = utils.stringify(row[5]).lower()
        update['city'] = utils.stringify(row[8]).lower()

        #Locality and city mandatory for playground and trainingcentre
        if entity_type != 'event':
          if update['locality'] == '' or update['city'] == '':
            logger.error('Locality or city is empty. Skipping this record')
            continue
        alias_name = utils.slugify(update['name'].lower())

        try:
          update['description'] = utils.stringify(row[2])
          update['sport'] = utils.stringify(row[3]).lower()
          update['person_name'] = utils.stringify(row[10])
          update['phone'] = utils.stringify(row[11])
          update['email'] = utils.stringify(row[12])
          update['website'] = utils.stringify(row[13])
          update['facebook'] = utils.stringify(row[18])
          update['twitter'] = utils.stringify(row[19])
          update['youtube'] = utils.stringify(row[20])
          update['gplus'] = utils.stringify(row[21])
          update['line1'] = utils.stringify(row[6])
          update['line2'] = utils.stringify(row[7])
          update['pin'] = int(row[9].strip()) if row[9] != '' else None 
          #update['start_datetime'] = row[22]
          #update['end_datetime'] = row[23]
          
          logger.debug('Constructed Structure for upload ' + str(update))
          logger.info('Entity type to be created, ' + entity_type)
          
          if entity_type == 'ground':        
            import_data = self.form_to_dao_ground(alias_name, **update)
          elif entity_type == 'club':
            import_data = self.form_to_dao_center(alias_name, **update)
          elif entity_type == 'event':
            import_data = self.form_to_dao_event(alias_name, **update)
          
          # for add locality table
          if import_data.address.locality != '':
            place_name = import_data.address.locality
            logger.info('Place: %s' % place_name)
        
            newfeed_url = 'https://maps.googleapis.com/maps/api/place/autocomplete/xml?types=(regions)&input='+urllib.quote(place_name)+'&key='+constants.PLACES_API_KEY
            logging.info('newfeed url %s' % newfeed_url)
            
            newroot = self.parse(newfeed_url)
            auto_status = newroot.getElementsByTagName('status')[0].firstChild.data
            logger.info('Auto Status: %s ' % auto_status)
            
            if auto_status == 'OK':
              items = newroot.getElementsByTagName('prediction')[0]
              place_id = items.getElementsByTagName('place_id')[0].firstChild.data
              place_name = items.getElementsByTagName('value')[0].firstChild.data #description
              logger.info('Place Name: %s Place Id: %s ' %(place_name, place_id))
              import_data.address.locality_id = place_id
              logger.info('Locality Id: %s ' % import_data.address.locality_id)
              locality_add = self.process_locality(place_name, place_id, constants.PLACES_API_KEY)
              #if import_data.address.latlong == '':
                #locality = self.importDao.query_by_place_id(place_id)
                #import_data.address.latlong = locality.latlong
                #logger.info('Geo Location New: %s ' % import_data.address.latlong)
            else:
              logger.error('Error: %s' % auto_status)

          logger.debug('Populated File Data ' + str(import_data))
          business_key = self.create_or_update_business(alias_name, import_data)
          import_data.business_id = business_key
                
          if entity_type == 'ground':
            ground = self.playgroundDao.query_by_alias(alias_name)
            if ground is not None:
              self.playgroundDao.copy_playground_model(ground, import_data)
              key = self.playgroundDao.persist(ground, self.user_info)
              upload_count += 1
              logger.info('Playground updated for %s with key %s' % (alias_name, key))      
            else:
              key = self.playgroundDao.persist(import_data, self.user_info)
              upload_count += 1
              logger.info('New playground created for %s' % (update['name']))          
          elif entity_type == 'club':
            tc = self.trainingCentreDao.query_by_alias(alias_name)
            if tc is not None:
              self.trainingCentreDao.copy_trainingCentre_model(tc, import_data)
              key = self.trainingCentreDao.persist(tc, self.user_info)
              upload_count += 1
              logger.info('TrainingCentre updated for %s with key %s' % (alias_name, key))      
            else:
              key = self.trainingCentreDao.persist(import_data, self.user_info)
              upload_count += 1
              logger.info('New training centre created for %s' % (update['name']))
          elif entity_type == 'event':
            event = self.eventDao.query_by_alias(alias_name)
            if event is not None:
              self.eventDao.copy_event_model(event, import_data)
              key = self.eventDao.persist(event, self.user_info)
              upload_count += 1
              logger.info('Event updated for %s with key %s' % (alias_name, key))      
            else:
              key = self.eventDao.persist(import_data, self.user_info)
              upload_count += 1
              logger.info('Event created for %s' % (update['name']))
        
          if key is not None:
            logger.info(str(entity_type) + ' succesfully created/updated')
          else:
            logger.error('Already Exist of %s:%s' % (entity_type, update['name']))
  
        except StandardError as e:
          #skipping to next record
          logger.error('Error occured, %s, for %s' % (str(e), alias_name))
      else:
        logger.info("skipping record number, %s " % row_count)
    return upload_count
    

  @webapp2.cached_property
  def form(self):
    return forms.ImportForm(self)
    
  def upload_photos(self, photos):
    upload_files = self.get_uploads()  
    if upload_files is not None and len(upload_files) > 0:
      files_count = len(upload_files)
      logger.info('no of files uploaded ' + str(files_count))
      for x in xrange(files_count):
        blob_info = upload_files[x]
        media_obj = Media()
        media_obj.name = self.form.media.__getitem__(x).data['name']
        media_obj.status = self.form.media.__getitem__(x).data['status']
        media_obj.link = blob_info.key()
        photos.append(media_obj)
        logger.info('Link to picture file ' + media_obj.name + ', ' + images.get_serving_url(media_obj.link))
    return photos
  
  def create_or_update_business(self, alias_name, import_data):
    business = self.businessDao.query_by_alias(alias_name)      
    
    if business is not None:
      business_key = business.key
      import_data.business_id = business_key
      logger.info('Business Already Exist with Key %s' % str(business_key))
    else:
      try:
        business = Business()
        business.name = import_data.name
        business.description = import_data.description
        business.alias = import_data.alias
        business.contact_info = import_data.contact_info
        business_key = self.businessDao.persist(business, self.user_info)
        import_data.business_id = business_key
        logger.info('New Business Created for %s with key %s' % (alias_name, str(business_key)))      
      except StandardError as e:
        #Skip the error and continue
        logger.error('Error occured, %s, for %s' % (str(e), alias_name))
        raise
    return business_key
  
  def form_to_dao_ground(self, alias_name, **update):
    try:
      playground = Playground()
      playground.name = update['name']
      #Create an automatic alias for the playground
      playground.alias = alias_name
      playground.description = update['description']
      playground.sport = update['sport']
      playground = self.form_to_dao_address_import(playground, **update)
      playground = self.form_to_dao_contact_info_import(playground, **update)
      #if playground.photos is None:
        #playground.photos = []
      #self.upload_photos(playground.photos)
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return playground
       
  def form_to_dao_center(self, alias_name, **update):
    try:
      trainingcentre = TrainingCentre()
      trainingcentre.name = update['name']
      #Create an automatic alias for the trainingcentre
      trainingcentre.alias = alias_name
      trainingcentre.description = update['description']
      trainingcentre.sport = update['sport']
      trainingcentre = self.form_to_dao_address_import(trainingcentre, **update)
      trainingcentre = self.form_to_dao_contact_info_import(trainingcentre, **update)
      #if trainingcentre.photos is None:
        #trainingcentre.photos = []
      #self.upload_photos(trainingcentre.photos)
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return trainingcentre
  
  def form_to_dao_event(self, alias_name, **update):
    try: 
      event = Event()
      event.name = update['name']
      #Create an automatic alias for the event
      event.alias = alias_name
      event.description = update['description']
      event.sport = update['sport']
      #event.start_datetime = update['start_datetime']
      #event.end_datetime = update['end_datetime']
      event = self.form_to_dao_contact_info_import(event, **update)
      #if event.photos is None:
        #event.photos = []
      #self.upload_photos(event.photos)
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return event
  
  def form_to_dao_business(self, **update):
    business = Business()    
    business.name = update['name']
    #Create an automatic alias for the business
    business.alias = utils.slugify(update['name'])
    business.description = update['description']
    business = self.form_to_dao_contact_info_import(business, **update)
    return business  

  def form_to_dao_address_import(self, entity, **update):
    #entity = playground
    try:
      if update['locality'] == '' or update['city'] == '':
        raise StandardError('Locality is empty. Cannot create entity')
      
      entity.address = Address()
      entity.address.line1 = update['line1'].lower()
      entity.address.line2 = update['line2'].lower()
      entity.address.locality = update['locality'].lower()
      entity.address.city = update['city'].lower()
      entity.address.pin = update['pin']
      lattitude, longitude = get_latlong_from_address(entity.address)
      if lattitude is not None and longitude is not None:
        entity.address.latlong = ndb.GeoPt(lattitude, longitude)
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise 
    return entity

  def form_to_dao_contact_info_import(self, entity, **update):
    try:
      entity.contact_info = ContactInfo()
      if len(update['person_name']) > 0:
        entity.contact_info.person_name = [x.strip() for x in update['person_name'].split(',')]
      if len(update['email']) > 0:
        entity.contact_info.email = [x.strip() for x in update['email'].split(',')]
      if len(update['phone']) > 0:
        entity.contact_info.phone = [x.strip() for x in update['phone'].split(',')]
      entity.contact_info.website = update['website']
      entity.contact_info.facebook = update['facebook']
      entity.contact_info.twitter = update['twitter']
      entity.contact_info.youtube = update['youtube']
      entity.contact_info.gplus = update['gplus']
    except StandardError as e:
      logger.error('Error occured, %s, for %s:%s' % (str(e), type, update['name']))
      raise
    return entity