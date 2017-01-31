
from dao.dao_factory import DaoFactory
from handlers.common.base_handler import BaseHandler
from models import User
from webapp2_extras import auth, jinja2, sessions
import json
import logging
import os
import webapp2

logger = logging.getLogger(__name__)

twitterDao = DaoFactory.create_ro_twitterdao()

'''
From: http://blog.abahgat.com/2013/01/07/user-authentication-with-webapp2-on-google-app-engine/
'''

class AllTwitterIdIterator(object):

    def process(self, user_id, twitter_userid):
        return True

    def cleanup(self):
        pass

class BaseApiHandler(BaseHandler):

    @staticmethod
    def get_social_id_from_request(request, id_param_name):
        social_id = request.get(id_param_name, None)
        if social_id is None:
            params = request.body
            input_dict = json.loads(params)
            social_id  = input_dict.get(id_param_name, None)
        return social_id

    
    def owned_by_user(self, user_id, social_id):
        #TODO: Validate that the social id is indeed added by this user.        
        return True
    
    def secure_process_social_id(self, id_param_name, fn):
        ctx = dict()
        ctx['valid'] = False
        user = self.auth.get_user_by_session()        
        if user is not None:
            social_id  = self.get_social_id_from_request(self.request, id_param_name)
            if social_id is not None and self.owned_by_user(user['user_id'], social_id): 
                fn(ctx, social_id, user['user_id'])
            else:
                # No social id
                self.error(400)
        else:
            self.error(401)

    def secure_process_twitter_id(self, fn):
        return self.secure_process_social_id('twitter_id', fn)

    def secure_process_instagram_id(self, fn):
        return self.secure_process_social_id('instagram_id', fn)
    
    def get_user_twitter_id(self):
        body = self.request.body
        body_dict  = json.loads(body)
        twitter_id = body_dict.get('twitter_id', None)
        user_id = body_dict.get('user_id', None)
        return (user_id, twitter_id)

    def iterate_all_twitter_accounts(self, twitterIdIterator):
            allusersquery = User.query()
            rs = allusersquery.fetch()
            all_users = []
            seen_twitter_ids  = set()
            map(lambda x: all_users.append(x), rs)
            process = True
            for singleuser in all_users:
                #TODO: Do only for paying users. based on User.role == ROLE_PREMIUM , say.
                if process:
                    singleuser_id = singleuser.key.id()
                    accounts = twitterDao.get_all_twitter_accounts(singleuser_id)
                    for singleaccount in accounts:
                        if singleaccount.twitter_userid in seen_twitter_ids:
                            logger.warning('Twitter user_id %s already processed for the day. Ignoring reprocess hence' %  \
                                           singleaccount.twitter_userid)
                        else:
                            proceed = twitterIdIterator.process(singleuser_id, singleaccount.twitter_userid)
                            twitterIdIterator.cleanup()
                            seen_twitter_ids.add(singleaccount.twitter_userid)
                            if not proceed:
                                process = False
                                break
                else:
                    break

    #Utility method to render the passed message in JSON
    def renderMessage(self, message):
        ctx = dict()
        ctx['valid'] = True
        ctx['message'] = message
        self.render_json(ctx)
