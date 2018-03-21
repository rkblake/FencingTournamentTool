from flask import render_template
from flask_login import login_user, logout_user, current_user, login_required
from app import app
from app.forms import LoginForm, RegistrationForm

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login')
def login():
    form = LoginForm()
    return render_template('login.html', title='Log In', form=form)

@app.route('/logout')
@login_required
def logout():
    lougout_user()
    return redirect(url_for('main.index'))

@app.route('/signup')
def signup():
    form = RegistrationForm()
    return render_template('signup.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    tournaments = user.tournaments.order_by(Post.date.desc())
    return render_template('user.html', user=user, tournaments=tournaments)

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
