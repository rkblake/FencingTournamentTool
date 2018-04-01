from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateTournamentForm, CreateEventForm
from app.models import User, Tournament, Event
from datetime import datetime

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Log In', form=form)

@app.route('/logout')
@login_required
def logout():
    lougout_user()
    return redirect(url_for('main.index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You are now a registered user.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    #tournaments = user.tournaments.order_by(Tournament.date.desc())
    tournaments = user.tournaments
    return render_template('user.html', user=user, tournaments=tournaments)

@app.route('/<int:tournament_id>')
def tournament(tournament_id):
    return "tournament"

@app.route('/explore')
def explore():
    tournaments = Tournament.query.all()
    return render_template('explore.html', tournaments=tournaments)

@app.route('/create-tournament', methods=['GET', 'POST'])
@login_required
def createTournament():
    user = User.query.filter_by(username=current_user.username).first()
    form = CreateTournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(name=form.name.data)
        user.tournaments.append(tournament)
        #query_access = User.query.join(access_table).join('Access').filter(access_table.c.isMainTO
        db.session.add(tournament)
        db.session.commit()
        flash('Created new tournament')
        return redirect(url_for('editTournament', tournament_id=tournament.id))
    return render_template('create-tournament.html', title='Create Tournament', form=form)

@app.route('/<int:tournament_id>/create-event', methods=['GET', 'POST'])
@login_required
def createEvent(tournament_id):
    user = User.query.filter_by(username=current_user.username).first()
    tournament = Tournament.query.filter_by(id=tournament_id).first()
    form = CreateEventForm()
    if form.validate_on_submit():
        event = Event(
                name=form.name.data,
                date=datetime.strptime(form.date.data.strftime('%m/%d/%Y'), '%m/%d/%Y'),
                tournament=tournament)
        tournament.events.append(event)
        db.session.add(event)
        db.session.commit()
        flash('Created new event')
        return redirect(url_for('editTournament', tournament_id=tournament_id))
    return render_template('create-event.html', tournament=tournament, form=form)

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

@app.route('/<int:tournament_id>/edit')
@login_required
def editTournament(tournament_id):
    '''create events and add TOs here'''
    tournament = Tournament.query.filter_by(id=tournament_id).first()
    events = tournament.events
    return render_template('edit-tournament.html', title='Edit Tournament', tournament=tournament, events=events)

@app.route('/<int:tournament_id>/event/<int:event_id>/registration/edit')
@login_required
def editRegistration(tournament_id, event_id):
    return render_template('edit-registration.html')

@app.route('/<int:tournament_id>/event/<int:event_id>/pool/<int:pool_id>/edit')
@login_required
def editPool(tournament_id, event_id, pool_id):
    return render_template('edit-pool.html')

@app.route('/<int:tournament_id>/event/<int:event_id>/de/edit')
@login_required
def editDE(tournament_id, event_id):
    return render_template('edit-de.html')
