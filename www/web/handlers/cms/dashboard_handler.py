# standard library imports
import logging
'''import constants
from web.lib import utils'''
from web.lib.basehandler import BaseHandler
from web.lib.decorators import user_required
from web.dao.dao_factory import DaoFactory
'''from web.handlers.cms import cms_forms as forms
from settings import DEFAULT_CITY'''

'''import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.ext import ndb
from google.appengine.api import taskqueue'''

logger = logging.getLogger(__name__)


class DashboardHandler(BaseHandler):

  businessDao =  DaoFactory.create_rw_businessDao()  
  eventDao =  DaoFactory.create_rw_eventDao()
  childeventDao =  DaoFactory.create_rw_childeventDao()
  playgroundDao =  DaoFactory.create_rw_playgroundDao()
  trainingcentreDao =  DaoFactory.create_rw_trainingCentreDao()  
  matchDao =  DaoFactory.create_rw_matchDao()
  teamDao =  DaoFactory.create_rw_teamDao()
  playerDao =  DaoFactory.create_rw_playerDao()
  
  @user_required
  def get(self, business_id=None):
    params = {}
    params['title'] = 'Dashboard'
    params['owner_business'] = self.businessDao.query_by_owner(self.user_info)
    params['owner_playgrounds'] = self.playgroundDao.query_by_owner(self.user_info)
    params['owner_events'] = self.eventDao.query_by_owner(self.user_info)
    params['owner_childevents'] = self.childeventDao.query_by_owner(self.user_info)
    params['owner_trainingcentres'] = self.trainingcentreDao.query_by_owner(self.user_info)
    params['owner_matches'] = self.matchDao.query_by_owner(self.user_info)
    params['owner_teams'] = self.teamDao.query_by_owner(self.user_info)
    params['owner_players'] = self.playerDao.query_by_owner(self.user_info)
    return self.render_template('/cms/dashboard.html', **params)

'''class ProfileHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):
  
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
    
    if self.user_info.image:
      params['current_image'] = images.get_serving_url(self.user_info.image)
    upload_url = self.uri_for('edit-user-image')
    params['media_upload_url'] = blobstore.create_upload_url(upload_url)
    params['want_list'] = constants.WANT_DICT
    params['owner_info'] = self.user_info
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

  @user_required
  def post(self, user_id=None):
    params = {}
    
    if not self.form.validate():
      if user_id is not None  and len(user_id) > 1:
        return self.get(user_id)
      else:
        return self.get()
    
    user = self.form_to_dao(user_id)
    upload_files = self.get_uploads('image')
    if upload_files is not None and len(upload_files) > 0:
      blob_info = upload_files[0]
      user.image = blob_info.key()
      logger.info('Link to image ' + images.get_serving_url(user.image))
      
    logger.debug('User populated ' + str(user))
    if user.email == self.user_info.email:
      key = self.profileDao.persist(user, self.user_info)
      logger.debug('key ' + str(key))

      if key is not None:
        redirect_url = self.uri_for('profile')
        logger.info('User Profile succesfully created/updated')
        message = ('User Profile succesfully created/updated.')
        self.add_message(message, 'success')
        return self.redirect(redirect_url)
  
    logger.error('User Profile updation failed')
    message = ('User Profile updation failed.')
    self.add_message(message, 'error')
    self.form = forms.UserProfileForm(self, user)
    return self.render_template('/cms/edit_profile.html', **params)
  
  @webapp2.cached_property
  def form(self):
    return forms.UserProfileForm(self)

  def form_to_dao(self, user_id):
    user = None
    if user_id is not None  and len(user_id) > 1:
      user = self.user_model.get_by_id(long(user_id))
    else:
      user = User()
    user.name = self.form.name.data
    #user.last_name = self.form.last_name.data
    user.email = self.form.email.data
    user.phone = self.form.phone.data
    user.locality = self.form.locality.data
    user.locality_id = self.form.locality_id.data
    user.i_want = self.form.i_want.data
    #user.sport = self.form.sport.data.lower()
    #for multi sport support
    sel_sport = self.request.get_all('sports_list')
    logger.debug('sel_team:  ' + str(sel_sport))
    if len(sel_sport) > 0:
      user.sport = ', '.join(sel_sport)
    else:
      user.sport = ''    
    return user
'''
'''class InviteFriendsHandler(BaseHandler):

  @user_required
  def get(self):
    params = {}
    
    if self.user:
      upload_url = self.uri_for('invite-friends')      
      user_info = self.user_model.get_by_id(long(self.user_id))          
      params['media_upload_url'] = upload_url
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
'''