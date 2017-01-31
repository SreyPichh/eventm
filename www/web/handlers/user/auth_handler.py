# standard library imports
import logging
import json

# related third party imports
import webapp2
from webapp2_extras import security
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
from webapp2_extras.appengine.auth.models import Unique
from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.runtime import apiproxy_errors
#from linkedin import linkedin

# local application/library specific imports
import models
import forms as forms
from web.lib import utils, captcha, twitter
from web.lib.basehandler import BaseHandler
from web.lib.decorators import user_required
from web.lib import facebook



class LoginRequiredHandler(BaseHandler):
    def get(self):
        continue_url, = self.request.get('continue', allow_multiple=True)
        self.redirect(users.create_login_url(dest_url=continue_url))

class RegisterBaseHandler(BaseHandler):
    """
    Base class for handlers with registration and login forms.
    """

    @webapp2.cached_property
    def form(self):
        return forms.RegisterForm(self)

class LoginHandler(BaseHandler):
    """
    Handler for authentication
    """

    def get(self):
        params = {}
        params['title'] = 'Login'
        return self.render_template('/user/login.html', **params)

    def post(self):
        """
        email: Get the email from POST dict
        password: Get the password from POST dict
        """

        if not self.form.validate():
            return self.get()
        email = self.form.email.data.lower()
        continue_url = self.request.get('continue').encode('ascii', 'ignore')

        try:
            if utils.is_email_valid(email):
                user = self.user_model.get_by_email(email)
                if user:
                    auth_id = user.auth_ids[0]
                else:
                    raise InvalidAuthIdError
            else:
                auth_id = "own:%s" % email
                user = self.user_model.get_by_auth_id(auth_id)

            password = self.form.password.data.strip()
            remember_me = True if str(self.request.POST.get('remember_me')) == 'on' else False

            # Password to SHA512
            # password = utils.hashing(password, self.app.config.get('salt'))

            # Try to login user with password
            # Raises InvalidAuthIdError if user is not found
            # Raises InvalidPasswordError if provided password
            # doesn't match with specified user
            self.auth.get_user_by_password(
                auth_id, password, remember=remember_me)

            # if user account is not activated, logout and redirect to home
            if (user.activated == False):
                # logout
                self.auth.unset_session()

                # redirect to home with error message
                resend_email_uri = self.uri_for('resend-account-activation', user_id=user.get_id(),
                                                token=self.user_model.create_resend_token(user.get_id()))
                message = ('Your account has not yet been activated. Please check your email to activate it or') + \
                          ' <a href="' + resend_email_uri + '">' + ('click here') + '</a> ' + ('to resend the email.')
                self.add_message(message, 'error')
                return self.redirect_to('home')

            # check twitter association in session
            twitter_helper = twitter.TwitterAuth(self)
            twitter_association_data = twitter_helper.get_association_data()
            if twitter_association_data is not None:
                if models.SocialUser.check_unique(user.key, 'twitter', str(twitter_association_data['id'])):
                    social_user = models.SocialUser(
                        user=user.key,
                        provider='twitter',
                        uid=str(twitter_association_data['id']),
                        extra_data=twitter_association_data
                    )
                    social_user.put()

            # check facebook association
            fb_data = None
            try:
                fb_data = json.loads(self.session['facebook'])
            except:
                pass

            if fb_data is not None:
                if models.SocialUser.check_unique(user.key, 'facebook', str(fb_data['id'])):
                    social_user = models.SocialUser(
                        user=user.key,
                        provider='facebook',
                        uid=str(fb_data['id']),
                        extra_data=fb_data
                    )
                    social_user.put()

            # check linkedin association
            li_data = None
            try:
                li_data = json.loads(self.session['linkedin'])
            except:
                pass

            if li_data is not None:
                if models.SocialUser.check_unique(user.key, 'linkedin', str(li_data['id'])):
                    social_user = models.SocialUser(
                        user=user.key,
                        provider='linkedin',
                        uid=str(li_data['id']),
                        extra_data=li_data
                    )
                    social_user.put()

            # end linkedin

            if self.app.config['log_visit']:
                try:
                    logVisit = models.LogVisit(
                        user=user.key,
                        uastring=self.request.user_agent,
                        ip=self.request.remote_addr,
                        timestamp=utils.get_date_time()
                    )
                    logVisit.put()
                except (apiproxy_errors.OverQuotaError, BadValueError):
                    logging.error("Error saving Visit Log in datastore")
            if continue_url:
              self.redirect(continue_url)
            else:
              #self.redirect_to('home')
              self.redirect_to('profile')
        except (InvalidAuthIdError, InvalidPasswordError), e:
            # Returns error message to self.response.write in
            # the BaseHandler.dispatcher
            message = ("Your email or password is incorrect. "
                        "Please try again (make sure your caps lock is off)")
            self.add_message(message, 'error')
            self.redirect_to('login', continue_url=continue_url) if continue_url else self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        return forms.LoginForm(self)


class SocialLoginHandler(BaseHandler):
    """
    Handler for Social authentication
    """

    def get(self, provider_name):
        provider = self.provider_info[provider_name]

        if not self.app.config.get('enable_federated_login'):
            message = ('Federated login is disabled.')
            self.add_message(message, 'warning')
            return self.redirect_to('login')
        callback_url = "%s/social_login/%s/complete" % (self.request.host_url, provider_name)

        if provider_name == "twitter":
            twitter_helper = twitter.TwitterAuth(self, redirect_uri=callback_url)
            self.redirect(twitter_helper.auth_url())

        elif provider_name == "facebook":
            self.session['linkedin'] = None
            perms = ['email', 'publish_stream', 'publish_actions', 'public_profile', 'user_birthday', 'user_photos']
            self.redirect(facebook.auth_url(self.app.config.get('fb_api_key'), callback_url, perms))

#         elif provider_name == 'linkedin':
#             self.session['facebook'] = None
#             authentication = linkedin.LinkedInAuthentication(
#                 self.app.config.get('linkedin_api'),
#                 self.app.config.get('linkedin_secret'),
#                 callback_url,
#                 [linkedin.PERMISSIONS.BASIC_PROFILE, linkedin.PERMISSIONS.EMAIL_ADDRESS])
#             self.redirect(authentication.authorization_url)

        elif provider_name in models.SocialUser.open_id_providers():
            continue_url = self.request.get('continue_url')
            if continue_url:
                dest_url = self.uri_for('social-login-complete', provider_name=provider_name, continue_url=continue_url)
            else:
                dest_url = self.uri_for('social-login-complete', provider_name=provider_name)
            try:
                login_url = users.create_login_url(federated_identity=provider['uri'], dest_url=dest_url)
                self.redirect(login_url)
            except users.NotAllowedError:
                self.add_message('You must enable Federated Login Before for this application.<br> '
                                 '<a href="http://appengine.google.com" target="_blank">Google App Engine Control Panel</a> -> '
                                 'Administration -> Application Settings -> Authentication Options', 'error')
                self.redirect_to('login')

        else:
            message = ('%s authentication is not yet implemented.' % provider.get('label'))
            self.add_message(message, 'warning')
            self.redirect_to('login')


class CallbackSocialLoginHandler(BaseHandler):
    """
    Callback (Save Information) for Social Authentication
    """

    def get(self, provider_name):
        if not self.app.config.get('enable_federated_login'):
            message = ('Federated login is disabled.')
            self.add_message(message, 'warning')
            return self.redirect_to('login')
        continue_url = self.request.get('continue_url')
        if provider_name == "twitter":
            oauth_token = self.request.get('oauth_token')
            oauth_verifier = self.request.get('oauth_verifier')
            twitter_helper = twitter.TwitterAuth(self)
            user_data = twitter_helper.auth_complete(oauth_token,
                                                     oauth_verifier)
            logging.info('twitter user_data: ' + str(user_data))
            if self.user:
                # new association with twitter
                user_info = self.user_model.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, 'twitter', str(user_data['user_id'])):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider='twitter',
                        uid=str(user_data['user_id']),
                        extra_data=user_data
                    )
                    social_user.put()

                    message = ('Twitter association added.')
                    self.add_message(message, 'success')
                else:
                    message = ('This Twitter account is already in use.')
                    self.add_message(message, 'error')
                if continue_url:
                    self.redirect(continue_url)
                else:
                    self.redirect_to('edit-profile')
            else:
                # login with twitter
                social_user = models.SocialUser.get_by_provider_and_uid('twitter',
                                                                        str(user_data['user_id']))
                if social_user:
                    # Social user exists. Need authenticate related site account
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    if continue_url:
                        self.redirect(continue_url)
                    else:
                        self.redirect_to('home')
                else:
                    uid = str(user_data['user_id'])
                    email = str(user_data.get('email'))
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url, user_data)

        # facebook association
        elif provider_name == "facebook":
            code = self.request.get('code')
            callback_url = "%s/social_login/%s/complete" % (self.request.host_url, provider_name)
            token = facebook.get_access_token_from_code(code, callback_url, self.app.config.get('fb_api_key'),
                                                        self.app.config.get('fb_secret'))
            access_token = token['access_token']
            fb = facebook.GraphAPI(access_token)
            user_data = fb.get_object('me')
            logging.info('facebook user_data: ' + str(user_data))
            if self.user:
                # new association with facebook
                user_info = self.user_model.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, 'facebook', str(user_data['id'])):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider='facebook',
                        uid=str(user_data['id']),
                        extra_data=user_data
                    )
                    social_user.put()

                    message = ('Facebook association added!')
                    self.add_message(message, 'success')
                else:
                    message = ('This Facebook account is already in use!')
                    self.add_message(message, 'error')
                if continue_url:
                    self.redirect(continue_url)
                else:
                    #self.redirect_to('edit-profile')
                    self.redirect_to('profile')
            else:
                # login with Facebook
                social_user = models.SocialUser.get_by_provider_and_uid('facebook',
                                                                        str(user_data['id']))
                if social_user:
                    # Social user exists. Need authenticate related site account
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    if continue_url:
                        self.redirect(continue_url)
                    else:
                        #self.redirect_to('home')
                        self.redirect_to('profile')
                else:
                    uid = str(user_data['id'])
                    email = str(user_data.get('email'))
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url, user_data)

                    # end facebook
        # association with linkedin
#         elif provider_name == "linkedin":
#             callback_url = "%s/social_login/%s/complete" % (self.request.host_url, provider_name)
#             authentication = linkedin.LinkedInAuthentication(
#                 self.app.config.get('linkedin_api'),
#                 self.app.config.get('linkedin_secret'),
#                 callback_url,
#                 [linkedin.PERMISSIONS.BASIC_PROFILE, linkedin.PERMISSIONS.EMAIL_ADDRESS])
#             authentication.authorization_code = self.request.get('code')
#             access_token = authentication.get_access_token()
#             link = linkedin.LinkedInApplication(authentication)
#             u_data = link.get_profile(selectors=['id', 'first-name', 'last-name', 'email-address'])
#             user_data = {
#                 'first_name': u_data.get('firstName'),
#                 'last_name': u_data.get('lastName'),
#                 'id': u_data.get('id'),
#                 'email': u_data.get('emailAddress')}
#             self.session['linkedin'] = json.dumps(user_data)
#             logging.info('linkedin user_data: ' + str(user_data))
# 
#             if self.user:
#                 # new association with linkedin
#                 user_info = self.user_model.get_by_id(long(self.user_id))
#                 if models.SocialUser.check_unique(user_info.key, 'linkedin', str(user_data['id'])):
#                     social_user = models.SocialUser(
#                         user=user_info.key,
#                         provider='linkedin',
#                         uid=str(user_data['id']),
#                         extra_data=user_data
#                     )
#                     social_user.put()
# 
#                     message = ('Linkedin association added!')
#                     self.add_message(message, 'success')
#                 else:
#                     message = ('This Linkedin account is already in use!')
#                     self.add_message(message, 'error')
#                 if continue_url:
#                     self.redirect(continue_url)
#                 else:
#                     self.redirect_to('edit-profile')
#             else:
#                 # login with Linkedin
#                 social_user = models.SocialUser.get_by_provider_and_uid('linkedin',
#                                                                         str(user_data['id']))
#                 if social_user:
#                     # Social user exists. Need authenticate related site account
#                     user = social_user.user.get()
#                     self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
#                     if self.app.config['log_visit']:
#                         try:
#                             logVisit = models.LogVisit(
#                                 user=user.key,
#                                 uastring=self.request.user_agent,
#                                 ip=self.request.remote_addr,
#                                 timestamp=utils.get_date_time()
#                             )
#                             logVisit.put()
#                         except (apiproxy_errors.OverQuotaError, BadValueError):
#                             logging.error("Error saving Visit Log in datastore")
#                     if continue_url:
#                         self.redirect(continue_url)
#                     else:
#                         self.redirect_to('home')
#                 else:
#                     uid = str(user_data['id'])
#                     email = str(user_data.get('email'))
#                     self.create_account_from_social_provider(provider_name, uid, email, continue_url, user_data)
# 
#                     # end linkedin

        # google, myopenid, yahoo OpenID Providers
        elif provider_name in models.SocialUser.open_id_providers():
            provider_display_name = models.SocialUser.PROVIDERS_INFO[provider_name]['label']
            # get info passed from OpenID Provider
            current_user = users.get_current_user()
            if current_user:
                if current_user.federated_identity():
                    uid = current_user.federated_identity()
                else:
                    uid = current_user.user_id()
                email = current_user.email()
            else:
                message = ('No user authentication information received from %s. '
                            'Please ensure you are logging in from an authorized OpenID Provider (OP).'
                            % provider_display_name)
                self.add_message(message, 'error')
                return self.redirect_to('login', continue_url=continue_url) if continue_url else self.redirect_to(
                    'login')
            if self.user:
                # add social account to user
                user_info = self.user_model.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, provider_name, uid):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider=provider_name,
                        uid=uid
                    )
                    social_user.put()

                    message = ('%s association successfully added.' % provider_display_name)
                    self.add_message(message, 'success')
                else:
                    message = ('This %s account is already in use.' % provider_display_name)
                    self.add_message(message, 'error')
                if continue_url:
                    self.redirect(continue_url)
                else:
                    self.redirect_to('edit-profile')
            else:
                # login with OpenID Provider
                social_user = models.SocialUser.get_by_provider_and_uid(provider_name, uid)
                if social_user:
                    # Social user found. Authenticate the user
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    if continue_url:
                        self.redirect(continue_url)
                    else:
                        self.redirect_to('home')
                else:
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url)
        else:
            message = ('This authentication method is not yet implemented.')
            self.add_message(message, 'warning')
            self.redirect_to('login', continue_url=continue_url) if continue_url else self.redirect_to('login')

    def create_account_from_social_provider(self, provider_name, uid, email=None, continue_url=None, user_data=None):
        """Social user does not exist yet so create it with the federated identity provided (uid)
        and create prerequisite user and log the user account in
        """
        provider_display_name = models.SocialUser.PROVIDERS_INFO[provider_name]['label']
        if models.SocialUser.check_unique_uid(provider_name, uid):
            # create user
            # Returns a tuple, where first value is BOOL.
            # If True ok, If False no new user is created
            # Assume provider has already verified email address
            # if email is provided so set activated to True
            auth_id = "%s:%s" % (provider_name, uid)
            if user_data:
              logging.info('User Data: ' + str(user_data))
              user_name = str(user_data.get('name'))
              user_gender = str(user_data.get('gender'))
              if user_name:
                name = user_name
              else:
                name = ''
              if user_gender:
                gender = user_gender
              else:
                gender = ''
              
            if email:
                unique_properties = ['email']
                user_info = self.auth.store.user_model.create_user(
                    auth_id, unique_properties, email=email, name=name, gender=gender,
                    activated=True
                )
            else:
                user_info = self.auth.store.user_model.create_user(
                    auth_id,  name=name, gender=gender, activated=True
                )
            if not user_info[0]:  # user is a tuple
                message = ('The account %s is already in use.' % provider_display_name)
                self.add_message(message, 'error')
                return self.redirect_to('signup')

            user = user_info[1]
            # create a basic role for the social user
            models.UserRole.create_basic_role(user)
                
            # create social user and associate with user
            social_user = models.SocialUser(
                user=user.key,
                provider=provider_name,
                uid=uid,
            )
            if user_data:
                social_user.extra_data = user_data
                self.session[provider_name] = json.dumps(user_data)  # TODO is this needed?
            social_user.put()
            # authenticate user
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
            if self.app.config['log_visit']:
                try:
                    logVisit = models.LogVisit(
                        user=user.key,
                        uastring=self.request.user_agent,
                        ip=self.request.remote_addr,
                        timestamp=utils.get_date_time()
                    )
                    logVisit.put()
                except (apiproxy_errors.OverQuotaError, BadValueError):
                    logging.error("Error saving Visit Log in datastore")

            message = ('Welcome!  You have been registered as a new user '
                        'and logged in through {}.').format(provider_display_name)
            self.add_message(message, 'success')
        else:
            message = ('This %s account is already in use.' % provider_display_name)
            self.add_message(message, 'error')
        if continue_url:
            self.redirect(continue_url)
        else:
            self.redirect_to('edit-profile')


class DeleteSocialProviderHandler(BaseHandler):
    """
    Delete Social association with an account
    """

    @user_required
    def post(self, provider_name):
        if self.user:
            user_info = self.user_model.get_by_id(long(self.user_id))
            if len(user_info.get_social_providers_info()['used']) > 1 and user_info.password is not None:
                social_user = models.SocialUser.get_by_user_and_provider(user_info.key, provider_name)
                if social_user:
                    social_user.key.delete()
                    message = ('%s successfully disassociated.' % provider_name)
                    self.add_message(message, 'success')
                else:
                    message = ('Social account on %s not found for this user.' % provider_name)
                    self.add_message(message, 'error')
            else:
                message = ('Social account on %s cannot be deleted for user.'
                           '  Please create a email and password to delete social account.' % provider_name)
                self.add_message(message, 'error')
        self.redirect_to('edit-profile')


class LogoutHandler(BaseHandler):
    """
    Destroy user session and redirect to login
    """

    def get(self):
        if self.user:
            #message = ("You've signed out successfully. Warning: Please clear all cookies and logout "
            #            "of OpenID providers too if you logged in on a public computer.")
            message = ("You've signed out successfully.")
            self.add_message(message, 'info')

        self.auth.unset_session()
        # User is logged out, let's try redirecting to login page
        try:
            self.redirect(self.auth_config['login_url'])
        except (AttributeError, KeyError), e:
            logging.error("Error logging out: %s" % e)
            message = ("User is logged out, but there was an error on the redirection.")
            self.add_message(message, 'error')
            return self.redirect_to('home')


class RegisterHandler(BaseHandler):
    """
    Handler for Sign Up Users
    """

    def get(self):
        """ Returns a simple HTML form for create a new user """

        if self.user:
            self.redirect_to('home')
        params = {}
        params['title'] = 'Sign Up'
        return self.render_template('user/register.html', **params)

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        name = self.form.name.data.strip()
        last_name = self.form.last_name.data.strip()
        email = self.form.email.data.lower()
        password = self.form.password.data.strip()

        # Password to SHA512
        # password = utils.hashing(password, self.app.config.get('salt'))

        # Passing password_raw=password so password will be hashed
        # Returns a tuple, where first value is BOOL.
        # If True ok, If False no new user is created
        unique_properties = ['email']
        auth_id = "own:%s" % email
        user = self.auth.store.user_model.create_user(
            auth_id, unique_properties, password_raw=password,
            name=name, last_name=last_name, email=email,
            ip=self.request.remote_addr
        )

        if not user[0]:  # user is a tuple
            if "email" in str(user[1]):
                message = ('Sorry, The email <strong>{}</strong> is already registered.').format(email)
            else:
                message = ('Sorry, The user is already registered.')
            self.add_message(message, 'error')
            return self.redirect_to('signup')
        else:
            # User registered successfully
            
            try:
                # create a basic role for the user
                models.UserRole.create_basic_role(user[1])
                
                # But if the user registered using the form, the user has to check their email to activate the account ???
                if not user[1].activated:
                    # send email
                    if self.app.config.get('send_mails'):
                      subject = ("%s Account Verification" % self.app.config.get('app_name'))
                      confirmation_url = self.uri_for("account-activation",
                                                      user_id=user[1].get_id(),
                                                      token=self.user_model.create_auth_token(user[1].get_id()),
                                                      _full=True)
  
                      # load email's template
                      template_val = {
                          "app_name": self.app.config.get('app_name'),
                          "email": email,
                          "confirmation_url": confirmation_url,
                          "support_url": self.uri_for("contact", _full=True)
                      }
                      body_path = "emails/account_activation.txt"
                      body = self.jinja2.render_template(body_path, **template_val)
  
                      email_url = self.uri_for('taskqueue-send-email')
                      taskqueue.add(url=email_url, params={
                          'to': str(email),
                          'subject': subject,
                          'body': body,
                      })

                    message = ('You were successfully registered. '
                                'Please check your email to activate your account.')
                    self.add_message(message, 'success')
                    #return self.redirect_to('home')
                    return self.redirect_to('profile')

                # If the user didn't register using registration form ???
                # db_user = self.auth.get_user_by_password(user[1].auth_ids[0], password)

                # Check Twitter association in session
                twitter_helper = twitter.TwitterAuth(self)
                twitter_association_data = twitter_helper.get_association_data()
                if twitter_association_data is not None:
                    if models.SocialUser.check_unique(user[1].key, 'twitter', str(twitter_association_data['id'])):
                        social_user = models.SocialUser(
                            user=user[1].key,
                            provider='twitter',
                            uid=str(twitter_association_data['id']),
                            extra_data=twitter_association_data
                        )
                        social_user.put()

                # check Facebook association
                fb_data = json.loads(self.session['facebook'])
                if fb_data is not None:
                    if models.SocialUser.check_unique(user.key, 'facebook', str(fb_data['id'])):
                        social_user = models.SocialUser(
                            user=user.key,
                            provider='facebook',
                            uid=str(fb_data['id']),
                            extra_data=fb_data
                        )
                        social_user.put()

                # check LinkedIn association
                li_data = json.loads(self.session['linkedin'])
                if li_data is not None:
                    if models.SocialUser.check_unique(user.key, 'linkedin', str(li_data['id'])):
                        social_user = models.SocialUser(
                            user=user.key,
                            provider='linkedin',
                            uid=str(li_data['id']),
                            extra_data=li_data
                        )
                        social_user.put()

                message = ('Welcome <strong>{}</strong>, you are now logged in.').format(email)
                self.add_message(message, 'success')
                #return self.redirect_to('home')
                return self.redirect_to('profile')
            except (AttributeError, KeyError), e:
                logging.error('Unexpected error creating the user %s: %s' % (email, e))
                message = ('Unexpected error creating the user %s' % email)
                self.add_message(message, 'error')
                return self.redirect_to('home')                

    @webapp2.cached_property
    def form(self):
        return forms.RegisterForm(self)


class AccountActivationHandler(BaseHandler):
    """
    Handler for account activation
    """

    def get(self, user_id, token):
        try:
            if not self.user_model.validate_auth_token(user_id, token):
                message = ('The link is invalid.')
                self.add_message(message, 'error')
                return self.redirect_to('home')

            user = self.user_model.get_by_id(long(user_id))
            # activate the user's account
            user.activated = True
            user.put()

            # Login User
            self.auth.get_user_by_token(int(user_id), token)

            # Delete token
            self.user_model.delete_auth_token(user_id, token)

            message = ('Congratulations, Your account <strong>{}</strong> has been successfully activated.').format(
                user.email)
            self.add_message(message, 'success')
            #self.redirect_to('home')
            return self.redirect_to('profile')
        
        except (AttributeError, KeyError, InvalidAuthIdError, NameError), e:
            logging.error("Error activating an account: %s" % e)
            message = ('Sorry, Some error occurred.')
            self.add_message(message, 'error')
            return self.redirect_to('home')


class ResendActivationEmailHandler(BaseHandler):
    """
    Handler to resend activation email
    """

    def get(self, user_id, token):
        try:
            if not self.user_model.validate_resend_token(user_id, token):
                message = ('The link is invalid.')
                self.add_message(message, 'error')
                return self.redirect_to('home')

            user = self.user_model.get_by_id(long(user_id))
            email = user.email

            if (user.activated == False):
                # send email
                subject = ("%s Account Verification" % self.app.config.get('app_name'))
                confirmation_url = self.uri_for("account-activation",
                                                user_id=user.get_id(),
                                                token=self.user_model.create_auth_token(user.get_id()),
                                                _full=True)

                # load email's template
                template_val = {
                    "app_name": self.app.config.get('app_name'),
                    "email": user.email,
                    "confirmation_url": confirmation_url,
                    "support_url": self.uri_for("contact", _full=True)
                }
                body_path = "emails/account_activation.txt"
                body = self.jinja2.render_template(body_path, **template_val)

                email_url = self.uri_for('taskqueue-send-email')
                taskqueue.add(url=email_url, params={
                    'to': str(email),
                    'subject': subject,
                    'body': body,
                })

                self.user_model.delete_resend_token(user_id, token)

                message = ('The verification email has been resent to %s. '
                            'Please check your email to activate your account.' % email)
                self.add_message(message, 'success')
                return self.redirect_to('home')
            else:
                message = ('Your account has been activated. Please <a href="/login/">sign in</a> to your account.')
                self.add_message(message, 'warning')
                return self.redirect_to('home')

        except (KeyError, AttributeError), e:
            logging.error("Error resending activation email: %s" % e)
            message = ('Sorry, Some error occurred.')
            self.add_message(message, 'error')
            return self.redirect_to('home')


class EditProfileHandler(BaseHandler):
    """
    Handler for Edit User Profile
    """

    @user_required
    def get(self):
        """ Returns a simple HTML form for edit profile """

        params = {}
        if self.user:
            user_info = self.user_model.get_by_id(long(self.user_id))            
            self.form.email.data = user_info.email
            self.form.name.data = user_info.name
            self.form.last_name.data = user_info.last_name
            providers_info = user_info.get_social_providers_info()
            if not user_info.password:
                params['local_account'] = False
            else:
                params['local_account'] = True
            params['used_providers'] = providers_info['used']
            params['unused_providers'] = providers_info['unused']

        #return self.render_template('user/edit_profile.html', **params)
        return self.redirect_to('profile')

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        email = self.form.email.data.lower()
        name = self.form.name.data.strip()
        last_name = self.form.last_name.data.strip()
        country = self.form.country.data
        tz = self.form.tz.data

        try:
            user_info = self.user_model.get_by_id(long(self.user_id))

            try:
                message = ''
                # update email if it has changed and it isn't already taken
                if email != user_info.email:
                    user_info.unique_properties = ['email', 'email']
                    uniques = [
                        'User.email:%s' % email,
                        'User.auth_id:own:%s' % email,
                    ]
                    # Create the unique email and auth_id.
                    success, existing = Unique.create_multi(uniques)
                    if success:
                        # free old uniques
                        Unique.delete_multi(
                            ['User.email:%s' % user_info.email, 'User.auth_id:own:%s' % user_info.email])
                        # The unique values were created, so we can save the user.
                        user_info.email = email
                        user_info.auth_ids[0] = 'own:%s' % email
                        message += ('Your new email is <strong>{}</strong>').format(email)

                    else:
                        message += (
                            'The email <strong>{}</strong> is already taken. Please choose another.').format(
                            email)
                        # At least one of the values is not unique.
                        self.add_message(message, 'error')
                        return self.get()
                user_info.name = name
                user_info.last_name = last_name
                user_info.country = country
                user_info.tz = tz
                user_info.put()
                message += " " + ('Thanks, your settings have been saved.')
                self.add_message(message, 'success')
                return self.get()

            except (AttributeError, KeyError, ValueError), e:
                logging.error('Error updating profile: ' + e)
                message = ('Unable to update profile. Please try again later.')
                self.add_message(message, 'error')
                return self.get()

        except (AttributeError, TypeError), e:
            login_error_message = ('Your session has expired.')
            self.add_message(login_error_message, 'error')
            self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        f = forms.EditProfileForm(self)
        #f.country.choices = self.countries_tuple
        #f.tz.choices = self.tz
        return f


class EditPasswordHandler(BaseHandler):
    """
    Handler for Edit User Password
    """

    @user_required
    def get(self):
        """ Returns a simple HTML form for editing password """

        params = {}
        return self.render_template('user/edit_password.html', **params)

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        current_password = self.form.current_password.data.strip()
        password = self.form.password.data.strip()

        try:
            user_info = self.user_model.get_by_id(long(self.user_id))
            auth_id = "own:%s" % user_info.email

            # Password to SHA512
            # current_password = utils.hashing(current_password, self.app.config.get('salt'))
            try:
                user = self.user_model.get_by_auth_password(auth_id, current_password)
                # Password to SHA512
                # password = utils.hashing(password, self.app.config.get('salt'))
                user.password = security.generate_password_hash(password, length=12)
                user.put()

                # send email
                subject = self.app.config.get('app_name') + " Account Password Changed"

                # load email's template
                template_val = {
                    "app_name": self.app.config.get('app_name'),
                    "first_name": user.name,
                    "email": user.email,
                    "email": user.email,
                    "reset_password_url": self.uri_for("password-reset", _full=True)
                }
                email_body_path = "emails/password_changed.txt"
                email_body = self.jinja2.render_template(email_body_path, **template_val)
                email_url = self.uri_for('taskqueue-send-email')
                taskqueue.add(url=email_url, params={
                    'to': user.email,
                    'subject': subject,
                    'body': email_body,
                    'sender': self.app.config.get('contact_sender'),
                })

                # Login User
                self.auth.get_user_by_password(user.auth_ids[0], password)
                self.add_message(('Password changed successfully.'), 'success')
                return self.redirect_to('edit-profile')
            except (InvalidAuthIdError, InvalidPasswordError), e:
                # Returns error message to self.response.write in
                # the BaseHandler.dispatcher
                message = ("Incorrect password! Please enter your current password to change your account settings.")
                self.add_message(message, 'error')
                return self.redirect_to('edit-password')
        except (AttributeError, TypeError), e:
            login_error_message = ('Your session has expired.')
            self.add_message(login_error_message, 'error')
            self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        return forms.EditPasswordForm(self)


class EditEmailHandler(BaseHandler):
    """
    Handler for Edit User's Email
    """

    @user_required
    def get(self):
        """ Returns a simple HTML form for edit email """

        params = {}
        if self.user:
            user_info = self.user_model.get_by_id(long(self.user_id))
            params['current_email'] = user_info.email

        return self.render_template('user/edit_email.html', **params)

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        new_email = self.form.new_email.data.strip()
        password = self.form.password.data.strip()

        try:
            user_info = self.user_model.get_by_id(long(self.user_id))
            auth_id = "own:%s" % user_info.email
            # Password to SHA512
            # password = utils.hashing(password, self.app.config.get('salt'))

            try:
                # authenticate user by its password
                user = self.user_model.get_by_auth_password(auth_id, password)

                # if the user change his/her email address
                if new_email != user.email:

                    # check whether the new email has been used by another user
                    aUser = self.user_model.get_by_email(new_email)
                    if aUser is not None:
                        message = ("The email %s is already registered." % new_email)
                        self.add_message(message, 'error')
                        return self.redirect_to("edit-email")

                    # send email
                    subject = ("%s Email Changed Notification" % self.app.config.get('app_name'))
                    user_token = self.user_model.create_auth_token(self.user_id)
                    confirmation_url = self.uri_for("email-changed-check",
                                                    user_id=user_info.get_id(),
                                                    encoded_email=utils.encode(new_email),
                                                    token=user_token,
                                                    _full=True)

                    # load email's template
                    template_val = {
                        "app_name": self.app.config.get('app_name'),
                        "first_name": user.name,
                        "email": user.email,
                        "new_email": new_email,
                        "confirmation_url": confirmation_url,
                        "support_url": self.uri_for("contact", _full=True)
                    }

                    old_body_path = "emails/email_changed_notification_old.txt"
                    old_body = self.jinja2.render_template(old_body_path, **template_val)

                    new_body_path = "emails/email_changed_notification_new.txt"
                    new_body = self.jinja2.render_template(new_body_path, **template_val)

                    email_url = self.uri_for('taskqueue-send-email')
                    taskqueue.add(url=email_url, params={
                        'to': user.email,
                        'subject': subject,
                        'body': old_body,
                    })
                    taskqueue.add(url=email_url, params={
                        'to': new_email,
                        'subject': subject,
                        'body': new_body,
                    })

                    # display successful message
                    msg = (
                        "Please check your new email for confirmation. Your email will be updated after confirmation.")
                    self.add_message(msg, 'success')
                    return self.redirect_to('edit-profile')

                else:
                    self.add_message(("You didn't change your email."), "warning")
                    return self.redirect_to("edit-email")


            except (InvalidAuthIdError, InvalidPasswordError), e:
                # Returns error message to self.response.write in
                # the BaseHandler.dispatcher
                message = ("Incorrect password! Please enter your current password to change your account settings.")
                self.add_message(message, 'error')
                return self.redirect_to('edit-email')

        except (AttributeError, TypeError), e:
            login_error_message = ('Your session has expired.')
            self.add_message(login_error_message, 'error')
            self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        return forms.EditEmailForm(self)


class PasswordResetHandler(BaseHandler):
    """
    Password Reset Handler with Captcha
    """

    def get(self):
        chtml = captcha.displayhtml(
            public_key=self.app.config.get('captcha_public_key'),
            use_ssl=(self.request.scheme == 'https'),
            error=None)
        if self.app.config.get('captcha_public_key') == "PUT_YOUR_RECAPCHA_PUBLIC_KEY_HERE" or \
                        self.app.config.get('captcha_private_key') == "PUT_YOUR_RECAPCHA_PUBLIC_KEY_HERE":
            chtml = '<div class="alert alert-error"><strong>Error</strong>: You have to ' \
                    '<a href="http://www.google.com/recaptcha/whyrecaptcha" target="_blank">sign up ' \
                    'for API keys</a> in order to use reCAPTCHA.</div>' \
                    '<input type="hidden" name="recaptcha_challenge_field" value="manual_challenge" />' \
                    '<input type="hidden" name="recaptcha_response_field" value="manual_challenge" />'
        params = {
            'captchahtml': chtml,
        }
        params['title'] = 'Password Reset'
        return self.render_template('user/password_reset.html', **params)

    def post(self):
        # check captcha
        challenge = self.request.POST.get('recaptcha_challenge_field')
        response = self.request.POST.get('recaptcha_response_field')
        remote_ip = self.request.remote_addr

        cResponse = captcha.submit(
            challenge,
            response,
            self.app.config.get('captcha_private_key'),
            remote_ip)

        if cResponse.is_valid:
            # captcha was valid... carry on..nothing to see here
            pass
        else:
            _message = ('Wrong image verification code. Please try again.')
            self.add_message(_message, 'danger')
            return self.redirect_to('password-reset')

        # check if we got an email
        email = str(self.request.POST.get('email')).lower().strip()
        if utils.is_email_valid(email):
            user = self.user_model.get_by_email(email)
            _message = ("If the email address you entered") + " (<strong>%s</strong>) " % email
        else:
            auth_id = "own:%s" % email
            user = self.user_model.get_by_auth_id(auth_id)
            _message = ("If the email you entered") + " (<strong>%s</strong>) " % email

        _message = _message + ("is associated with an account in our records, you will receive "
                                "an email from us with instructions for resetting your password. "
                                "<br>If you don't receive instructions within a minute or two, "
                                "check your email's spam and junk filters, or ") + \
                   '<a href="' + self.uri_for('contact') + '">' + ('contact us') + '</a> ' + (
            "for further assistance.")

        if user is not None:
            user_id = user.get_id()
            token = self.user_model.create_auth_token(user_id)
            email_url = self.uri_for('taskqueue-send-email')
            reset_url = self.uri_for('password-reset-check', user_id=user_id, token=token, _full=True)
            subject = ("%s Password Assistance" % self.app.config.get('app_name'))

            # load email's template
            template_val = {
                "email": user.email,
                "email": user.email,
                "reset_password_url": reset_url,
                "support_url": self.uri_for("contact", _full=True),
                "app_name": self.app.config.get('app_name'),
            }

            body_path = "emails/reset_password.txt"
            body = self.jinja2.render_template(body_path, **template_val)
            taskqueue.add(url=email_url, params={
                'to': user.email,
                'subject': subject,
                'body': body,
                'sender': self.app.config.get('contact_sender'),
            })
        self.add_message(_message, 'warning')
        return self.redirect_to('login')


class PasswordResetCompleteHandler(BaseHandler):
    """
    Handler to process the link of reset password that received the user
    """

    def get(self, user_id, token):
        verify = self.user_model.get_by_auth_token(int(user_id), token)
        params = {}
        if verify[0] is None:
            message = ('The URL you tried to use is either incorrect or no longer valid. '
                        'Enter your details again below to get a new one.')
            self.add_message(message, 'warning')
            return self.redirect_to('password-reset')

        else:
            return self.render_template('user/password_reset_complete.html', **params)

    def post(self, user_id, token):
        verify = self.user_model.get_by_auth_token(int(user_id), token)
        user = verify[0]
        password = self.form.password.data.strip()
        if user and self.form.validate():
            # Password to SHA512
            # password = utils.hashing(password, self.app.config.get('salt'))

            user.password = security.generate_password_hash(password, length=12)
            user.put()
            # Delete token
            self.user_model.delete_auth_token(int(user_id), token)
            # Login User
            self.auth.get_user_by_password(user.auth_ids[0], password)
            self.add_message(('Password changed successfully.'), 'success')
            return self.redirect_to('home')

        else:
            self.add_message(('The two passwords must match.'), 'error')
            return self.redirect_to('password-reset-check', user_id=user_id, token=token)

    @webapp2.cached_property
    def form(self):
        return forms.PasswordResetCompleteForm(self)


class EmailChangedCompleteHandler(BaseHandler):
    """
    Handler for completed email change
    Will be called when the user click confirmation link from email
    """

    def get(self, user_id, encoded_email, token):
        verify = self.user_model.get_by_auth_token(int(user_id), token)
        email = utils.decode(encoded_email)
        if verify[0] is None:
            message = ('The URL you tried to use is either incorrect or no longer valid.')
            self.add_message(message, 'warning')
            self.redirect_to('home')

        else:
            # save new email
            user = verify[0]
            user.email = email
            user.put()
            # delete token
            self.user_model.delete_auth_token(int(user_id), token)
            # add successful message and redirect
            message = ('Your email has been successfully updated.')
            self.add_message(message, 'success')
            self.redirect_to('edit-profile')

