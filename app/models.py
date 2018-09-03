from app import db, app, login
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
import jwt
from enum import Enum

class Stage(Enum):
    PREREGISTRATION = 0
    REGISTRATION_OPEN = 1
    REGISTRATION_CLOSE = 2
    POOLS = 3
    POOLS_DONE = 4
    DES = 5
    DONE = 6

Base = declarative_base()

class AccessTable(db.Model):
    __tablename__ = 'access_table'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    main_to = db.Column(db.Boolean, default=False)

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

    def get_reset_pasword_token(self, expires_in=1800):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Tournament(db.Model):
    __tablename__ = 'tournament'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    format = db.Column(db.String())
    organizers = db.relationship('AccessTable', backref='tournament')
    events = db.relationship('Event', backref='tournament', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Tournament {}>'.format(self.name)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    date = db.Column(db.Date, index=True)
    stage = db.Column(db.Integer, default=0) #0 = prereg, 1 = reg open, 2 = reg closed, 3 = pools, 4 = pools finished, 5 = des, 6 = done
    num_fencers = db.Column(db.Integer, default=0)
    num_fencers_checked_in = db.Column(db.Integer, default=0)
    tableau_json = db.Column(db.String)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    weapon = db.Column(db.String(5))
    pools = db.relationship('Pool', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    des = db.relationship('DE', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    fencers = db.relationship('Fencer', backref='event', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Event {}>'.format(self.name)

    def advance_stage(self, next_stage):
        self.stage = next_stage.value if next_stage.value > self.stage else self.stage

class Club(db.Model): #also university
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    fencers = db.relationship('Fencer', backref='club', cascade='all, delete-orphan')
    teams = db.relationship('Team', backref='club', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Club {}>'.format(self.name)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    fencers = db.relationship('Fencer', backref='team_members', lazy='dynamic', cascade='all, delete-orphan')
    is_checked_in = db.Column(db.Boolean)
    num_in_pool = db.Column(db.Integer)
    victories = db.Column(db.Integer, default=0)
    touches_scored = db.Column(db.Integer, default=0)
    touches_recieved = db.Column(db.Integer, default=0)
    indicator = db.Column(db.Integer, default=0)
    round_eliminated_in = db.Column(db.Integer, default=None, nullable=True)
    final_place = db.Column(db.Integer, default=None, nullable=True)
    event_id = db.Column('Event', db.ForeignKey('event.id'))
    event = db.relationship('Event', backref=db.backref('teams', lazy='dynamic', cascade='all, delete-orphan'), foreign_keys=[event_id])
    pool_id = db.Column('Pool', db.ForeignKey('pool.id'))
    pool = db.relationship('Pool', backref=db.backref('teams', lazy='dynamic', cascade='all, delete-orphan'), foreign_keys=[pool_id])
    club_id = db.Column('Club', db.ForeignKey('club.id'))

    def __repr__(self):
        return '<Team {}>'.format(self.name)


class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poolNum = db.Column(db.Integer)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    num_fencers = db.Column(db.Integer)
    state = db.Column(db.Integer, default=0)  # 0 = pools not finished, 1 = pools finished
    pool_letter = db.Column(db.String(1))
    results = db.relationship('Result', backref='results', lazy='dynamic', cascade='all, delete-orphan')
    fencers = db.relationship('Fencer', backref='fencers', lazy='dynamic', cascade='all, delete-orphan')
    #teams = db.relationship('Team', backref='teams', lazy='dynamic')

    def __repr__(self):
        return '<Pool {}, {} fencers>'.format(self.poolNum, self.num_fencers)

class DE(db.Model):
    __tablename__ = 'de'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Integer)  # 0 = not started, 1 = in progress, 2 = finished, 3 = bye, 4 = tbd
    is_third = db.Column(db.Boolean, default=False)
    round = db.Column(db.Integer, default=None, nullable=True)
    fencer1_id = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    fencer1 = db.relationship('Fencer', foreign_keys=[fencer1_id])
    fencer2_id = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    fencer2 = db.relationship('Fencer', foreign_keys=[fencer2_id])
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), default=None)
    team1 = db.relationship('Team', foreign_keys=[team1_id])
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), default=None)
    team2 = db.relationship('Team', foreign_keys=[team2_id])
    fencer1_score = db.Column(db.Integer)
    fencer2_score = db.Column(db.Integer)
    fencer1_win = db.Column(db.Boolean)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))

    def __repr__(self):
        return '<DE {} {} vs {}>'.format(self.id, self.fencer1, self.fencer2)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'))
    de_id = db.Column(db.Integer, db.ForeignKey('de.id'))
    de = db.relationship('DE', foreign_keys=[de_id])
    fencer = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    opponent = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    opponent_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', foreign_keys=[team_id])
    opponent_team = db.relationship('Team', foreign_keys=[opponent_team_id])
    fencer_score = db.Column(db.Integer)
    fencer_win = db.Column(db.Boolean)

class Fencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(32), index=True)
    last_name = db.Column(db.String(32), index=True)
    is_checked_in = db.Column(db.Boolean)
    num_in_pool = db.Column(db.Integer)
    victories = db.Column(db.Integer, default=0)
    touches_scored = db.Column(db.Integer, default=0)
    touches_recieved = db.Column(db.Integer, default=0)
    indicator = db.Column(db.Integer, default=0)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'))
    pool = db.relationship('Pool', backref='pool')
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', backref='team', foreign_keys=[team_id])
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    team_position = db.Column(db.String(1))

    def __repr__(self):
        return '<Fencer {}, {} Num {}>'.format(self.last_name, self.first_name, self.num_in_pool)
