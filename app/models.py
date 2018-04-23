from app import db, app, login
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import column_property
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class AccessTable(db.Model):
    __tablename__ = 'access_table'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    mainTO = db.Column(db.Boolean, default=False)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    '''tournaments = db.relationship(
            "Tournament",
            secondary=AccessTable,
            backref='user_tournaments',
            lazy='dynamic')'''
    tournaments = db.relationship('AccessTable', backref='user')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Tournament(db.Model):
    __tablename__ = 'tournament'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    format = db.Column(db.String())
    organizers = db.relationship('AccessTable', backref='tournament')
    events = db.relationship('Event', backref='tournament', lazy='dynamic')

    def __repr__(self):
        return '<Tournament {}>'.format(self.name)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    date = db.Column(db.Date, index=True)
    stage = db.Column(db.Integer, default=0) #0 = prereg, 1 = reg open, 2 = reg closed, 3 = pools, 4 = pools finished, 5 = des, 6 = done
    numFencers = db.Column(db.Integer, default=0)
    numFencersCheckedIn = db.Column(db.Integer, default=0)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    #tournament = db.relationship('Tournament', foreign_keys=[tournament_id])
    pools = db.relationship('Pool', backref='event', lazy='dynamic')
    des = db.relationship('DE', backref='event', lazy='dynamic')
    fencers = db.relationship('Fencer', backref='event', lazy='dynamic')
    teams = db.relationship('Team', backref='event', lazy='dynamic')

    def __repr__(self):
        return '<Event {}>'.format(self.name)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    fencers = db.relationship('Fencer', backref='club')
    teams = db.relationship('Team', backref='club', lazy='dynamic')

    def __repr__(self):
        return '<Club {}>'.format(self.name)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    fencers = db.relationship('Fencer', backref='team_members')
    isCheckedIn = db.Column(db.Boolean)
    event_id = db.Column('Event', db.ForeignKey('event.id'))
    #event = db.relationship('Event', foreign_keys=[event_id])
    club_id = db.Column('Club', db.ForeignKey('club.id'))
    #club = db.relationship('Club', foreign_keys=[club_id])
    '''
    fencerA_id = db.Column('Fencer', db.ForeignKey('fencer.id'))
    fencerA = db.relationship('Fencer', foreign_keys=[fencerA_id])
    fencerB_id = db.Column('Fencer', db.ForeignKey('fencer.id'))
    fencerB = db.relationship('Fencer', foreign_keys=[fencerB_id])
    fencerC_id = db.Column('Fencer', db.ForeignKey('fencer.id'))
    fencerC = db.relationship('Fencer', foreign_keys=[fencerC_id])
    fencerD_id = db.Column('Fencer', db.ForeignKey('fencer.id'))
    fencerD = db.relationship('Fencer', foreign_keys=[fencerD_id])
    '''

    def __repr__(self):
        return '<Event {}>'.format(self.name)

class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poolNum = db.Column(db.Integer)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    numFencers = db.Column(db.Integer)
    state = db.Column(db.Integer, default=0) #0 = pools not finished, 1 = pools finished
    results = db.relationship('Result', backref='results', lazy='dynamic')
    fencers = db.relationship('Fencer', backref='fencers', lazy='dynamic')

    def __repr__(self):
        return '<Pool {}, {} fencers>'.format(self.poolNum, self.numFencers)

class DE(db.Model):
    __tablename__ = 'de'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'))
    result = db.relationship('Result', foreign_keys=[result_id])

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'))
    de_id = db.Column(db.Integer, db.ForeignKey('de.id'))
    fencer = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    opponent = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    fencerScore = db.Column(db.Integer)
    fencerWin = db.Column(db.Boolean)

class Fencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(64), index=True)
    lastName = db.Column(db.String(63), index=True)
    isCheckedIn = db.Column(db.Boolean)
    numInPool = db.Column(db.Integer)
    ratingClass = db.Column(db.String(1))
    ratingYear = db.Column(db.Integer)
    victories = db.Column(db.Integer, default=0)
    #defeats = db.Column(db.Integer, )
    touchesScored = db.Column(db.Integer, default=0)
    touchesRecieved = db.Column(db.Integer, default=0)
    indicator = db.Column(db.Integer, default=0)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'))
    pool = db.relationship('Pool', backref='pool')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))
    #club = db.relationship('Club', foreign_keys=[club_id])
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    #team = db.relationship('Team', backref='team')
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    teamPosition = db.Column(db.String(1))

    def __repr__(self):
        return '<Fencer {}, {} Num {}>'.format(self.lastName, self.firstName, self.numInPool)
