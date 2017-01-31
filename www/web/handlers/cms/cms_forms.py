from wtforms import fields
from wtforms import Form
from wtforms import validators
from web.lib import utils
import constants

FIELD_MAXLENGTH = 200 # intended to stop maliciously long input
NAME_FILED_MAXLENGTH = 50
STRING_FIELD_SIZE = 100

class BaseForm(Form):
  def __init__(self, request_handler, obj=None):
    super(BaseForm, self).__init__(request_handler.request.POST, obj=obj)


class Address(Form):
  line1 = fields.StringField(('Line 1'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  line2 = fields.StringField(('Line 2'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  locality = fields.StringField(('Area/Locality*'), [validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  city = fields.StringField(('City*'), [validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  pin = fields.IntegerField(('Pincode'), [validators.Optional()])

class EventAddress(Form):
  line1 = fields.StringField(('Line 1'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  line2 = fields.StringField(('Line 2'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  locality = fields.StringField(('Area/Locality'), [validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  city = fields.StringField(('City*'), [validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  pin = fields.IntegerField(('Pincode'), [validators.Optional()])
  
class ContactInfo(Form):
  person_name = fields.StringField(('Contact Person'), [validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  email = fields.StringField(('Email'), [validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  phone = fields.StringField(('Phone number'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  website = fields.StringField(('Website'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  facebook = fields.StringField(('Facebook'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  twitter = fields.StringField(('Twitter'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  youtube = fields.StringField(('Youtube'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  gplus = fields.StringField(('GPlus'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
class CustomInfo(Form):
  name = fields.StringField(('Field Name'), [validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  value = fields.TextAreaField(('Content'))

class MediaForm(Form):
  name = fields.StringField('Name')
  media = fields.FileField('Photo/Video')
  status = fields.BooleanField('Active/Inactive')
  primary = fields.BooleanField('Is Primary')  

class BusinessForm(BaseForm):
  name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  description = fields.TextAreaField('Description')
  logo = fields.FileField('Logo')
  contact_info = fields.FormField(ContactInfo)
  pass

class PlaygroundForm(BaseForm):
  name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  sport = fields.SelectField(u'Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='others')
  locality = fields.StringField(('Area/Locality'), [validators.Required(), validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  city = fields.StringField(('City'), [validators.Required(), validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  description = fields.TextAreaField('Description')
  featured = fields.BooleanField('Featured')  
  media = fields.FieldList(fields.FormField(MediaForm), min_entries=1)
  address = fields.FormField(Address)
  contact_info = fields.FormField(ContactInfo)
  locality_id = fields.HiddenField()
  #custom_info = fields.FieldList(fields.FormField(CustomInfo), min_entries=2)
  pass

class TrainingCentreForm(BaseForm):
  name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  sport = fields.SelectField(u'Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='others')
  locality = fields.StringField(('Area/Locality'), [validators.Required(), validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  city = fields.StringField(('City'), [validators.Required(), validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  description = fields.TextAreaField('Description')
  featured = fields.BooleanField('Featured')
  media = fields.FieldList(fields.FormField(MediaForm), min_entries=1)
  business_id = fields.HiddenField()
  address = fields.FormField(Address)
  contact_info = fields.FormField(ContactInfo)
  locality_id = fields.HiddenField()
  #custom_info = fields.FieldList(fields.FormField(CustomInfo), min_entries=2)
  pass

class EventForm(BaseForm):
  name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  sport = fields.SelectField(u'Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='others')
  caption = fields.TextAreaField('Caption')
  city = fields.StringField(('City'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  description = fields.TextAreaField('Description')
  featured = fields.BooleanField('Featured')
  media = fields.FieldList(fields.FormField(MediaForm), min_entries=1)
  business_id = fields.HiddenField()
  start_datetime = fields.DateField('Start Date', [validators.Required()])
  end_datetime = fields.DateField('End Date', [validators.Required()])
  address = fields.FormField(EventAddress)
  contact_info = fields.FormField(ContactInfo)
  locality_id = fields.HiddenField()
  #custom_info = fields.FieldList(fields.FormField(CustomInfo), min_entries=2)  
  pass
  
class ChildEventForm(BaseForm):
  name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  description = fields.TextAreaField('Description')
  
  media = fields.FieldList(fields.FormField(MediaForm), min_entries=5)
  parent_event_id = fields.HiddenField()
  start_datetime = fields.DateTimeField('Start Date Time', [validators.Required()])
  end_datetime = fields.DateTimeField('End Date Time', [validators.Required()])
  contact_info = fields.FormField(ContactInfo)
  custom_info = fields.FieldList(fields.FormField(CustomInfo), min_entries=2)  
  pass

class ImportForm(BaseForm):
  linenum = fields.IntegerField(('Line Number'), [validators.Required()])
  importfile = fields.FileField(('Excel/CSV'))
  pass

class TeamDetails(Form):
  team = fields.SelectField(u'Group', coerce=int)
    
def edit_user(request, id):
  teamDao = DaoFactory.create_rw_teamDao()
  user = self.teamDao.get_teams_for_user(self.user_info)
  form = TeamDetails(request.POST, obj=user)
  form.team.choices = [(key, value) for key, value in user]
  
class MatchForm(BaseForm):
  importfile = fields.FileField(('Excel/CSV'))
  name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  sport = fields.SelectField(u'Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='others')  
  event_id = fields.HiddenField()
  start_datetime = fields.DateTimeField('Start Date Time', [validators.Required()])
  end_datetime = fields.DateTimeField('End Date Time', [validators.Required()])
  result = fields.TextAreaField('Result')
  summary = fields.TextAreaField('Summary')
  participant_type = fields.SelectField('Participant Type', [validators.Required()], choices=[('team','Teams'),('player','Players')])
  #participants = fields.FieldList(fields.FormField(TeamDetails))
  pass

class PlayerForm(Form):
  name = fields.StringField('Player Name')
  email = fields.StringField('Player Email')
  #phone = fields.StringField('Player Phone')
     
class TeamForm(BaseForm):
  importfile = fields.FileField(('Excel/CSV'))
  name = fields.StringField(('Team Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  sport = fields.SelectField(u'Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='others')
  logo = fields.FileField('Logo')
  category = fields.SelectField(u'Category', choices=[(key, value) for key, value in constants.CATEGORY_DICT.items()], default='open')  
  new_player = fields.FieldList(fields.FormField(PlayerForm), min_entries=1)  
  #players = fields.FieldList(fields.FormField(MyForm))  
  pass

class NewPlayerForm(BaseForm):
  importfile = fields.FileField(('Excel/CSV'))
  name = fields.StringField(('Player Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  email = fields.StringField(('Player Email'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  phone = fields.StringField(('Player Phone'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  sport = fields.SelectField(u'Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='others')
  teamName = fields.StringField(('Team Name'), [validators.Optional()])
  pass

class ImportTeamForm(BaseForm):
  importfile = fields.FileField(('Excel/CSV'))
  pass

class SaveLocalityForm(BaseForm):  
  lat = fields.StringField(('Latitude'), [validators.Required(message=('Latitude is not empty'))])
  long = fields.StringField(('Longitude'), [validators.Required(message=('Longitude is not empty'))])
  radius = fields.IntegerField(('Radius'), [validators.Required()])
  limit = fields.IntegerField(('Limit'), [validators.Required()])
  key = fields.StringField(('Api Key'), [validators.Required(message=('Api Key is not empty'))])
  pass

class UserProfileForm(BaseForm):
  name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])  
  email = fields.StringField(('Email'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  image = fields.FileField('Image')
  dob = fields.DateField('Date of Birth', [validators.Required()])
  gender = fields.SelectField(u'Gender', choices=[(key, value) for key, value in constants.GENDER_DICT.items()], default='male')  
  profession = fields.SelectField(u'Profession', choices=[(key, value) for key, value in constants.PROFESSION_DICT.items()], default='')
  phone = fields.StringField(('Phone'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])  
  locality = fields.StringField(('Area/Locality'), [validators.Length(max=NAME_FILED_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  locality_id = fields.HiddenField()
  i_want = fields.SelectField(u'I want to', choices=[(key, value) for key, value in constants.WANT_DICT.items()], default='train')
  sport = fields.SelectField(u'Favorite Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='cricket')
  #sport = fields.StringField(('Favorite Sport'), [validators.Optional()])
  pass

class InviteForm(BaseForm):
  email_list = fields.TextAreaField(("Friend's Email"),[validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  pass
  
class BasicContact(Form):
  person_name = fields.StringField(('Contact Person'), [validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  email = fields.StringField(('Email'), [validators.Length(max=FIELD_MAXLENGTH*2, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  phone = fields.StringField(('Phone number'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  website = fields.StringField(('Website'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
class MasterDataForm(BaseForm):
  pg_name = fields.StringField(('Name'), [validators.Required(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  sport = fields.SelectField(u'Sport', choices=[(key, value) for key, value in constants.SPORTS_LIST.items()], default='others')
  locality_id = fields.HiddenField()
  business_id = fields.HiddenField()
    
  address = fields.FormField(Address)
  contact_pg = fields.FormField(BasicContact)
  
  public = fields.SelectField(u'Open for Public?', choices=[(key, value) for key, value in constants.OPEN_DICT.items()], default=0)
  booking_days = fields.SelectField(u'Public Booking Day(s)', choices=[(key, value) for key, value in constants.DAYS_LIST.items()], default='sunday')
  regular_time = fields.StringField('Regular Timings')
  ground_type = fields.SelectField(u'Ground Type', choices=[(key, value) for key, value in constants.GROUND_TYPE.items()], default='both')
  surface_type = fields.StringField('Types of Surfaces')
  tot_fields = fields.IntegerField(('No.of Courts'), [validators.Optional()])
  ground_rules = fields.TextAreaField('Ground Rules')
  
  tc_name = fields.StringField(('Club Name'), [validators.Optional(), validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  tc_open_days = fields.SelectField(u'Club Open Day(s)', choices=[(key, value) for key, value in constants.DAYS_LIST.items()], default='sunday')
  age_limit = fields.StringField('Age Limits')
  tc_participants = fields.IntegerField(('No.of Participants'), [validators.Optional()])
  contact_tc = fields.FormField(BasicContact)
  
  se_name = fields.StringField(('Event Name'), [validators.Length(max=FIELD_MAXLENGTH, message=(
                                                  "Field cannot be longer than %(max)d characters."))])
  start_datetime = fields.DateField(('Start Date'), [validators.Optional()])
  end_datetime = fields.DateField(('End Date'), [validators.Optional()])
  contact_se = fields.FormField(BasicContact) 
  pass
  