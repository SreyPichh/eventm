PLAYGROUND = 'playground'
TRAINING_CENTRE = 'trainingcentre'
EVENT = 'event'
PHOTO = 'photo'
VIDEO = 'video'
PROFILE = 'profile'
TEAM = 'team'
SPORT_DICT = {'cricket':'Cricket', 'football':'Football', 'tennis':'Tennis', 'hockey':'Hockey', 'badminton':'Badminton', 'others':'more'}
#Default media to be stored in the below path as jpgs with entity type as folder name and sport type as filename
#ex: for cricket playground, default media will be /assets/img/default_media/playground/cricket.jpg
DEFAULT_MEDIA_PATH = '/assets/img/default_media/'
#Constants for sport specific fields of Expando model
EXPANDO_MATCH = {'cricket':['mom']}
EXPANDO_MATCH_SUMMARY  = {'cricket':['toss_won_by', 'total_runs', 'total_wickets', 'overs']}
EXPANDO_MATCH_DETAIL = {'cricket':['balls_faced', 'runs_taken', 'fours_count', 'six_count', 'minutes', 'overs_bowled', 'runs_conceded', 'wickets', 'maiden_overs', 'catches', 'stumping']}
TYPE_DICT = {'event':'Events', 'playground':'Playgrounds', 'trainingcentre':'Training Centres'}
PLACES_API_KEY = 'AIzaSyBcUqb3ZWh5-_TuHX1lRjZXlqKXfKRIS8k'
GENDER_DICT = {'male':'MALE', 'female':'FEMALE'}
PROFESSION_DICT = {'student':'STUDENT', 'corporate':'CORPORATE'}
CATEGORY_DICT = {'open':'Open for All', 'school':'School Level', 'university':'University Level', 'corporate':'Corporate Level'}
#WANT_DICT = {'train':'Train', 'compete':'Compete in events', 'playing':'Enjoy playing with friends'}
WANT_DICT = {'1':'become a sport professional', '2':'relax with friends / stay fit', '3':'be in touch and compete in local events'}
SPORTS_LIST = {'cricket':'Cricket', 'football':'Football', 'tennis':'Tennis', 'hockey':'Hockey', 'badminton':'Badminton', 'boxing':'Boxing', 'golf':'Golf', 'horse riding':'Horse Riding', 'motor sport':'Motor Sport', 'rowing':'Rowing', 'sailing':'Sailing', 'skating':'Skating', 'squash':'Squash', 'swimming':'Swimming', 'others':'More' }
DAYS_LIST = {'monday':'MONDAY', 'tuesday':'TUESDAY', 'wednesday':'WEDNESDAY', 'thursday':'THURSDAY', 'friday':'FRIDAY', 'saturday':'SATURDAY', 'sunday':'SUNDAY'}
NUM_LIST = {'1':'1-5 Events', '2':'5-10 Events', '3':'Above 10'}
REG_PRICE = 10000
OPEN_DICT = { '0':'Not Now', '1':'Open'}
AGE_DICT = {'1':'0-12', '2':'13-17', '3':'18-29', '4':'30-59', '5':'Above 60'}
REG_TIME = {'1':'6-10 Am', '2':'6-10 Pm', '3':'6 Am to 10 Pm'}
GROUND_TYPE = {'indoor':'Indoor', 'outdoor':'Outdoor', 'both':'Both'}
SURFACE_TYPE = {'oval':'Oval', 'circle':'Circle', 'square':'Square'}