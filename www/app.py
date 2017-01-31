import logging
import webapp2
from webapp2_extras.routes import PathPrefixRoute
from webapp2_extras.appengine.users import login_required  

from settings import config, ENV_PROD
import sys
from google.appengine.ext import ndb
sys.modules['ndb'] = ndb

from web.lib.basehandler import BaseHandler
from web.handlers.user import auth_handler
from web.handlers.common import common_handler
from web.handlers.cms import business_handler, playground_handler, trainingcentre_handler, event_handler, dashboard_handler, childevent_handler, import_handler, match_handler, team_handler, import_teamhandler, profile_handler, bulk_handler
from web.handlers.app import home_handler, search_handler, details_handler, register_handler

logger = logging.getLogger(__name__)

def is_valid(value):
  return value is not None and len(value) > 0

#TODO: Remove all handlers from here. They are here now only for testing static template pages.
class MainPage(BaseHandler):

  def get(self):
    params = {}
    params['bg_class'] = 'home-bg'
    self.render_template('/home/home2.html', **params)

class Main2Page(BaseHandler):

  def get(self):
    ctx = self.get_base_variables()
    self.render_response('/home/home.html', **ctx)

class SearchPage(BaseHandler):

  def get(self):
    params = {}
    params['bg_class'] = ''
    self.render_template('/home/search.html', **params)

class DetailsPage(BaseHandler):

  def get(self):
    params = {}
    params['bg_class'] = ''
    self.render_template('/home/details.html', **params)

class PrivacyPolicyPage(BaseHandler):

  def get(self):
    params = {}
    params['title'] = 'privacy policy'
    self.render_template('/home/privacy_policy.html', **params)
    
mappings = [
  webapp2.Route('/details', DetailsPage),
  webapp2.Route('/home2', Main2Page),  
  #static pages
  webapp2.Route('/contact', MainPage, name="contact"),
  webapp2.Route('/about', MainPage, name="about"),
  webapp2.Route(r'/robots.txt', common_handler.RobotsHandler, name='robots'),
  webapp2.Route(r'/humans.txt', common_handler.HumansHandler, name='humans'),
  webapp2.Route(r'/sitemap.xml', common_handler.SitemapHandler, name='sitemap'),
  webapp2.Route(r'/crossdomain.xml', common_handler.CrossDomainHandler, name='crossdomain'),
  webapp2.Route('/privacypolicy', PrivacyPolicyPage, name="privacypolicy"),
  #user
  webapp2.Route('/taskqueue-send-email/', common_handler.SendEmailHandler, name='taskqueue-send-email'),
  webapp2.Route('/_ah/login_required', auth_handler.LoginRequiredHandler),
  webapp2.Route('/login', auth_handler.LoginHandler, name='login'),
  webapp2.Route('/logout', auth_handler.LogoutHandler, name='logout'),
  webapp2.Route('/social_login/<provider_name>', auth_handler.SocialLoginHandler, name='social-login'),
  webapp2.Route('/social_login/<provider_name>/complete', auth_handler.CallbackSocialLoginHandler, name='social-login-complete'),
  webapp2.Route('/social_login/<provider_name>/delete', auth_handler.DeleteSocialProviderHandler, name='delete-social-provider'),
  webapp2.Route('/signup', auth_handler.RegisterHandler, name='signup'),
  webapp2.Route('/activation/<user_id>/<token>', auth_handler.AccountActivationHandler, name='account-activation'),
  webapp2.Route('/resend/<user_id>/<token>', auth_handler.ResendActivationEmailHandler, name='resend-account-activation'),
  webapp2.Route('/settings/profile', auth_handler.EditProfileHandler, name='edit-profile'),
  webapp2.Route('/settings/password', auth_handler.EditPasswordHandler, name='edit-password'),
  webapp2.Route('/settings/email', auth_handler.EditEmailHandler, name='edit-email'),
  webapp2.Route('/password-reset/', auth_handler.PasswordResetHandler, name='password-reset'),
  webapp2.Route('/password-reset/<user_id>/<token>', auth_handler.PasswordResetCompleteHandler, name='password-reset-check'),
  webapp2.Route('/change-email/<user_id>/<encoded_email>/<token>', auth_handler.EmailChangedCompleteHandler, name='email-changed-check'),
  #cms
  webapp2.Route('/cms/business/create', business_handler.ManageBusinessHandler, name='create-business'),
  webapp2.Route('/cms/business/edit/<business_id>', business_handler.ManageBusinessHandler, name='edit-business'),
  webapp2.Route('/cms/trainingcentre/create', trainingcentre_handler.ManageTrainingCentreHandler, name='select-for-trainingcentre'),
  webapp2.Route('/cms/trainingcentre/create/<business_id>', trainingcentre_handler.ManageTrainingCentreHandler, name='create-trainingcentre'),
  webapp2.Route('/cms/trainingcentre/edit/<business_id>/<trainingcentre_id>', trainingcentre_handler.ManageTrainingCentreHandler, name='edit-trainingcentre'),
  webapp2.Route('/upload/trainingcentre/cover', trainingcentre_handler.UploadTrainingCentreCoverHandler, name='upload-trainingcentre-cover'),
  webapp2.Route('/enquire/trainingcentre', trainingcentre_handler.EnquireTrainingCentreHandler, name='enquire-trainingcentre'),
  webapp2.Route('/cms/event/create', event_handler.ManageEventHandler, name='select-for-event'),
  webapp2.Route('/cms/event/create/<business_id>', event_handler.ManageEventHandler, name='create-event'),
  webapp2.Route('/cms/event/edit/<business_id>/<event_id>', event_handler.ManageEventHandler, name='edit-event'),
  webapp2.Route('/cms/childevent/create', childevent_handler.ManageChildEventHandler, name='select-for-childevent'),
  webapp2.Route('/cms/childevent/create/<event_id>', childevent_handler.ManageChildEventHandler, name='create-child-event'),
  webapp2.Route('/cms/childevent/edit/<event_id>/<childevent_id>', childevent_handler.ManageChildEventHandler, name='edit-child-event'),
  webapp2.Route('/cms/playground/create', playground_handler.ManagePlaygroundHandler, name='create-playground'),
  webapp2.Route('/cms/playground/edit/<playground_id>', playground_handler.ManagePlaygroundHandler, name='edit-playground'),
  webapp2.Route('/upload/playground/cover', playground_handler.UploadPlaygroundCoverHandler, name='upload-playground-cover'),
  webapp2.Route('/enquire/playground', playground_handler.EnquirePlaygroundHandler, name='enquire-playground'),
  webapp2.Route('/cms/dashboard', dashboard_handler.DashboardHandler, name='dashboard'),
  webapp2.Route('/cms/import', import_handler.ImportHandler, name='import'),
  webapp2.Route('/cms/bulk/data/create', bulk_handler.ManageBulkDataHandler, name='create-bulk-data'),
  #webapp2.Route('/cms/user/profile', dashboard_handler.ProfileHandler, name='profile'),
  #webapp2.Route('/cms/user/edit/profile/<user_id>', dashboard_handler.ProfileHandler, name='edit-profile'),
  webapp2.Route('/cms/user/invite/friends', profile_handler.InviteFriendsHandler, name='invite-friends'),
  webapp2.Route('/cms/user/profile', profile_handler.ProfileHandler, name='profile'),
  webapp2.Route('/edit/user/name', profile_handler.EditUserNameHandler, name='edit-user-name'),
  webapp2.Route('/edit/user/dob', profile_handler.EditUserDOBHandler, name='edit-user-dob'),
  webapp2.Route('/edit/user/gender', profile_handler.EditUserGenderHandler, name='edit-user-gender'),
  webapp2.Route('/edit/user/profession', profile_handler.EditUserProfessionHandler, name='edit-user-profession'),
  webapp2.Route('/edit/user/phone', profile_handler.EditUserPhoneHandler, name='edit-user-phone'),
  webapp2.Route('/edit/user/status', profile_handler.EditUserStatusHandler, name='edit-user-status'),
  webapp2.Route('/edit/user/locality', profile_handler.EditUserLocalityHandler, name='edit-user-locality'),
  webapp2.Route('/edit/user/city', profile_handler.EditUserCityHandler, name='edit-user-city'),
  webapp2.Route('/edit/user/image', profile_handler.EditUserImageHandler, name='edit-user-image'),
  webapp2.Route('/upload/profile/gallery', profile_handler.UploadProfileGalleryHandler, name='upload-profile-gallery'),
  webapp2.Route('/edit/user/sport', profile_handler.EditUserSportHandler, name='edit-user-sport'),
  
  webapp2.Route('/event/register', register_handler.ManageRegisterHandler, name='event-register'),
  webapp2.Route('/event/register/<record_id>', register_handler.ManageRegisterHandler, name='edit-event-register'),
  
  webapp2.Route('/cms/match/create', match_handler.ManageMatchHandler, name='select-for-match'),
  webapp2.Route('/cms/match/create/<event_id>', match_handler.ManageMatchHandler, name='create-match'),
  webapp2.Route('/cms/match/edit/<event_id>/<match_id>', match_handler.ManageMatchHandler, name='edit-match'),
  
  webapp2.Route('/cms/team/create', team_handler.ManageTeamHandler, name='create-team'),
  webapp2.Route('/cms/team/edit/<team_id>', team_handler.ManageTeamHandler, name='edit-team'),
  webapp2.Route('/cms/team/player/edit/<team_id>', team_handler.EditTeamPlayerHandler, name='edit-team-player'),
  webapp2.Route('/cms/team/view/<team_id>', team_handler.ViewTeamHandler, name='view-team'),
  webapp2.Route('/edit/team/name', team_handler.EditTeamNameHandler, name='edit-team-name'),
  webapp2.Route('/edit/team/sport', team_handler.EditTeamSportHandler, name='edit-team-sport'),
  webapp2.Route('/edit/team/preferdays', team_handler.EditTeamPreferDaysHandler, name='edit-team-preferdays'),
  webapp2.Route('/edit/team/eventsnum', team_handler.EditTeamEventsNumHandler, name='edit-team-eventsnum'),
  webapp2.Route('/edit/team/category', team_handler.EditTeamCategoryHandler, name='edit-team-category'),
  webapp2.Route('/edit/team/logo', team_handler.EditTeamLogoHandler, name='edit-team-logo'),
  webapp2.Route('/upload/team/gallery', team_handler.UploadTeamGalleryHandler, name='upload-team-gallery'),
  webapp2.Route('/cms/player/create', team_handler.ManagePlayerHandler, name='create-player'),
  webapp2.Route('/cms/player/edit/<player_id>', team_handler.ManagePlayerHandler, name='edit-player'),
  webapp2.Route('/cms/import/team', import_teamhandler.ImportTeamHandler, name='import-team'),
  webapp2.Route('/cms/save/locality', import_teamhandler.SaveLocalityHandler, name='save-locality'),
  webapp2.Route('/cms/search/update', import_teamhandler.SearchUpdateHandler, name='search-update'),
  
  #app
  webapp2.Route('/search', search_handler.GenericSearchHandler, name='search'),
  PathPrefixRoute('/playgrounds', 
    [ webapp2.Route('/search', search_handler.PlaygroundSearchHandler, name='pg-search'),
      webapp2.Route('/<city_name>/<locality_name>/<entity_id>/<entity_alias>', details_handler.PlaygroundDetailsHandler, name='pg-details'),
      webapp2.Route(r'/<city_name>/<locality_name>', search_handler.PlaygroundSearchHandler, name='pg-locality-home'),
      #webapp2.Route(r'/<city_name>/<sport>', search_handler.PlaygroundSearchHandler, name='pg-sport-home'),
      webapp2.Route(r'/<city_name>', search_handler.PlaygroundSearchHandler, name='pg-city-home'),
      webapp2.Route('/', search_handler.PlaygroundSearchHandler, name='pg-home'),
    ]),
  PathPrefixRoute('/training-centres', 
    [ webapp2.Route('/search', search_handler.TrainingCentreSearchHandler, name='tc-search'),
      webapp2.Route('/<city_name>/<locality_name>/<entity_id>/<entity_alias>', details_handler.TrainingCentreDetailsHandler, name='tc-details'),
      webapp2.Route(r'/<city_name>/<locality_name>', search_handler.TrainingCentreSearchHandler, name='tc-locality-home'),
      webapp2.Route(r'/<city_name>', search_handler.TrainingCentreSearchHandler, name='tc-city-home'),
      webapp2.Route('/', search_handler.TrainingCentreSearchHandler, name='tc-home'),
    ]),
  #TODO: Use PathPrefixRoute for everything
  PathPrefixRoute('/events', 
    [ webapp2.Route('/search', search_handler.EventSearchHandler, name='event-search'),
      webapp2.Route('/<city_name>/<entity_id>/<entity_alias>', details_handler.EventDetailsHandler, name='event-details'),
      webapp2.Route('/<city_name>/<locality_name>', search_handler.EventSearchHandler, name='event-sports-home'),
      webapp2.Route('/<city_name>', search_handler.EventSearchHandler, name='event-city-home'),
      webapp2.Route('/', search_handler.EventSearchHandler, name='event-home')
    ]),

  webapp2.Route('/<city_name>/<sport>', home_handler.CityHomeHandler, name='city-sports-home'),
  webapp2.Route('/<city_name>', home_handler.CityHomeHandler, name='city-home'),
  webapp2.Route('/', home_handler.CityHomeHandler, name='home'),
]            
    
app = webapp2.WSGIApplication(mappings,
config=config,
debug=True  # not ENV_PROD
)
