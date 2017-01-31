"""
Created on June 10, 2012
@author: peta15
"""

from wtforms import fields
from wtforms import Form
from wtforms import validators
from web.lib import utils

FIELD_MAXLENGTH = 50 # intended to stop maliciously long input

class BaseForm(Form):
    def __init__(self, request_handler):
        super(BaseForm, self).__init__(request_handler.request.POST)

# ==== Mixins ====
class PasswordConfirmMixin(BaseForm):
    password = fields.TextField(('Password'), [validators.Required(),
                                                validators.Length(max=FIELD_MAXLENGTH, message=(
                                                    "Field cannot be longer than %(max)d characters."))])
    c_password = fields.TextField(('Confirm Password'),
                                  [validators.Required(), validators.EqualTo('password', ('Passwords must match.')),
                                   validators.Length(max=FIELD_MAXLENGTH,
                                                     message=("Field cannot be longer than %(max)d characters."))])

class NameMixin(BaseForm):
    name = fields.TextField(('Name'), [
        validators.Length(max=FIELD_MAXLENGTH, message=("Field cannot be longer than %(max)d characters.")),
        validators.regexp(utils.NAME_LASTNAME_REGEXP, message=(
            "Name invalid. Use only letters and numbers."))])
    last_name = fields.TextField(('Last Name'), [
        validators.Length(max=FIELD_MAXLENGTH, message=("Field cannot be longer than %(max)d characters.")),
        validators.regexp(utils.NAME_LASTNAME_REGEXP, message=(
            "Last Name invalid. Use only letters and numbers."))])


class EmailMixin(BaseForm):
    email = fields.TextField(('Email'), [validators.Required(),
                                          validators.Length(min=8, max=FIELD_MAXLENGTH, message=(
                                                    "Field must be between %(min)d and %(max)d characters long.")),
                                          validators.regexp(utils.EMAIL_REGEXP, message=('Invalid email address.'))])


# ==== Forms ====
class PasswordResetCompleteForm(PasswordConfirmMixin):
    pass


class LoginForm(EmailMixin):
    password = fields.TextField(('Password'), [validators.Required(),
                                                validators.Length(max=FIELD_MAXLENGTH, message=(
                                                    "Field cannot be longer than %(max)d characters."))],
                                id='l_password')
    pass


class RegisterForm(PasswordConfirmMixin, NameMixin, EmailMixin):
    pass


class EditProfileForm(NameMixin, EmailMixin):
    pass


class EditPasswordForm(PasswordConfirmMixin):
    current_password = fields.TextField(('Password'), [validators.Required(),
                                                        validators.Length(max=FIELD_MAXLENGTH, message=(
                                                            "Field cannot be longer than %(max)d characters."))])
    pass


class EditEmailForm(BaseForm):
    new_email = fields.TextField(('Email'), [validators.Required(),
                                              validators.Length(min=8, max=FIELD_MAXLENGTH, message=(
                                                    "Field must be between %(min)d and %(max)d characters long.")),
                                              validators.regexp(utils.EMAIL_REGEXP,
                                                                message=('Invalid email address.'))])
    password = fields.TextField(('Password'), [validators.Required(),
                                                validators.Length(max=FIELD_MAXLENGTH, message=(
                                                    "Field cannot be longer than %(max)d characters."))])
    pass
