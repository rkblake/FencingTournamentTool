from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, CreateTournamentForm, CreateEventForm, AddFencerForm, CreatePoolForm
from app.models import User, Tournament, Event, Fencer, Team, Pool
from datetime import datetime

def isTOofTourney(user, tournament):
    #TODO: check if user has access to tournament
    return True

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
    logout_user()
    return redirect(url_for('index'))

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
        tournament = Tournament(name=form.name.data.title(), format=form.format.data)
        user.tournaments.append(tournament)
        #TODO: add user as TO of tourney
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
    if isTOofTourney(user, tournament) is False:
        return redirect(url_for('index'))
    form = CreateEventForm()
    if form.validate_on_submit():
        event = Event(
                name=form.name.data.title(),
                date=datetime.strptime(form.date.data.strftime('%m/%d/%Y'), '%m/%d/%Y'),
                tournament=tournament)
        tournament.events.append(event)
        db.session.add(event)
        db.session.commit()
        flash('Created new event')
        return redirect(url_for('editTournament', tournament_id=tournament_id))
    return render_template('create-event.html', tournament=tournament, form=form)

#TODO: live registration view for public
@app.route('/<int:tournament_id>/event/<int:event_id>/registration')
def registration(tournament_id, event_id):
    return "registration"

#TODO: live pools for public
@app.route('/<int:tournament_id>/event/<int:event_id>/pool')
def pool(tournament_id, event_id):
    return "pool"

#TODO: live des for public
@app.route('/<int:tournament_id>/event/<int:event_id>/de')
def de(tournament_id, event_id):
    return "de"

#TODO: final results for public
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

@app.route('/event/<int:event_id>/registration/edit', methods=['GET', 'POST'])
@login_required
def editRegistration(event_id):
    #tournament = Tournament.query.filter_by(id=tournament_id).first()
    event = Event.query.filter_by(id=event_id).first()
    fencers = event.fencers
    form = AddFencerForm()
    if form.validate_on_submit():
        team = None
        team = Team.query.filter_by(name=form.team.data).first()
        if form.team.data is not None and team is None:
            team = Team(name=form.team.data)
        fencer = Fencer(
                firstName=form.firstName.data.title(),
                lastName=form.lastName.data.title(),
                team_id=team,
                rating=form.rating.data.upper(),
                isCheckedIn=form.checked_in.data)
        if team is not None:
            team.fencers.append(fencer)
        event.fencers.append(fencer)
        event.numFencers += 1
        if fencer.isCheckedIn:
            event.numFencersCheckedIn = Event.numFencersCheckedIn + 1
        db.session.add(fencer)
        db.session.commit()
        flash('Added fencer')
    return render_template('edit-registration.html', form=form, fencers=fencers, event=event)

@app.route('/event/<int:event_id>/edit-pools')
@login_required
def editPools(event_id):
    event = Event.query.filter_by(id=event_id).first()
    pools = event.pools
    return render_template('edit-pools.html', event=event, pools=pools)

#TODO: sanitize and check input; rewrite using wtform
@app.route('/event/<int:event_id>/pool/<int:pool_id>/edit', methods=['GET', 'POST'])
@login_required
def editPool(event_id, pool_id):
    pool = Pool.query.filter_by(id=pool_id).first()
    fencers = pool.fencers
    seen = dict()
    if request.method == "POST":
        for key, value in request.form.items():
            key = key.strip('result')
            if key.reverse() in seen:
                result = Result.query.filter_by(id=seen[key.reverse()]).first()
                result.fencer2Score=result[1]
            fencer1 = Fencer.query.filter_by(pool_id=pool_id, numInPool=key[0]).first()
            fencer2 = Fencer.query.filter_by(pool_id=pool_id, numInPool=key[1]).first()
            result = Result(pool_id=pool.id, fencer1=fencer1, fencer2=fencer2, fencer1Score=int(result[1]))
            result.fencer1Win = True if result[0].lower is 'v' else False
            seen[key] = result.id
            db.session.add(result)
        pool.state = 1
        db.session.commit()
        return redirect(url_for('edit-pools.html', event_id=event_id))
    elif request.method == "GET":
        event = Event.query.filter_by(id=event_id).first()
        return render_template('edit-pool.html', event=event, pool=pool, fencers=fencers)

@app.route('/event/<int:event_id>/de/edit')
@login_required
def editDE(tournament_id, event_id):
    return render_template('edit-de.html')

@app.route('/<int:event_id>/check-in/<int:fencer_id>')
@login_required
def checkInFencer(event_id, fencer_id):
    fencer = Fencer.query.filter_by(id=fencer_id).first()
    fencer.isCheckedIn = True
    event.numFencersCheckedIn += 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))

@app.route('/<int:event_id>/absent/<int:fencer_id>')
@login_required
def makeAbsent(event_id, fencer_id):
    fencer = Fencer.query.filter_by(id=fencer_id).first()
    fencer.isCheckedIn = False
    event.numFencersCheckedIn -= 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))

@app.route('/open-registration/<int:event_id>')
@login_required
def openRegistration(event_id):
    event = Event.query.filter_by(id=event_id).first()
    event.stage = 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))

@app.route('/close-registration/<int:event_id>')
@login_required
def closeRegistration(event_id):
    event = Event.query.filter_by(id=event_id).first()
    event.stage = 2
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))

@app.route('/<int:event_id>/create-pools', methods=['GET', 'POST'])
@login_required
def createPools(event_id):
    form = CreatePoolForm()
    event = Event.query.filter_by(id=event_id).first()
    #TODO: only select checked in fencers
    fencers = event.fencers.order_by(Fencer.team_id.desc())
    form.numFencers.data = event.numFencers
    if form.validate_on_submit():
        pools = []
        poolNum = 1
        for _ in range(0, form.numPools1.data):
            pool = Pool(event_id = event.id, numFencers = form.numFencers1.data, poolNum = poolNum)
            poolNum += 1
            pools.append(pool)
            db.session.add(pool)
        for _ in range(0, form.numPools2.data):
            pool = Pool(event_id = event.id, numFencers = form.numFencers2.data, poolNum = poolNum)
            poolNum += 1
            pools.append(pool)
            db.session.add(pool)
        for i, fencer in enumerate(fencers):
            pools[i % len(pools)].fencers.append(fencer)
            fencer.pool = pools[i % len(pools)]
        for pool in pools:
            for i, fencer in enumerate(pool.fencers):
                fencer.numInPool = i
        db.session.commit()
        return redirect(url_for('editPools', event_id=event_id))
    return render_template('create-pools.html', form=form, event=event)
