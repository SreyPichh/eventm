import time
import urllib
import json

from datetime import datetime
import constants
from settings import GOOGLE_GEOENCODE_API_KEY, DEFAULT_CITY, STATIC_CACHE_EXPIRATION
import logging
from google.appengine.ext import ndb

logger = logging.getLogger(__name__)
googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'

def encode_complex(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%dT%H:%M:%S')
    elif isinstance(obj, ndb.Model):
        return obj.to_dict()
    elif isinstance(obj, object):
        try:
            return obj.__dict__
        except:
            #logger.warn('Unable to decipher %s ' % type(obj))
            return dict()
    else:
        raise TypeError(repr(obj) + " is not JSON serializable")


def split_to_chunks(data, chunk_size=95):
    chunks=[data[x:x+chunk_size] for x in xrange(0, len(data), chunk_size)]
    return chunks

def normalize_sport_name(sport):
  sport = sport.strip().lower()
  if sport not in constants.SPORT_DICT.keys():
    sport = 'others'
  return sport
  
def get_default_media(type, sport='others'):
  return constants.DEFAULT_MEDIA_PATH + type + '/' + normalize_sport_name(sport) + '.jpg'

def round_to_date(datetime):
  date_str = datetime.now().date().strftime('%Y%m%d')
  return datetime.strptime(date_str, '%Y%m%d')
  
#Uses the google geocode api to get the latlong 
def get_latlong_from_address(address, from_sensor=False):
  address_str = ''
  if address.line1 != '':
    address_str += address.line1
  if address.line2 != '':
    address_str += ',' + address.line2
  if address.locality != '':
    address_str += ',' + address.locality
  if address.city != '':
    address_str += ',' + address.city
  address_str = address_str.strip(',')
  logger.debug('Complete address str,  %s ' % address_str)
  
  address_str = address_str.encode('utf-8')
  params = {
    'address': address_str,
    'sensor': "true" if from_sensor else "false"
  }
  url = googleGeocodeUrl + urllib.urlencode(params)
  json_response = urllib.urlopen(url)
  response = json.loads(json_response.read())
  if response['results']:
    location = response['results'][0]['geometry']['location']
    latitude, longitude = location['lat'], location['lng']
    logger.debug('Address: %s, Lat %s, Long %s ' % (address_str, latitude, longitude))
  else:
    latitude, longitude = None, None
    logger.debug('Address: %s, LatLong not found ' % (address_str))
  time.sleep(1) # Slowing down to control the number of requests to google geoencode api every minute. Recheck with API Key later
  return latitude, longitude
  
#Gets the default city from settings now. To be used in all handlers.
#TODO: Get the city based on the user's IP or from his preferences, if he is logged in. Else, fallback to settings value
def get_default_city():
  return DEFAULT_CITY   

def get_event_state(event):
  now = round_to_date(datetime.now())
  if now > event.end_datetime:
    return 'past'
  elif now < event.start_datetime:
    return 'future'
  else:
    return 'present'
  
if  __name__ =='__main__':
  get_latlong_from_address(',, phnom-penh')
