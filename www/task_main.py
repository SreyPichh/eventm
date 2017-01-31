import sys

from google.appengine.ext import ndb
from handlers.twitter.task.pull_twitter_data_handler import PullTwitterDataTaskHandler, PullTwitterUserStatusTaskHandler
sys.modules['ndb'] = ndb
from settings import config

import webapp2
import logging

logger = logging.getLogger(__name__)


mappings  = [
    ('/tasks/pull_twitter_data', PullTwitterDataTaskHandler),
    ('/tasks/pull_twitter_user_status', PullTwitterUserStatusTaskHandler),
]             


application = webapp2.WSGIApplication(mappings,    
 config=config,
 debug=True)