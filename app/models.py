from app import db

access_table = Table('association', db.Base.metadata,
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('tournament_id', db.Integer, db.ForeignKey('tournament.id'))
)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tournaments = db.relationship(
            "Tournament",
            secondary=access_table,
            back_populates="organizers"
    )

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Tournament(db.Model):
    __tablename__ = 'tournament'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    organizers = db.relationship(
            "User",
            secondary=access_table,
            back_populates=tournaments
    )

    def __repr__(self):
        return '<Tournament {}>'.format(self.name)
