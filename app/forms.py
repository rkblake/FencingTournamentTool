from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms.fields.html5 import DateField
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class CreateTournamentForm(FlaskForm):
    name = StringField('Tournament Name', validators=[DataRequired()])
    #date = DateField('Date', format='%Y-%m-%d')
    submit = SubmitField('Create Tournament')

class CreateEventForm(FlaskForm):
    name = StringField('Event name', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d')
    submit = SubmitField('Create Event')

class AddFencerForm(FlaskForm):
    name = StringField('Fencer name', validators=[DataRequired()])
    rating = StringField('Rating', validators=[DataRequired(), Length(min=3,max=3)])
    submit = SubmitField('Add Fencer')
