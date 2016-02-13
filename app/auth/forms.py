from flask import flash
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import IntegerField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms.validators import NumberRange, Optional
from wtforms import ValidationError
from ..models import User


class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 128),
                                             Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    email = StringField('Email*', validators=[Required(), Length(1, 128),
                                              Email()])
    username = StringField('Username*', validators=[
        Required(), Length(1, 128), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                           'Usernames must have only letters, '
                                           'numbers, dots or underscores')])
    password = PasswordField('Password*', validators=[
        Required(), EqualTo('password2', message='Passwords must match.'),
        Length(8, 128)])
    password2 = PasswordField('Confirm password*', validators=[Required(),
                                                               Length(8, 128)])
    sex = SelectField('Sex',
                      validators=[Optional(True)],
                      choices=[('0', 'unspecified'),
                               ('1', 'female'),
                               ('2', 'male')])
    birth_year = IntegerField('Year of Birth',
                              validators=[Optional(True),
                                          NumberRange(1900, 2015)])
    size = IntegerField('Size (in cm)',
                        validators=[Optional(True), NumberRange(0, 300)])
    weight = IntegerField('Weight (in kg)',
                          validators=[Optional(True), NumberRange(0, 500)])
    accept_privacy_terms = BooleanField('I accept the privacy terms, '
                                        'the exclusion of liability and '
                                        'the processing of my data.*')
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

    def validate_accept_privacy_terms(self, field):
        if not field.data:
            flash('You must accept the privacy terms.')
            raise ValidationError('You must accept the privacy terms.')


class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[Required()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match'),
        Length(8, 128)])
    password2 = PasswordField('Confirm new password',
                              validators=[Required(), Length(8, 128)])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 128),
                        Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 128),
                                             Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match'),
        Length(8, 128)])
    password2 = PasswordField('Confirm password', validators=[Required(),
                                                              Length(8, 128)])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class DeleteAccountForm(Form):
    submit = SubmitField('Yes, delete my account')
