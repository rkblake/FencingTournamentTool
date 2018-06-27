from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from wtforms.fields.html5 import DateField
from app.models import User, Event

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
    choices = [("USFA Individual", "USFA Individual"), ("USFA Team", "USFA Team"), ("SWIFA", "SWIFA")]
    format = SelectField('Format', choices=choices)
    submit = SubmitField('Create Tournament')

class CreateEventForm(FlaskForm):
    name = StringField('Event name', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d')
    submit = SubmitField('Create Event')

#TODO: don't allow same name fencers, ask for nickname after firstname in paren
class AddFencerForm(FlaskForm):
    firstName = StringField('Fencer first name', validators=[DataRequired()])
    lastName = StringField('Fencer last name', validators=[DataRequired()])
    club = StringField('Club', validators=[Optional()], filters=[lambda x : x or None])
    rating = StringField('Rating', validators=[DataRequired(), Length(min=1,max=3)])
    checked_in = BooleanField('Checked In')
    submit = SubmitField('Add Fencer')

    def validate_rating(self, rating):
        if rating.data.upper() == 'U' or rating.data.upper() == 'U18':
            return True
        if rating.data[0].upper() not in ['A', 'B', 'C', 'D', 'E']:
            raise ValidationError('Not a valid rating')
        if int(rating.data[1:]) < 14 or int(rating.data[1:]) > 18:
            raise ValidationError('Not a valid rating')

class CreatePoolForm(FlaskForm):
    numFencers = HiddenField()
    numPools1 = IntegerField(validators=[DataRequired()])
    numFencers1 = IntegerField(validators=[DataRequired()])
    numPools2 = IntegerField(validators=[Optional()], default=0)
    numFencers2 = IntegerField(validators=[Optional()], default=0)
    submit = SubmitField('Create Pool')

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        if self.numPools1.data * self.numFencers1.data + self.numPools2.data * self.numFencers2.data == int(self.numFencers.data):
            return True
        else:
            return False
            #raise ValidationError('Pools and fencers must add up to total fencers in event.')

class AddTOForm(FlaskForm):
    email = StringField('Organizers Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Add TO')

class AddTeamForm(FlaskForm):
    teamName = StringField('Team name', validators=[DataRequired()])
    fencerA = StringField('Fencer A', validators=[DataRequired()])
    fencerB = StringField('Fencer B', validators=[DataRequired()])
    fencerC = StringField('Fencer C', validators=[Optional()])
    fencerD = StringField('Fencer D (Alt)', validators=[Optional()])
    choices = [('Rice', 'Rice'), ('St. Thomas', 'St. Thomas'), ('TAMU', 'TAMU'),
        ('TAMUCC', 'TAMUCC'), ('TXST', 'TXST'), ('UH', 'UH'), ('UNT', 'UNT'), ('UTA', 'UTA'),
        ('UTD', 'UTD'), ('UT', 'UT'), ('UTSA', 'UTSA')]
    club = SelectField('University', choices=choices)
    #club = StringField('Club/University', validators=[DataRequired()])
    #checked_in = BooleanField('Checked In')
    submit = SubmitField('Add Team')

'''
class EditPoolForm(FlaskForm):
    def __init__(self, numFencers):
        super().__init__()
        self.numFencers = numFencers
        self.field = [['' for _ in range(numFencers)] for _ in range(numFencers)]
        for i in range(0, numFencers):
            for j in range(0, numFencers):
                if i == j:
                    continue
                self.field[i][j] = StringField(validators=[DataRequired()])
        self.submit = SubmitField('Submit pool results')

    def validate(self):
        for i in range(0, int(self.numFencers.data)):
            for j in range(0, int(self.numFencers.data)):
                if i == j:
                    continue
                if not (field[i][j].data[0].upper() is 'V' and field[i][j].data[0].upper() is 'D' or field[j][i].data[0].upper() is 'V' and field[j][i].data[0].upper() is 'D'):
                    return False
        return True
'''
