from app import db, app, login
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

access_table = db.Table('access',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('tournament_id', db.Integer, db.ForeignKey('tournament.id'))
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tournaments = db.relationship(
            "Tournament",
            secondary=access_table,
            backref='user_tournaments')

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
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    organizers = db.relationship(
            "User",
            secondary=access_table,
            backref='tournament_organizers'
    )
    events = db.relationship('Event', backref='tournament', lazy='dynamic')

    def __repr__(self):
        return '<Tournament {}>'.format(self.name)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'))
    pools = db.relationship('Pool', backref='event', lazy='dynamic')
    des = db.relationship('DE', backref='event', lazy='dynamic')

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    fencers = db.relationship('Fencer', backref='club_members')

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    fencers = db.relationship('Fencer', backref='team_members')

class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    results = db.relationship('Result', backref='results', lazy='dynamic')
    fencers = db.relationship('Fencer', backref='fencers', lazy='dynamic')

class DE(db.Model):
    __tablename__ = 'de'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    result_id = db.Column(db.Integer, db.ForeignKey('result.id'))

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'))
    de_id = db.Column(db.Integer, db.ForeignKey('de.id'))
    fencer1 = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    fencer2 = db.Column(db.Integer, db.ForeignKey('fencer.id'))
    fencer1Score = db.Column(db.Integer)
    fencer2Score = db.Column(db.Integer)
    fencer1Win = db.Column(db.Boolean)

class Fencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    isCheckedIn = db.Column(db.Boolean)
    rating = db.Column(db.String(3))
    victories = db.Column(db.Integer)
    defeats = db.Column(db.Integer)
    touchesScored = db.Column(db.Integer)
    touchesRecieved = db.Column(db.Integer)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'))
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
