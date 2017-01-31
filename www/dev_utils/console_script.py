from google.appengine.ext import ndb
from models import Event
import constants
import logging
from datetime import datetime

from models import Team, Match
logger = logging.getLogger(__name__)

team1 = Team()
team1.name = 'CSK'
team1.sport = 'cricket'
team1.created_on = datetime.now()
team1_key = team1.put()
print 'team1_key, %s' % team1_key

team2 = Team()
team2.name = 'RCB'
team2.sport = 'cricket'
team2.created_on = datetime.now()
team2_key = team1.put()
print 'team2_key, %s' % team2_key


match = Match()
match.name = 'Match 23'
match.event_id = ndb.Key('Event', 4845650822823936)
match.playground_id = ndb.Key('Playground', 4532977203675136)
match.sport = 'cricket'
match.participants.append(team1_key)
match.participants.append(team2_key)
match.start_datetime = datetime.strptime('2014-05-10', '%Y-%m-%d')
match.end_datetime = datetime.strptime('2014-05-10', '%Y-%m-%d')
match.result = 'CSK Won by 10 runs'
match.summary = 'MOM: Dhoni 75 runs in 35 balls'
match_key = match.put()
print 'match key, %s' % match_key
