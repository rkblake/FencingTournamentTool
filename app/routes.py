from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    return "hello"

@app.route('/login')
def login():
    return "login"

@app.route('/signup')
def signup():
    return "signup"

@app.route('/user/<username>')
def user(username):
    return "user"

@app.route('/<int:tournament_id>')
def tournament(tournament_id):
    return "tournament"

@app.route('/explore')
def explore():
    return "explore"

@app.route('/create-tournament')
def createTournament():
    return "create tournament"

@app.route('/<int:tournament_id>/event/<int:event_id>/registration')
def registration(tournament_id, event_id):
    return "registration"

@app.route('/<int:tournament_id>/event/<int:event_id>/pool')
def pool(tournament_id, event_id):
    return "pool"

@app.route('/<int:tournament_id>/event/<int:event_id>/de')
def de(tournament_id, event_id):
    return "de"

@app.route('/<int:tournament_id>/event/<int:event_id>/final')
def final(tournament_id, event_id):
    return "final"

@app.route('/<int:tournament_id>/event/<int:event_id>/registration/edit')
def editRegistration(tournament_id, event_id):
    return render_template('edit-registration.html')

@app.route('/<int:tournament_id>/event/<int:event_id>/pool/<int:pool_id>/edit')
def editPool(tournament_id, event_id, pool_id):
    return render_template('edit-pool.html')

@app.route('/<int:tournament_id>/event/<int:event_id>/de/edit')
def editDE(tournament_id, event_id):
    return render_template('edit-de.html')
