import sys

from google.appengine.ext import ndb
sys.modules['ndb'] = ndb
from settings import config

from handlers.twitter.cron.compute_followers_daily import ComputeFollowersDailyHandler
from handlers.twitter.cron.delete_history_keywords_handler import DeleteHistoryKeywordsHandler
from handlers.twitter.cron.pull_keywords_source_handler import PullKeywordsSourceHandler

import webapp2
import logging

logger = logging.getLogger(__name__)


mappings  = [
    ('/cron/compute_followers_daily', ComputeFollowersDailyHandler),
    ('/cron/pull_keywords', PullKeywordsSourceHandler),
    ('/cron/delete_keyword_history', DeleteHistoryKeywordsHandler),
]             


application = webapp2.WSGIApplication(mappings,    
 config=config,
 debug=True)