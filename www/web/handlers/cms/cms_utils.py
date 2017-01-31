from google.appengine.ext import ndb
from models import ContactInfo, Address, ContactPg, ContactTc, ContactSe
from web.utils.app_utils import get_latlong_from_address

def form_to_dao_contact_info(form, entity):
  contact_info = form.contact_info.data
  if contact_info is not None:
    entity.contact_info = ContactInfo()
    if len(contact_info['person_name']) > 0:
      entity.contact_info.person_name = [x.strip() for x in contact_info['person_name'].split(',')]
    if len(contact_info['email']) > 0:
      entity.contact_info.email = [x.strip() for x in contact_info['email'].split(',')]
    if len(contact_info['phone']) > 0:
      entity.contact_info.phone = [x.strip() for x in contact_info['phone'].split(',')]
    entity.contact_info.website = contact_info['website']
    entity.contact_info.facebook = contact_info['facebook']
    entity.contact_info.twitter = contact_info['twitter']
    entity.contact_info.youtube = contact_info['youtube']
    entity.contact_info.gplus = contact_info['gplus']
  return entity
  
def dao_to_form_contact_info(entity, form):
  if entity.contact_info is not None:
    if entity.contact_info.person_name is not None and len(entity.contact_info.person_name) > 0:
      form.contact_info.person_name.data = ', '.join(entity.contact_info.person_name)
    if entity.contact_info.email is not None and len(entity.contact_info.email) > 0:
      form.contact_info.email.data = ', '.join(entity.contact_info.email)
    if entity.contact_info.phone is not None and len(entity.contact_info.phone) > 0:
      form.contact_info.phone.data = ', '.join(entity.contact_info.phone)
  return form
  
def form_to_dao_address(form, entity):
  address = form.address.data
  if address is not None:
    entity.address = Address()
    entity.address.line1 = address['line1'].lower()
    entity.address.line2 = address['line2'].lower()
    entity.address.locality = address['locality'].lower()
    entity.address.city = address['city'].lower()
    entity.address.pin = address['pin']
    latitude, longitude = get_latlong_from_address(entity.address)
    if latitude is not None and longitude is not None:
      entity.address.latlong = ndb.GeoPt(latitude,longitude)
    return entity

def dao_to_form_address(entity, form):
  if entity.address is not None and entity.address.latlong is not None:   
    form.address.lat.data = entity.address.latlong.lat
    form.address.long.data = entity.address.latlong.lon
  return form

def dao_to_form_city_info(entity, form):
  if entity.address is not None:
    if entity.address.city is not None:
      form.city.data = entity.address.city
    if entity.address.locality_id is not None:
      form.locality_id.data = entity.address.locality_id
    return form

def dao_to_form_locality_info(entity, form):
  if entity.address is not None:
    if entity.address.locality is not None:
      form.locality.data = entity.address.locality
    if entity.address.locality_id is not None:
      form.locality_id.data = entity.address.locality_id
    if entity.address.city is not None:
      form.city.data = entity.address.city
    return form

def form_to_dao_contact_pg(form, entity):
  contact_pg = form.contact_pg.data
  if contact_pg is not None:
    entity.contact_pg = ContactPg()
    if len(contact_pg['person_name']) > 0:
      entity.contact_pg.person_name = [x.strip() for x in contact_pg['person_name'].split(',')]
    if len(contact_pg['email']) > 0:
      entity.contact_pg.email = [x.strip() for x in contact_pg['email'].split(',')]
    if len(contact_pg['phone']) > 0:
      entity.contact_pg.phone = [x.strip() for x in contact_pg['phone'].split(',')]
    entity.contact_pg.website = contact_pg['website']
  return entity

def form_to_dao_contact_tc(form, entity):
  contact_tc = form.contact_tc.data
  if contact_tc is not None:
    entity.contact_tc = ContactTc()
    if len(contact_tc['person_name']) > 0:
      entity.contact_tc.person_name = [x.strip() for x in contact_tc['person_name'].split(',')]
    if len(contact_tc['email']) > 0:
      entity.contact_tc.email = [x.strip() for x in contact_tc['email'].split(',')]
    if len(contact_tc['phone']) > 0:
      entity.contact_tc.phone = [x.strip() for x in contact_tc['phone'].split(',')]
    entity.contact_tc.website = contact_tc['website']
  return entity
  
def form_to_dao_contact_se(form, entity):
  contact_se = form.contact_se.data
  if contact_se is not None:
    entity.contact_se = ContactSe()
    if len(contact_se['person_name']) > 0:
      entity.contact_se.person_name = [x.strip() for x in contact_se['person_name'].split(',')]
    if len(contact_se['email']) > 0:
      entity.contact_se.email = [x.strip() for x in contact_se['email'].split(',')]
    if len(contact_se['phone']) > 0:
      entity.contact_se.phone = [x.strip() for x in contact_se['phone'].split(',')]
    entity.contact_se.website = contact_se['website']
  return entity
