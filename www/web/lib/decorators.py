# *-* coding: UTF-8 *-*

# standard library imports
import logging
# related third party imports
from google.appengine.api import users
# local application/library specific imports
from models import UserRole
from settings import config, ROLE_FLAG_DICT
from utils import user_has_role

logger = logging.getLogger(__name__)

def user_required(handler):
    """
         Decorator for checking if there's a user associated
         with the current session.
         Will also fail if there's no session present.
    """

    def check_login(self, *args, **kwargs):
        """
            If handler has no login_url specified invoke a 403 error
        """
        if self.request.query_string != '':
            query_string = '?' + self.request.query_string
        else:
            query_string = ''

        continue_url = self.request.path_url + query_string
        login_url = self.uri_for('login', **{'continue': continue_url})

        try:
            user = self.auth.get_user_by_session()
            if not user:
                try:
                    self.redirect(login_url, abort=True)
                except (AttributeError, KeyError), e:
                    self.abort(403)
        except AttributeError, e:
            # avoid AttributeError when the session was delete from the server
            logging.error(e)
            self.user.unset_session()
            self.redirect(login_url)

        return handler(self, *args, **kwargs)
    return check_login


def role_required(role_name):
    """
         Decorator for checking if there's a admin user associated
         with the current session.
         Will also fail if there's no session present.
    """
    def check_role_decorator(handler):
      def check_role(self, *args, **kwargs):
        """
            If handler has no login_url specified invoke a 403 error
        """
        if self.request.query_string != '':
          query_string = '?' + self.request.query_string
        else:
          query_string = ''

        continue_url = self.request.path_url + query_string
        login_url = self.uri_for('login', **{'continue': continue_url})

        try:
          user = self.auth.get_user_by_session()
          if not user:
            try:
              self.redirect(login_url, abort=True)
            except (AttributeError, KeyError), e:
              self.abort(403)
          else:
            user_info = self.user_model.get_by_id(long(user['user_id']))
            if not user_has_role(user_info, role_name):
              logger.info('user does not have role')
              msg = ['This user does not have the required permission to access the page requested.', 'error']
              self.redirect(login_url)
        except AttributeError, e:
          # avoid AttributeError when the session was delete from the server
          logging.error(e)
          self.auth.unset_session()
          self.redirect(login_url)

        return handler(self, *args, **kwargs)
      return check_role
    return check_role_decorator

def cron_method(handler):
    """
    Decorator to indicate that this is a cron method and applies request.headers check
    """

    def check_if_cron(self, *args, **kwargs):
        """
         Check if it is executed by Cron in Staging or Production
         Allow run in localhost calling the url
        """
        if self.request.headers.get('X-AppEngine-Cron') is None \
            and config.get('environment') == "production" \
            and not users.is_current_user_admin():
            return self.error(403)
        else:
            return handler(self, *args, **kwargs)

    return check_if_cron


def taskqueue_method(handler):
    """
    Decorator to indicate that this is a taskqueue method and applies request.headers check
    """

    def check_if_taskqueue(self, *args, **kwargs):
        """
         Check if it is executed by Taskqueue in Staging or Production
         Allow run in localhost calling the url
        """
        if self.request.headers.get('X-AppEngine-TaskName') is None \
            and config.get('environment') == "production" \
            and not users.is_current_user_admin():
            return self.error(403)
        else:
            return handler(self, *args, **kwargs)

    return check_if_taskqueue
