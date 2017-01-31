# standard library imports
import logging
import webapp2
import constants
from models import User, Media
from web.lib import utils
from web.lib.basehandler import BaseHandler
from web.lib.decorators import user_required
from web.dao.dao_factory import DaoFactory
from web.handlers.cms import cms_forms as forms

from google.appengine.api import images
from google.appengine.api import taskqueue
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from datetime import datetime, date, time

logger = logging.getLogger(__name__)

class ProfileHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
  eventDao =  DaoFactory.create_rw_eventDao() 
  playgroundDao =  DaoFactory.create_rw_playgroundDao()   
  trainingcentreDao =  DaoFactory.create_rw_trainingCentreDao() 
  mediaDao =  DaoFactory.create_ro_mediaDao()
  profileDao =  DaoFactory.create_rw_profileDao()
  teamDao =  DaoFactory.create_rw_teamDao()
  
  @user_required
  def get(self, user_id=None):
    params = {}
    
    if user_id is not None  and len(user_id) > 1:
      user_info = self.user_model.get_by_id(long(user_id))
      upload_url = self.uri_for('edit-profile', user_id=user_id)            
      logger.debug('upload_url : ' + upload_url)
      if user_info.image:
        params['current_image'] = images.get_serving_url(user_info.image)
      if user_info.sport:
        params['sel_sport'] = [x.strip() for x in user_info.sport.split(',')]
      params['sports_list'] = constants.SPORTS_LIST
      params['media_upload_url'] = blobstore.create_upload_url(upload_url)      
      
      self.form = forms.UserProfileForm(self, user_info)
      return self.render_template('/cms/edit_profile.html', **params)
    
    '''logger.debug('User Id: ' + str(self.user_id))
    logger.debug('User Info: ' + str(self.user_info))
    logger.debug('User Type: ' + str(self.user_type))'''
    if self.user_info.image:
      params['current_image'] = images.get_serving_url(self.user_info.image)
    elif self.user_type[0] == 'facebook':
      params['current_image'] = 'https://graph.facebook.com/'+str(self.user_type[1])+'/picture?type=large'
    upload_url = self.uri_for('edit-user-image')
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    upload_gallery_url = self.uri_for('upload-profile-gallery')
    params['upload_gallery_url'] = blobstore.create_upload_url(upload_gallery_url)
    params['title'] = self.user_info.name
    params['want_list'] = constants.WANT_DICT
    params['owner_info'] = self.user_info
    params['profile_gallery'] = self.mediaDao.get_all_media(self.user_info.key, constants.PROFILE)    
    params['owner_playgrounds'] = self.playgroundDao.query_by_owner(self.user_info)
    params['owner_events'] = self.eventDao.query_by_owner(self.user_info)    
    params['owner_trainingcentres'] = self.trainingcentreDao.query_by_owner(self.user_info)
    params['owner_teams'] = self.teamDao.query_by_owner(self.user_info, 'all', 4)
    
    recommend_events = self.eventDao.get_recommend(self.user_info.locality, self.user_info.sport, 4)
    params['recommend_events'] = recommend_events
    recommend_playgrounds = self.playgroundDao.get_recommend(self.user_info.locality, self.user_info.sport, 4)
    params['recommend_playgrounds'] = recommend_playgrounds    
    recommend_trainingcentres = self.trainingcentreDao.get_recommend(self.user_info.locality, self.user_info.sport, 4)
    params['recommend_trainingcentres'] = recommend_trainingcentres
        
    event_media = self.mediaDao.get_primary_media(recommend_events, constants.EVENT)
    params['event_media'] = event_media
    playground_media = self.mediaDao.get_primary_media(recommend_playgrounds, constants.PLAYGROUND)
    params['playground_media'] = playground_media
    trainingcentre_media = self.mediaDao.get_primary_media(recommend_trainingcentres, constants.TRAINING_CENTRE)
    params['trainingcentre_media'] = trainingcentre_media
    logger.debug(' event_media %s ' % len(event_media))
    logger.debug(' playground_media %s ' % len(playground_media))
    logger.debug(' trainingcentre_media %s ' % len(trainingcentre_media))
    
    return self.render_template('/cms/profile.html', **params)
  
class EditUserNameHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))    
    user.name = utils.stringify(self.request.get("value"))
    logger.info('Id: %s Value: %s' % (id, user.name))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserDOBHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    dob_str = self.request.get("value")
    user = User.get_by_id(long(id))
    #user.dob = datetime(*(self.request.get("value")))
    user.dob = datetime.strptime(dob_str, "%Y-%m-%d")
    #user.dob = datetime(*(self.request.get("value").timetuple()[:6]))
    logger.info('Id: %s Value: %s' % (id, user.dob))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserGenderHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))
    user.gender = self.request.get("value")
    logger.info('Id: %s Value: %s' % (id, user.gender))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserProfessionHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))
    user.profession = self.request.get("value")
    logger.info('Id: %s Value: %s' % (id, user.profession))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserPhoneHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))
    user.phone = utils.stringify(self.request.get("value"))
    logger.info('Id: %s Value: %s' % (id, user.phone))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserStatusHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))
    user.i_want = self.request.get("value")
    logger.info('Id: %s Value: %s' % (id, user.i_want))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserLocalityHandler(webapp2.RequestHandler):
  importDao =  DaoFactory.create_rw_importDao()
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))
    user.locality = utils.stringify(self.request.get("value"))
    locality_exist = self.importDao.query_by_place_name(user.locality.title())
    if locality_exist:
      user.locality_id = locality_exist.place_id
    logger.info('Id: %s Value: %s' % (id, user.locality))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserCityHandler(webapp2.RequestHandler):
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))
    user.city = utils.stringify(self.request.get("value"))
    logger.info('Id: %s Value: %s' % (id, user.city))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class EditUserImageHandler(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):
  
  def post(self):    
    upload_files = self.get_uploads('file')
    id = self.request.get("user_id")    
    user = User.get_by_id(long(id))
    redirect_url = self.uri_for('profile')    
    if upload_files is not None and len(upload_files) > 0:
      blob_info = upload_files[0]
      user.image = blob_info.key()
      user.image_url = images.get_serving_url(blob_info.key())
      user.put()
      logger.info('Link to image ' + images.get_serving_url(user.image))
    
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return self.redirect(redirect_url)

class UploadProfileGalleryHandler(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):
  
  mediaDao =  DaoFactory.create_ro_mediaDao()
  
  def post(self):
    upload_files = self.get_uploads('gallery_images')
    id = self.request.get("user_id")
    user = User.get_by_id(long(id))
    redirect_url = self.uri_for('profile')
    logger.info('Uploaded files: ' + str(upload_files))
    #logger.info('Get Request: ' + str(self.request.get()))
    if upload_files is not None and len(upload_files) > 0:
      files_count = len(upload_files)
      logger.info('no of files uploaded ' + str(files_count))
      for x in xrange(files_count):
        blob_info = upload_files[x]
        media_obj = Media()
        #media_obj.name = self.form.media.__getitem__(x).data['name']
        media_obj.type = constants.PHOTO
        media_obj.status = True
        #media_obj.primary = self.form.media.__getitem__(x).data['primary']
        media_obj.link = blob_info.key()
        media_obj.url = images.get_serving_url(blob_info.key())
        media_obj.entity_id = user.key
        media_obj.entity_type = constants.PROFILE
        logger.info('Upload file detail: ' + str(media_obj))
        #self.mediaDao.persist(media_obj)
        media_obj.put()
        logger.info('Link to picture file ' + images.get_serving_url(media_obj.link))
    return self.redirect(redirect_url)
        
class EditUserSportHandler(webapp2.RequestHandler):  
  
  def post(self):
    logging.info(self.request.body)
    id = self.request.get("pk")
    user = User.get_by_id(long(id))
    sel_sport = self.request.get_all("value[]")    
    if len(sel_sport) > 0:
      if 'None' in sel_sport:
        sel_sport.remove('None')
      user.sport = ', '.join(sel_sport)
    else:
      user.sport = ''
    #user.sport = sel_sport
    logger.info('Id: %s Value: %s' % (id, user.sport))
    user.put()
    logger.debug('User Data: ' + str(user))
    #return json.dumps(result) #or, as it is an empty json, you can simply use return "{}"
    return

class InviteFriendsHandler(BaseHandler):

  @user_required
  def get(self):
    params = {}
    
    if self.user:
      upload_url = self.uri_for('invite-friends')      
      user_info = self.user_model.get_by_id(long(self.user_id))          
      params['media_upload_url'] = upload_url
      params['title'] = 'Invite friends'      
    return self.render_template('/cms/invite_friends.html', **params)
  
  @user_required
  def post(self):
    params = {}
    emails = []
    upload_count = 0
    
    if not self.form.validate():
      return self.get()
  
    email_list = [x.strip() for x in self.form.email_list.data.split(',')]
    logger.debug('email List: ' + str(email_list))
    
    for email in email_list:
      logger.debug('email: ' + str(email))
      if email == '':
        logger.error('Skipped Empty Email')
        continue
      if utils.is_email_valid(email):
        try:
          # send email
          user = self.user_model.get_by_id(long(self.user_id))
          subject = ("%s Invite Email" % self.app.config.get('app_name'))
          user_token = self.user_model.create_auth_token(self.user_id)
          confirmation_url = self.uri_for("login", _full=True)

          # load email's template
          template_val = {
            "app_name": self.app.config.get('app_name'),
            "first_name": user.name,            
            "confirmation_url": confirmation_url,
            "support_url": self.uri_for("contact", _full=True)
          }

          email_body_path = "emails/email_invites.txt"
          email_body = self.jinja2.render_template(email_body_path, **template_val)
          print email_body
        
          email_url = self.uri_for('taskqueue-send-email')
        
          taskqueue.add(url=email_url, params={
            'to': email,
            'subject': subject,
            'body': email_body,
          })
          upload_count += 1          
          logger.info("Your email invite will be sent successfully to %s" % email)          

        except StandardError as e:          
          logger.error("Error occured, %s, for Email %s!" % (str(e),email))
          
      else:
        logger.error('Skipped Invalid Email Id %s' % email)        
    
    logger.info(str(upload_count) + ' Email invites sent successfully.')
    self.add_message(str(upload_count) + ' Email invites sent successfully.', 'success') 
    return self.redirect_to('invite-friends')

  @webapp2.cached_property
  def form(self):
    return forms.InviteForm(self)
