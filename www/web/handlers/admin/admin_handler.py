__author__ = 'akkumar'

import logging
from handlers.common.base_handler import BaseHandler
from settings import ROLE_ADMIN, FLAG_ADMIN

logger = logging.getLogger(__name__)

class AdminHandler(BaseHandler):

    def get(self):
        user = self.auth.get_user_by_session()
        if user is None:
            self.redirect('/login')
        else:
            if user['role'] & FLAG_ADMIN == 0:
                logger.warning('Given user role %s not an admin . Not allowing hence ' % user['role'])
                self.redirect('/login')
            else:
                mydict = self.get_base_variables()
                self.render_response('admin/admin.html', **mydict)

    def post(self):
        pass