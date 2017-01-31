# *-* coding: UTF-8 *-*

# standard library imports
import logging
import re
import pytz
import os
# related third party imports
import webapp2
from webapp2_extras import jinja2
from webapp2_extras import auth
from webapp2_extras import sessions

from google.appengine.ext import blobstore
# local application/library specific imports
import constants
import settings
import models
from web.lib import utils, i18n, jinja_bootstrap
from web.utils.app_utils import get_default_city
from web.platform.gae.dao.dao_utils import  get_localities

from models import Locality
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from web.dao.dao_factory import DaoFactory
from xml.dom import minidom
from google.appengine.api import taskqueue

logger = logging.getLogger(__name__)

class ViewClass:
    """
        ViewClass to insert variables into the template.

        ViewClass is used in BaseHandler to promote variables automatically that can be used
        in jinja2 templates.
        Use case in a BaseHandler Class:
            self.view.var1 = "hello"
            self.view.array = [1, 2, 3]
            self.view.dict = dict(a="abc", b="bcd")
        Can be accessed in the template by just using the variables liek {{var1}} or {{dict.b}}
    """
    pass


class BaseHandler(webapp2.RequestHandler):
    importDao =  DaoFactory.create_rw_importDao()
    profileDao =  DaoFactory.create_rw_profileDao()
    
    """
        BaseHandler for all requests

        Holds the auth and session properties so they
        are reachable for all requests
    """

    def __init__(self, request, response):
        """ Override the initialiser in order to set the language.
        """
        self.initialize(request, response)
        self.locale = i18n.set_locale(self, request)
        self.view = ViewClass()

    def dispatch(self):
        """
            Get a session store for this request.
        """
        self.session_store = sessions.get_store(request=self.request)

        try:
            # csrf protection
            if self.request.method == "POST" and not self.request.path.startswith('/taskqueue'):
                token = self.session.get('_csrf_token')
                if not token or token != self.request.get('_csrf_token'):
                    self.abort(403)

            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def user_model(self):
        """Returns the implementation of the user model.

        Keep consistency when config['webapp2_extras.auth']['user_model'] is set.
        """
        return self.auth.store.user_model

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

    @webapp2.cached_property
    def messages(self):
        return self.session.get_flashes(key='_messages')

    def add_message(self, message, level=None):
        self.session.add_flash(message, level, key='_messages')

    @webapp2.cached_property
    def auth_config(self):
        """
              Dict to hold urls for login/logout
        """
        return {
            'login_url': self.uri_for('login'),
            'logout_url': self.uri_for('logout')
        }

    @webapp2.cached_property
    def user(self):
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user_id(self):
        return str(self.user['user_id']) if self.user else None

    @webapp2.cached_property
    def user_info(self):
        if self.user:
            return self.user_model.get_by_id(long(self.user_id))
        return None
    
    @webapp2.cached_property
    def user_type(self):
        if self.user:
            user_info = self.user_model.get_by_id(long(self.user_id))
            return user_info.auth_ids[0].split(':')
        return None
    
    @webapp2.cached_property
    def user_key(self):
        if self.user:
            user_info = self.user_model.get_by_id(long(self.user_id))
            return user_info.key
        return None

    @webapp2.cached_property
    def email(self):
        if self.user:
            try:
                user_info = self.user_model.get_by_id(long(self.user_id))
                return user_info.email
            except AttributeError, e:
                # avoid AttributeError when the session was delete from the server
                logging.error(e)
                self.auth.unset_session()
                self.redirect_to('home')
        return None
      
    @webapp2.cached_property
    def is_business_user(self):
      if self.user_info:
        return utils.user_has_role(self.user_info, 'business')
      return False
    
    @webapp2.cached_property
    def is_admin_user(self):
      if self.user_info:
        return utils.user_has_role(self.user_info, 'admin')
      return False
  
    @webapp2.cached_property
    def provider_uris(self):
        login_urls = {}
        continue_url = self.request.get('continue_url')
        for provider in self.provider_info:
            if continue_url:
                login_url = self.uri_for("social-login", provider_name=provider, continue_url=continue_url)
            else:
                login_url = self.uri_for("social-login", provider_name=provider)
            login_urls[provider] = login_url
        return login_urls

    @webapp2.cached_property
    def provider_info(self):
        return models.SocialUser.PROVIDERS_INFO

    @webapp2.cached_property
    def current_user(self):
        user = self.auth.get_user_by_session()
        if user:
            return self.user_model.get_by_id(user['user_id'])
        return None

    @webapp2.cached_property
    def is_mobile(self):
        return utils.set_device_cookie_and_return_bool(self)

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(factory=jinja_bootstrap.jinja2_factory, app=self.app)

    @webapp2.cached_property
    def get_base_layout(self):
        """
        Get the current base layout template for jinja2 templating. Uses the variable base_layout set in config
        or if there is a base_layout defined, use the base_layout.
        """
        return self.base_layout if hasattr(self, 'base_layout') else self.app.config.get('base_layout')
    
    def set_base_layout(self, layout):
        """
        Set the base_layout variable, thereby overwriting the default layout template name in config.py.
        """
        self.base_layout = layout

    def render_template(self, filename, **kwargs):
        # make all self.view variables available in jinja2 templates
        if hasattr(self, 'view'):
            kwargs.update(self.view.__dict__)

        if 'city_name' not in kwargs:
          kwargs['city_name'] = get_default_city()
        if 'sport' not in kwargs:
          kwargs['sport'] = None
        # set or overwrite special vars for jinja templates
        kwargs.update({
            'alltypes': constants.TYPE_DICT.items(),
            'sports': constants.SPORT_DICT.items(),
            'sports_list': constants.SPORTS_LIST.items(),
            'days_list': constants.DAYS_LIST.items(),
            'num_list': constants.NUM_LIST.items(),
            'category_dict': constants.CATEGORY_DICT.items(),
            'want_dict': constants.WANT_DICT.items(),
            'status': settings.STATUS_DICT.items(),
            'google_analytics_code': self.app.config.get('google_analytics_code'),
            'app_name': self.app.config.get('app_name'),
            'user_id': self.user_id,
            'user_info': self.user_info,
            'user_type': self.user_type,
            'fb_app_id': self.app.config.get('fb_api_key'),
            'is_business_user': self.is_business_user,
            'is_admin_user': self.is_admin_user,
            'email': self.email,
            'url': self.request.url,
            'path': self.request.path,
            'query_string': self.request.query_string,
            'is_mobile': self.is_mobile,
            'base_layout': self.get_base_layout,
            'localities': get_localities(kwargs['city_name'])
        })
        kwargs.update(self.auth_config)
        if hasattr(self, 'form'):
          kwargs['form'] = self.form
        if self.messages:
          if 'messages' in kwargs:
            kwargs['messages'].append(self.messages)
          else:
            kwargs['messages'] = self.messages
        logger.debug('sport value now .... %s ' % kwargs['sport'])
        self.response.headers.add_header('X-UA-Compatible', 'IE=Edge,chrome=1')
        self.response.write(self.jinja2.render_template(filename, **kwargs))
        
    def process_locality(self, place_name, place_id, api_key):
      locality_count = 0
      locality_exist = self.importDao.query_by_place_id(place_id)
      if locality_exist is None:
        detail_url = 'https://maps.googleapis.com/maps/api/place/details/xml?placeid='+place_id+'&key='+api_key
        logging.info('detail_url %s' % detail_url)
    
        detail = self.parse(detail_url)
        for entry in detail.getElementsByTagName('PlaceDetailsResponse'):
          status = entry.getElementsByTagName('status')[0].firstChild.data
          logger.info('Detail Status: %s ' % status)
          if status == 'OK':
            try:
              datas = {}                
              datas["lat"] = entry.getElementsByTagName('lat')[0].firstChild.data
              datas["long"] = entry.getElementsByTagName('lng')[0].firstChild.data              
              datas["name"] = entry.getElementsByTagName('name')[0].firstChild.data
              datas["ref_id"] = entry.getElementsByTagName('id')[0].firstChild.data
              datas["place_id"] = entry.getElementsByTagName('place_id')[0].firstChild.data
              datas["address"] = entry.getElementsByTagName('formatted_address')[0].firstChild.data
              logger.debug('Data Result Final: ' + str(datas))
      
              locality = self.form_to_dao_locality(**datas)
              logger.debug('populated file data: ' + str(locality))
              key = self.importDao.persist(locality, self.user_info)
              locality_count += 1
              logger.info('New Locality Created for %s with key %s' % (locality.name, key))                  
            except IndexError, ValueError:
              pass
          else:
            logger.error('Error: %s' % status)
      else:
        logger.error('Already Exist Locality %s with Id: %s' %(place_name, place_id))
      return locality_count    
    
    def form_to_dao_locality(self, **datas):
      try:
        locality = Locality()
        locality.name = datas['name']
        locality.ref_id = datas['ref_id']
        locality.place_id = datas['place_id']
        locality.address = datas['address']
        locality.latlong = ndb.GeoPt(datas['lat'],datas['long'])        
      except StandardError as e:
        logger.error('Error occured for %s:%s' % (str(e), datas['name']))
        raise
      return locality
    
    def parse(self, url):
      r = urlfetch.fetch(url)
      if r.status_code == 200:
        return minidom.parseString(r.content)
    
    def send_enquiry_email(self, type, data, enq_datetime):
      params = {}
      email_count = 0
      
      user = self.user_info
      owner = self.profileDao.get_record(long(data.created_by.id()))
    
      try:
        # send email      
        subject = ("%s %s Enquire Email" % (self.app.config.get('app_name'), type))      

        # load email's template
        user_template_val = {
          "app_name": self.app.config.get('app_name'),
          "user_name": user.name,        
          "type_name": data.name,
          "email": user.email,
          "type": type,
          "date_time": enq_datetime,          
          "support_url": self.uri_for("contact", _full=True)
        }

        user_email_body_path = "emails/user_enquiry.txt"
        user_email_body = self.jinja2.render_template(user_email_body_path, **user_template_val)
        #print user_email_body
      
        owner_template_val = {
          "app_name": self.app.config.get('app_name'),
          "user_name": owner.name,        
          "type_name": data.name,
          "email": owner.email,
          "type": type,
          "date_time": enq_datetime,                  
          "support_url": self.uri_for("contact", _full=True)
        }

        owner_email_body_path = "emails/owner_enquiry.txt"
        owner_email_body = self.jinja2.render_template(owner_email_body_path, **owner_template_val)
        #print owner_email_body
      
        email_url = self.uri_for('taskqueue-send-email')
    
        taskqueue.add(url=email_url, params={        
          'to': user.email,
          'subject': subject,
          'body': user_email_body,
        })
      
        taskqueue.add(url=email_url, params={        
          'to': owner.email,
          'subject': subject,
          'body': owner_email_body,
        })
      
        email_count += 1
        logger.info("Your enquiry will be sent successfully.")          
      
      except StandardError as e:          
        logger.error("Error occured, %s, for Email %s!" % (str(e), user.email))      
      return email_count
