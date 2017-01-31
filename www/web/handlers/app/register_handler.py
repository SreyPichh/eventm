# standard library imports
import logging
import webapp2
import constants

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from models import Register
from web.lib.basehandler import BaseHandler
from web.handlers.cms import cms_forms as forms
from web.dao.dao_factory import DaoFactory
from web.lib.decorators import role_required, user_required
from datetime import datetime, date, time

logger = logging.getLogger(__name__)

class ManageRegisterHandler(blobstore_handlers.BlobstoreUploadHandler, BaseHandler):

  eventDao =  DaoFactory.create_rw_eventDao()
  mediaDao = DaoFactory.create_rw_mediaDao()
  teamDao =  DaoFactory.create_rw_teamDao()
  profileDao = DaoFactory.create_rw_profileDao()
  registerDao = DaoFactory.create_rw_registerDao()
  
  @user_required
  def get(self):
    params = {}
    
    return True

  @user_required
  def post(self, record_id=None):
    params = {}
        
    continue_url = self.request.get('continue').encode('ascii', 'ignore')
    
    register = self.form_to_dao(record_id)
    logger.debug('registration populated ' + str(register))       
    key = self.registerDao.persist(register, self.user_info)
    logger.debug('key ' + str(key))

    if key is not None:
      record = self.registerDao.get_record(key.id())
      message = ''
      if record.team_id:
        message += ('%s teams ' %len(record.team_id))
      if record.player_id:
        message += ('%s player ' %len(record.player_id))
      message += ('registered this event succesfully')
      logger.info(message)
      self.add_message(message, 'success')        
      if continue_url:
        return self.redirect(continue_url)
      else:
        return self.redirect_to('profile', **params)
    
    logger.error('registration failed')
    message = ('registration failed.')
    self.add_message(message, 'error')    
    return self.redirect_to('profile', **params)
  
  def form_to_dao(self, record_id=None):
    register = None
    if record_id is not None  and len(record_id) > 1:
      register = self.registerDao.get_record(long(record_id))
    else:
      register = Register()
    event_id = self.request.get('event_id')
    event_data = self.eventDao.get_record(long(event_id))
    register.reg_id = event_data.key
    register.reg_type = self.request.get('participant_type')
    register.user_id = self.user_info.key
    
    sel_team = self.request.get_all('team')
    sel_player = self.request.get_all('player')
    logger.debug('sel_team:  ' + str(sel_team))
    logger.debug('sel_player:  ' + str(sel_player))    
    payment = 0
    if len(sel_team) > 0:        
      teams = []        
      teams_count = len(sel_team)
      logger.debug('Teams Count: ' + str(teams_count))
      for x in xrange(teams_count):
        teams.append(self.teamDao.get_record(sel_team[x]).key)        
      logger.debug('Teams ' + str(teams))
      payment += teams_count * constants.REG_PRICE
      register.team_id = teams
    
    if len(sel_player) > 0:        
      players = []        
      players_count = len(sel_player)
      logger.debug('Players Count: ' + str(players_count))
      for x in xrange(players_count):
        players.append(self.profileDao.get_record(sel_player[x]).key)
      logger.debug('Players ' + str(players))
      payment += players_count * constants.REG_PRICE        
      register.player_id = players
      
    register.payment = payment    
    return register
  
  
  '''def send_register_email(self, record_id):
    params = {}
    emails = []
    upload_count = 0
    
    if record_id:
      register = self.registerDao.get_record(record_id)
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
    return self.redirect_to('invite-friends')'''