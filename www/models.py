import time
import logging
from webapp2_extras.appengine.auth.models import User
from google.appengine.ext import ndb
from webapp2_extras import security
 
from settings import ROLE_BASIC, ROLE_BUSINESS, ROLE_ADMIN
logger = logging.getLogger(__name__)

class User(User):
    """
    Universal user model. Can be used with App Engine's default users API,
    own auth or third party authentication methods (OpenID, OAuth etc).
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #: User Name
    name = ndb.StringProperty()
    #: User Last Name
    last_name = ndb.StringProperty()
    #: User email
    email = ndb.StringProperty()
    #: User image
    image = ndb.BlobKeyProperty()
    #: User image url
    image_url = ndb.StringProperty()
    #: User Sport
    sport = ndb.StringProperty()
    #: User Phone Number
    phone = ndb.StringProperty(indexed = True)
    #: User Locality
    locality = ndb.StringProperty(indexed = True)
    #: User Locality Id
    locality_id = ndb.StringProperty(indexed = True)
    
    city = ndb.StringProperty(indexed = True)
    #: User Want to
    i_want = ndb.StringProperty()
    
    dob = ndb.DateTimeProperty()
    
    gender = ndb.StringProperty()
    
    profession = ndb.StringProperty()    
    
    #: Hashed password. Only set for own authentication.
    # Not required because third party authentication
    # doesn't use password.
    password = ndb.StringProperty()
    #: Account activation verifies email
    activated = ndb.BooleanProperty(default=True)
    
    @classmethod
    def get_by_email(cls, email):
        """Returns a user object based on an email.

        :param email:
            String representing the user email. Examples:

        :returns:
            A user object.
        """
        return cls.query(cls.email == email).get()

    @classmethod
    def create_resend_token(cls, user_id):
        entity = cls.token_model.create(user_id, 'resend-activation-mail')
        return entity.token

    @classmethod
    def validate_resend_token(cls, user_id, token):
        return cls.validate_token(user_id, 'resend-activation-mail', token)

    @classmethod
    def delete_resend_token(cls, user_id, token):
        cls.token_model.get_key(user_id, 'resend-activation-mail', token).delete()

    def get_social_providers_names(self):
        social_user_objects = SocialUser.get_by_user(self.key)
        result = []
#        import logging
        for social_user_object in social_user_objects:
#            logging.error(social_user_object.extra_data['screen_name'])
            result.append(social_user_object.provider)
        return result

    def get_social_providers_info(self):
        providers = self.get_social_providers_names()
        result = {'used': [], 'unused': []}
        for k,v in SocialUser.PROVIDERS_INFO.items():
            if k in providers:
                result['used'].append(v)
            else:
                result['unused'].append(v)
        return result

    # TODO:: Old methods... retained for now. Need to relook
    def set_password(self, raw_password):
        """Sets the password for the current user
        :param raw_password:
            The raw password which wi
            ll be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)
    
    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.
        
        :param user_id:
            The user_id of the requesting user.
        :param token:
            The token string to be verified.
        :returns:
            A tuple ``(User, timestamp)``, with a user object and
            the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp
        
        return None, None

#ref: http://codingrecipes.com/how-to-write-a-permission-system-using-bits-and-bitwise-operations-in-php
class UserRole(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    role = ndb.IntegerProperty()
    
    @classmethod
    def get_role_for_user(cls, user):
      user_role = cls.query(cls.user == user.key).fetch(1)
      return user_role[0].role if user_role is not None and len(user_role) > 0 else None
      
    @classmethod
    def create_basic_role(cls, user):
      cls.create_role(user, ROLE_BASIC)
    
    @classmethod
    def create_business_role(cls, user):
      cls.create_role(user, ROLE_BUSINESS)

    @classmethod
    def create_admin_role(cls, user):
      cls.create_role(user, ROLE_ADMIN)
    
    @classmethod
    def create_role(self, user, role):
      userRole = UserRole()
      userRole.user = user.key
      userRole.role = role
      userRole.put()
      
  
class LogVisit(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    uastring = ndb.StringProperty()
    ip = ndb.StringProperty()
    timestamp = ndb.StringProperty()


class OptionsSite(ndb.Model):
    name = ndb.KeyProperty
    value = ndb.StringProperty()
    @classmethod
    def get_option(cls,option_name):
        return cls.query(name=option_name)


class LogEmail(ndb.Model):
    sender = ndb.StringProperty(
        required=True)
    to = ndb.StringProperty(
        required=True)
    subject = ndb.StringProperty(
        required=True)
    body = ndb.TextProperty()
    when = ndb.DateTimeProperty()


class SocialUser(ndb.Model):
    PROVIDERS_INFO = { # uri is for OpenID only (not OAuth)
        'google': {'name': 'google', 'label': 'Google', 'uri': 'gmail.com'},
        'facebook': {'name': 'facebook', 'label': 'Facebook', 'uri': ''},
        'linkedin': {'name': 'linkedin', 'label': 'LinkedIn', 'uri': ''},
        'twitter': {'name': 'twitter', 'label': 'Twitter', 'uri': ''}
    }

    user = ndb.KeyProperty(kind=User)
    provider = ndb.StringProperty()
    uid = ndb.StringProperty()
    extra_data = ndb.JsonProperty()

    @classmethod
    def get_by_user(cls, user):
        return cls.query(cls.user == user).fetch()

    @classmethod
    def get_by_user_and_provider(cls, user, provider):
        return cls.query(cls.user == user, cls.provider == provider).get()

    @classmethod
    def get_by_provider_and_uid(cls, provider, uid):
        return cls.query(cls.provider == provider, cls.uid == uid).get()

    @classmethod
    def check_unique_uid(cls, provider, uid):
        # pair (provider, uid) should be unique
        test_unique_provider = cls.get_by_provider_and_uid(provider, uid)
        if test_unique_provider is not None:
            return False
        else:
            return True
    
    @classmethod
    def check_unique_user(cls, provider, user):
        # pair (user, provider) should be unique
        test_unique_user = cls.get_by_user_and_provider(user, provider)
        if test_unique_user is not None:
            return False
        else:
            return True

    @classmethod
    def check_unique(cls, user, provider, uid):
        # pair (provider, uid) should be unique and pair (user, provider) should be unique
        return cls.check_unique_uid(provider, uid) and cls.check_unique_user(provider, user)
    
    @staticmethod
    def open_id_providers():
        return [k for k,v in SocialUser.PROVIDERS_INFO.items() if v['uri']]


#Supporting models which will be used by other models as StructuredProperty
class Address(ndb.Model):
  line1 = ndb.StringProperty(indexed = False)
  line2 = ndb.StringProperty(indexed = False)
  locality = ndb.StringProperty(indexed = True)
  locality_id = ndb.StringProperty(indexed = True)
  city = ndb.StringProperty(indexed = True)
  pin = ndb.IntegerProperty(indexed = True)
  latlong = ndb.GeoPtProperty(indexed = True) 
  
class ContactInfo(ndb.Model):
  person_name = ndb.StringProperty(indexed = False, repeated = True)
  email = ndb.StringProperty(indexed = False, repeated = True)
  phone = ndb.StringProperty(indexed = False, repeated = True)
  website = ndb.StringProperty(indexed = True)
  facebook = ndb.StringProperty(indexed = False)
  twitter = ndb.StringProperty(indexed = False)
  youtube = ndb.StringProperty(indexed = False)
  gplus = ndb.StringProperty(indexed = False)
  
class CustomInfo(ndb.Model):
  name = ndb.StringProperty()
  value = ndb.TextProperty()
  
class ReviewStats(ndb.Model):
  ratings_count = ndb.IntegerProperty()
  avg_rating = ndb.FloatProperty()
  reviews_count = ndb.IntegerProperty()

#Actual Models that will be directly used by the application
#For all the business related models, ids will be created by the application during entity creation
#Represents a business entity that can own one or many playgrounds, training clubs or events or a combination of these     
class Business(ndb.Model): 
  name = ndb.StringProperty(indexed = True)
  alias = ndb.StringProperty(indexed = True)
  description = ndb.TextProperty()
  logo = ndb.BlobKeyProperty()
  contact_info = ndb.StructuredProperty(ContactInfo, repeated = False)
  review_stats = ndb.StructuredProperty(ReviewStats, repeated = False)
  status = ndb.IntegerProperty(indexed = True) #0 - pending creation, 1 - pending approval, 2 - approved
  owners = ndb.KeyProperty(kind=User, repeated=True) #A list of users who has the permission to update this
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)
  
class Playground(ndb.Model):
  name = ndb.StringProperty(indexed = True)
  alias = ndb.StringProperty(indexed = True)
  sport = ndb.StringProperty(indexed = True)
  caption = ndb.TextProperty()
  business_id = ndb.KeyProperty(indexed = True, kind = 'Business') #Need to check whether this works as desired for custom created keys
  description = ndb.TextProperty()
  cover = ndb.BlobKeyProperty()
  address = ndb.StructuredProperty(Address, repeated = False)
  contact_info = ndb.StructuredProperty(ContactInfo, repeated = False)
  custom_info = ndb.LocalStructuredProperty(CustomInfo, repeated = True)
  review_stats = ndb.StructuredProperty(ReviewStats, repeated = False)
  status = ndb.IntegerProperty(indexed = True) #0 - pending creation, 1 - pending approval, 2 - approved
  featured = ndb.BooleanProperty()
  owners = ndb.KeyProperty(kind=User, repeated=True) #A list of users who has the permission to update this
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)

class TrainingCentre(ndb.Model):
  name = ndb.StringProperty(indexed = True)
  alias = ndb.StringProperty(indexed = True)
  sport = ndb.StringProperty(indexed = True)
  caption = ndb.TextProperty()
  business_id = ndb.KeyProperty(indexed = True, kind = 'Business') #Need to check whether this works as desired for custom created keys
  description = ndb.TextProperty()
  cover = ndb.BlobKeyProperty()
  address = ndb.StructuredProperty(Address, repeated = False)
  contact_info = ndb.StructuredProperty(ContactInfo, repeated = False)
  custom_info = ndb.LocalStructuredProperty(CustomInfo, repeated = True)
  review_stats = ndb.StructuredProperty(ReviewStats, repeated = False)
  status = ndb.IntegerProperty(indexed = True) #0 - pending creation, 1 - pending approval, 2 - approved
  featured = ndb.BooleanProperty()
  owners = ndb.KeyProperty(kind=User, repeated=True) #A list of users who has the permission to update this
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)
  
# Model to store info about parent and child events
class Event(ndb.Model):
  name = ndb.StringProperty(indexed = True)
  alias = ndb.StringProperty(indexed = True)
  sport = ndb.StringProperty(indexed = True)
  caption = ndb.TextProperty()
  business_id = ndb.KeyProperty(kind = 'Business') #updated for a parent event
  child_events = ndb.KeyProperty(kind = 'Event', repeated = True) #updated for a parent event
  parent_event_id = ndb.KeyProperty(kind = 'Event', repeated = False) #updated for child event
  playground_id = ndb.KeyProperty(kind = 'Playground', repeated = False) #updated for child event
  description = ndb.TextProperty() #updated for both parent and child event
  address = ndb.StructuredProperty(Address, repeated = False)
  contact_info = ndb.StructuredProperty(ContactInfo, repeated = False) #updated for both parent and child event
  custom_info = ndb.LocalStructuredProperty(CustomInfo, repeated = True)
  start_datetime = ndb.DateTimeProperty(indexed = True)
  end_datetime = ndb.DateTimeProperty(indexed = True)
  review_stats = ndb.StructuredProperty(ReviewStats, repeated = False)
  status = ndb.IntegerProperty(indexed = True) #0 - pending creation, 1 - pending approval, 2 - approved
  featured = ndb.BooleanProperty()
  registration_open = ndb.BooleanProperty()
  owners = ndb.KeyProperty(kind=User, repeated=True) #A list of users who has the permission to update this
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)
  
class Team(ndb.Model):
  name = ndb.StringProperty(indexed = True)
  alias = ndb.StringProperty(indexed = True)
  sport = ndb.StringProperty(indexed = True)
  logo = ndb.BlobKeyProperty()
  logo_url = ndb.StringProperty()
  category = ndb.StringProperty()
  prefer_days = ndb.StringProperty()
  events_num = ndb.StringProperty()
  players = ndb.KeyProperty(repeated = True)
  owners = ndb.KeyProperty(kind=User, repeated=True) #A list of users who has the permission to update this
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)
  
class Player(ndb.Model):
  name = ndb.StringProperty(indexed = True)  
  sport = ndb.StringProperty() # Can contain a list of sports, comma seperated
  email = ndb.StringProperty(indexed = True)
  phone = ndb.StringProperty(indexed = True)
  user_id = ndb.KeyProperty() # Asscociate the player to an existing user
  teams = ndb.KeyProperty(kind = 'Team', repeated = True) # A player can belong to multiple teams
  owners = ndb.KeyProperty(kind=User, repeated=True) #A list of users who has the permission to update this
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)
  
#Using an Expando model to have sport specific details here.
class Match(ndb.Model):
  name = ndb.StringProperty(indexed = True)
  alias = ndb.StringProperty(indexed = True)
  event_id = ndb.KeyProperty(kind = 'Event')
  playground_id = ndb.KeyProperty(kind = 'Playground', repeated = False)
  sport = ndb.StringProperty(indexed = True)
  participants = ndb.KeyProperty(repeated = True) #For the list of teams participating in this match. To be used for Players, for individual sports
  participant_type = ndb.StringProperty(indexed = True)
  start_datetime = ndb.DateTimeProperty(indexed = True)
  end_datetime = ndb.DateTimeProperty(indexed = True)
  result = ndb.TextProperty()
  summary = ndb.TextProperty()
  status = ndb.IntegerProperty(indexed = True) #0 - pending creation, 1 - pending approval, 2 - approved
  owners = ndb.KeyProperty(kind=User, repeated=True) #A list of users who has the permission to update this
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)

#Using an Expando model to have sport specific details here.
#TO store the summary information about a match, at team level, or at player level for individual sport
class MatchSummary(ndb.Expando): 
  event_id = ndb.KeyProperty(kind = 'Event')
  match_id = ndb.KeyProperty(kind = 'Match')
  team_id = ndb.KeyProperty(kind = 'Team')
  player_id = ndb.KeyProperty(kind = 'Player')
  
#Using an Expando model to have sport specific details here.
# To store the last detail of information about the match, at every player level
# Expected to have the same fields at match level
class MatchDetail(ndb.Expando): 
  event_id = ndb.KeyProperty(kind = 'Event')
  match_id = ndb.KeyProperty(kind = 'Match')
  team_id = ndb.KeyProperty(kind = 'Team')
  player_id = ndb.KeyProperty(kind = 'Player')
  
  
class Media(ndb.Model):
  business_id = ndb.KeyProperty(kind = 'Business', repeated = False) #Only one of the following four ids are populated for a media
  entity_id = ndb.KeyProperty(repeated = False, indexed = True) 
  entity_type = ndb.StringProperty()
  name = ndb.StringProperty()
  type = ndb.StringProperty(indexed = True)
  link = ndb.BlobKeyProperty()
  url = ndb.StringProperty()
  status = ndb.BooleanProperty() #active and inactive
  primary = ndb.BooleanProperty() #Will be used in all the thumbnails
  
  
#to store the booking related info
class BookingCalender(ndb.Model):
  playground_id = ndb.KeyProperty(kind = 'Playground', repeated = False)
  event_id = ndb.KeyProperty(kind = 'Event', repeated = False) #optional, used if the booking is for a listed event
  description = ndb.TextProperty()
  start_datetime = ndb.DateTimeProperty()
  end_datetime = ndb.DateTimeProperty()
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  
class Post(ndb.Model):
  business_id = ndb.KeyProperty(kind = 'Business', repeated = False) #Only one of the following four ids are populated for a post
  training_centre_id = ndb.KeyProperty(kind = 'TrainingCentre', repeated = False) 
  playground_id = ndb.KeyProperty(kind = 'Playground', repeated = False)
  event_id = ndb.KeyProperty(kind = 'Event', repeated = False)
  title = ndb.StringProperty(indexed = True)
  content = ndb.TextProperty()
  photos = ndb.LocalStructuredProperty(Media, repeated = True)
  videos = ndb.LocalStructuredProperty(Media, repeated = True)
  comment_count = ndb.IntegerProperty()
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  
class Review(ndb.Model):
  business_id = ndb.KeyProperty(kind = 'Business', repeated = False) #Only one of the following four ids are populated for a review
  training_centre_id = ndb.KeyProperty(kind = 'TrainingCentre', repeated = False) 
  playground_id = ndb.KeyProperty(kind = 'Playground', repeated = False)
  event_id = ndb.KeyProperty(kind = 'Event', repeated = False)
  rating = ndb.IntegerProperty(indexed = True)
  review = ndb.TextProperty()
  photos = ndb.LocalStructuredProperty(Media, repeated = True)
  videos = ndb.LocalStructuredProperty(Media, repeated = True)
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)

class Comment(ndb.Model):
  post_id = ndb.KeyProperty(kind = 'Post', repeated = False)
  comment = ndb.TextProperty()
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)

class Locality(ndb.Model):  
  name = ndb.StringProperty(indexed = True)
  ref_id = ndb.StringProperty(indexed = True)
  place_id = ndb.StringProperty(indexed = True)
  latlong = ndb.GeoPtProperty(indexed = True)
  address = ndb.StringProperty(indexed = False)
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)

class Register(ndb.Model):  
  reg_id = ndb.KeyProperty()
  reg_type = ndb.StringProperty(indexed = True)
  team_id = ndb.KeyProperty(kind = 'Team', repeated = True)
  user_id = ndb.KeyProperty(kind=User, repeated = False)
  player_id = ndb.KeyProperty(kind=User, repeated = True)
  booked_date = ndb.DateTimeProperty(indexed = True)
  payment = ndb.IntegerProperty()
  status = ndb.IntegerProperty(indexed = True) #0 - pending creation, 1 - pending approval, 2 - approved  
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)

class ContactPg(ndb.Model):
  person_name = ndb.StringProperty(indexed = False, repeated = True)
  email = ndb.StringProperty(indexed = False, repeated = True)
  phone = ndb.StringProperty(indexed = False, repeated = True)
  website = ndb.StringProperty(indexed = True)

class ContactTc(ndb.Model):
  person_name = ndb.StringProperty(indexed = False, repeated = True)
  email = ndb.StringProperty(indexed = False, repeated = True)
  phone = ndb.StringProperty(indexed = False, repeated = True)
  website = ndb.StringProperty(indexed = True)

class ContactSe(ndb.Model):
  person_name = ndb.StringProperty(indexed = False, repeated = True)
  email = ndb.StringProperty(indexed = False, repeated = True)
  phone = ndb.StringProperty(indexed = False, repeated = True)
  website = ndb.StringProperty(indexed = True)
    
class MasterData(ndb.Model):
  pg_name = ndb.StringProperty(indexed = True)  
  sport = ndb.StringProperty(indexed = True)
  business_id = ndb.KeyProperty(indexed = True, kind = 'Business') #Need to check whether this works as desired for custom created keys
  address = ndb.StructuredProperty(Address, repeated = False)
  contact_pg = ndb.StructuredProperty(ContactPg, repeated = False)
  
  public = ndb.StringProperty()
  booking_days = ndb.StringProperty()
  regular_time = ndb.StringProperty()
  ground_type = ndb.StringProperty()
  surface_type = ndb.StringProperty()
  tot_fields = ndb.IntegerProperty()
  ground_rules = ndb.StringProperty(indexed = True)
  
  tc_name = ndb.StringProperty(indexed = True)
  tc_open_days = ndb.StringProperty()
  age_limit = ndb.StringProperty()
  tc_participants = ndb.IntegerProperty()
  contact_tc = ndb.StructuredProperty(ContactTc, repeated = False)
  
  se_name = ndb.StringProperty(indexed = True)
  start_datetime = ndb.DateTimeProperty(indexed = True)
  end_datetime = ndb.DateTimeProperty(indexed = True)
  contact_se = ndb.StructuredProperty(ContactSe, repeated = False)
  
  created_by = ndb.KeyProperty(kind=User)
  created_on = ndb.DateTimeProperty(auto_now_add = True)
  updated_by = ndb.KeyProperty(kind=User)
  updated_on = ndb.DateTimeProperty(auto_now = True)
