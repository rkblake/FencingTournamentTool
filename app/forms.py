from datetime import date as pydate
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, \
                    SubmitField, HiddenField, IntegerField, \
                    SelectField, FormField, widgets, FileField, \
                    TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional, NoneOf
from wtforms.fields.html5 import DateField
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=32, message='Username must be between 4 and 32 characters.')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=32, message='Password must be between 4 and 32 characters.')])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
        if not username.data.isalnum():
            raise ValidationError('Username must be alphanumeric; no special characters allowed.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class CreateTournamentForm(FlaskForm):
    name = StringField('Tournament Name', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Create Tournament')


class CreateEventForm(FlaskForm):
    name = StringField('Event name', validators=[DataRequired(), Length(max=64)])
    choices = [
        ('none', 'Choose a weapon'),
        ('foil', 'Foil'),
        ('epee', 'Epee'),
        ('saber', 'Saber')
    ]
    weapon = SelectField('Weapon', choices=choices, validators=[NoneOf(['none'], message='Please select a Weapon.')])
    date = DateField('Date', format='%Y-%m-%d')
    submit = SubmitField('Create Event')

    def validate_date(self, date):
        present = pydate.today()
        if datetime.strptime(date.data.strftime('%Y-%m-%d'), '%Y-%m-%d').date() < present:
            raise ValidationError('Date cannot be in the past.')


class CreatePoolForm(FlaskForm):
    num_fencers = HiddenField()
    numPools1 = IntegerField(validators=[DataRequired()])
    numFencers1 = IntegerField(validators=[DataRequired()])
    numPools2 = IntegerField(validators=[Optional()], default=0)
    numFencers2 = IntegerField(validators=[Optional()], default=0)
    submit = SubmitField('Create Pool')

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        if self.numFencers1 == 0 or self.numFencers2 == 0:
            return False
        if (abs(self.numFencers1.data - self.numFencers2.data) > 1) and self.numFencers2.data is not 0:
            return False
        if self.numPools1.data * self.numFencers1.data + self.numPools2.data * self.numFencers2.data == int(self.num_fencers.data):
            return True
        else:
            return False
            #raise ValidationError('Pools and fencers must add up to total fencers in event.') #TODO: make this work

class AddTOForm(FlaskForm):
    email = StringField('Organizers Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Add TO')


def validate_name(form, field):
    if field is None:
        return True
    if len(field.data.split()) != 2:
        raise ValidationError('Fencer name must contain first and last name.')
    if not field.data.replace(' ', '').isalpha():
        raise ValidationError('Fencer name must contain only letters.')


class TeamField(FlaskForm):
    fencer_a = StringField('Fencer A', validators=[Optional(), Length(max=64), validate_name])
    fencer_b = StringField('Fencer B', validators=[Optional(), Length(max=64), validate_name])
    fencer_c = StringField('Fencer C', validators=[Optional(), Length(max=64), validate_name])
    fencer_d = StringField('Fencer D (Alt)', validators=[Optional(), Length(max=64), validate_name])


class AddTeamForm(FlaskForm):
    teamName = StringField('Team name', validators=[DataRequired(), Length(max=64)])
    fencer_a = StringField('Fencer A', validators=[DataRequired(), Length(max=64), validate_name])
    fencer_b = StringField('Fencer B', validators=[DataRequired(), Length(max=64), validate_name])
    fencer_c = StringField('Fencer C', validators=[Optional(), Length(max=64), validate_name])
    fencer_d = StringField('Fencer D (Alt)', validators=[Optional(), Length(max=64), validate_name])
    choices = [
        ('none', 'Choose a university'),
        ('Rice', 'Rice'),
        ('St. Thomas', 'St. Thomas'),
        ('TAMU', 'TAMU'),
        ('TAMUCC', 'TAMUCC'),
        ('Texas State', 'Texas State'),
        ('UH', 'UH'),
        ('UNT', 'UNT'),
        ('UTA', 'UTA'),
        ('UTD', 'UTD'),
        ('UTFC', 'UTFC'),
        ('UTSA', 'UTSA')]
    club = SelectField('University', choices=choices, validators=[NoneOf(['none'], message='Please select a university.')])
    submit = SubmitField('Add Team')

    def validate_club(self, club): #TODO: why isnt this being used?
        if club.data is 'none':
            raise ValidationError('Please select a university.')


class PreregisterForm(FlaskForm):
    Foil_A = FormField(TeamField)
    Foil_B = FormField(TeamField)
    Epee_A = FormField(TeamField)
    Epee_B = FormField(TeamField)
    Saber_A = FormField(TeamField)
    Saber_B = FormField(TeamField)
    submit = SubmitField('Preregister')

    def validate(self):
        return True


class EmailListForm(FlaskForm):
    email_json = FileField('JSON Formatted Email List', validators=[DataRequired()], filters=[lambda x : x or None])
    submit = SubmitField('Send Preregistration Emails')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')
