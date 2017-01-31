import sys

from google.appengine.ext import ndb
sys.modules['ndb'] = ndb
from settings import config

import webapp2
import logging

from handlers.user.pricing_handler import PricingHandler
from handlers.user.subscription_handler import SubscriptionHandler

logger = logging.getLogger(__name__)

mappings  = [
    ('/api/get_pricing', PricingHandler),
    ('/api/subscribe', SubscriptionHandler),
]


application = webapp2.WSGIApplication(mappings,    
 config=config,
 debug=True)