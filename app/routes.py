from datetime import datetime
import copy
from urllib.parse import urlparse
from operator import attrgetter
from sqlalchemy import func

from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db

from app.forms import *
from app.models import *
from app.utils import generate_tournament


def isTOofTourney(user, tournament):
    access = AccessTable.query.filter_by(user_id=user.id, tournament_id=tournament.id).first()
    if access is not None:
        return True
    else:
        return False


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
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
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
        user = User(username=form.username.data.lower(), email=form.email.data)
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
    if user != current_user:
        return redirect(url_for('index'))
    #TODO: remove duplicates
    q = db.session.query(User, AccessTable, Tournament).filter(AccessTable.user_id == user.id).filter(Tournament.id == AccessTable.tournament_id).distinct()
    q = [i for _,_,i in q]
    return render_template('user.html', user=user, tournaments=q, public=False)


@app.route('/tournament/<int:tournament_id>')
def tournament(tournament_id):
    tournament = Tournament.query.filter_by(id=tournament_id).first()
    events = tournament.events
    return render_template('tournament.html', tournament=tournament, events=events, public=True)


@app.route('/explore')
def explore():
    tournaments = Tournament.query.all()
    return render_template('explore.html', tournaments=tournaments, public=True)


@app.route('/create-tournament', methods=['GET', 'POST'])
@login_required
def createTournament():
    user = User.query.filter_by(username=current_user.username).first()
    form = CreateTournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(name=form.name.data.title(), format=form.format.data)
        access = AccessTable(user_id=user.id, tournament_id=tournament.id, mainTO=True)
        user.tournaments.append(access)
        tournament.organizers.append(access)
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


@app.route('/event/<int:event_id>/registration')
def registration(event_id):
    event = Event.query.filter_by(id=event_id).first()
    return render_template('registration.html', event=event)


@app.route('/event/<int:event_id>/initial-seeding')
def initialSeeding(event_id):
    event = Event.query.filter_by(id=event_id).first()
    fencers = event.fencers.order_by(Fencer.ratingClass.asc(), Fencer.ratingYear.desc())
    return render_template('initialSeed.html', event=event, fencers=fencers)


@app.route('/event/<int:event_id>/pool-results')
def poolResults(event_id):
    event = Event.query.filter_by(id=event_id).first()
    #q = db.session.query(Fencer, Pool).filter(Fencer.event == event).filter(Fencer.pool_id == Pool.id).order_by(func.div(Fencer.victories, Pool.numFencers).desc(), Fencer.indicator.desc())
    #(fencers, _) = q
    #TODO: convert to sqlalchemy statement, needs more tie checking
    fencers = db.engine.execute('SELECT u.id, (u.victories*1.0 / (p.numFencers - 1)) as winPercent FROM fencer u JOIN pool p ON u.pool_id = p.id WHERE u.isCheckedIn IS 1 AND u.event_id = {} ORDER BY winPercent DESC, u.indicator DESC;'.format(event_id))
    fencers = [(Fencer.query.get(i), j) for (i, j) in fencers]
    return render_template('pool-results.html', event=event, fencers=fencers)


@app.route('/event/<int:event_id>/pools')
def pools(event_id):
    event = Event.query.filter_by(id=event_id).first()
    pools = event.pools
    results = dict()
    fencers = dict()
    for pool in pools:
        fencers[pool.poolNum] = pool.fencers.order_by(Fencer.numInPool.asc())
        results[pool.poolNum] = dict()
        for result in pool.results:
            fencer = Fencer.query.filter_by(pool=pool, id=result.fencer).first()
            opponent = Fencer.query.filter_by(id=result.opponent).first()
            results[pool.poolNum][str(fencer.numInPool)+str(opponent.numInPool)] = result

    #fencers = event.fencers.order_by(Fencer.numInPool.asc())
    return render_template('pools.html', title='Pools', event=event, pools=pools, results=results, fencers=fencers)


#TODO: pool assignments
@app.route('/event/<int:event_id>/pool-assignment')
def poolAssignment(event_id):
    event = Event.query.filter_by(id=event_id).first()
    pools = event.pools
    fencers = event.fencers
    return render_template('pool-assignments.html', title='Pool Assignments' event=event, pools=pools, fencers=fencers)


#TODO: live des for public
@app.route('/event/<int:event_id>/de')
def de(event_id):
    event = Event.query.filter_by(id=event_id).first()
    #return render_template('de.html', event=event)
    return "in progress"


#TODO: final results for public
@app.route('/event/<int:event_id>/final')
def final(tournament_id, event_id):
    return "in progress"


@app.route('/<int:tournament_id>/edit', methods=['GET', 'POST'])
@login_required
def editTournament(tournament_id):
    user = User.query.filter_by(username=current_user.username).first()
    tournament = Tournament.query.filter_by(id=tournament_id).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    form = AddTOForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            #TODO: send user email to register
            return
        access = AccessTable(user_id=user.id, tournament_id=tournament.id, mainTO=False)
        user.tournaments.append(access)
        tournament.organizers.append(access)
        db.session.add(access)
        db.session.commit()
    events = tournament.events
    return render_template('edit-tournament.html', title='Edit Tournament', tournament=tournament, events=events, form=form)


@app.route('/event/<int:event_id>/registration/edit', methods=['GET', 'POST'])
@login_required
def editRegistration(event_id):
    user = User.query.filter_by(username=current_user.username).first()
    event = Event.query.filter_by(id=event_id).first()
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))

    if tournament.format == 'SWIFA':
        teams = event.teams
        form = AddTeamForm()
        if form.validate_on_submit():
            club = Club.query.filter_by(name=form.club.data.lower()).first()
            if club is None:
                club = Club(name=form.club.data.lower())
            team = Team(name=form.teamName.data)
            fencerA = Fencer(
                firstName=form.fencerA.data.split()[0].title(),
                lastName=form.fencerA.data.split()[1].title(),
                teamPosition='A')
            team.fencers.append(fencerA)
            fencerB = Fencer(
                firstName=form.fencerB.data.split()[0].title(),
                lastName=form.fencerB.data.split()[1].title(),
                teamPosition='B')
            team.fencers.append(fencerB)
            if form.fencerC.data is not '':
                fencerC = Fencer(
                    firstName=form.fencerC.data.split()[0].title(),
                    lastName=form.fencerC.data.split()[1].title(),
                    teamPosition='C')
                team.fencers.append(fencerC)
                db.session.add(fencerC)
            if form.fencerD.data is not '':
                fencerD = Fencer(
                    firstName=form.fencerD.data.split()[0].title(),
                    lastName=form.fencerD.data.split()[1].title(),
                    teamPosition='D')
                team.fencers.append(fencerD)
                db.session.add(fencerD)
            club.teams.append(team)
            event.teams.append(team)
            event.numFencersCheckedIn = Event.numFencersCheckedIn + 1
            event.numFencers += 1
            db.session.add_all([club, team, fencerA, fencerB])
            db.session.commit()
            flash('Added team')
        return render_template('edit-registration-teams.html', form=form, teams=teams, event=event, allCheckedIn=(event.numFencersCheckedIn == event.numFencers))

    elif tournament.format == 'USFA Individual':
        fencers = event.fencers
        form = AddFencerForm()
        if form.validate_on_submit():
            club = Club.query.filter_by(name=form.club.data).first()
            if form.club.data is not None and club is None:
                club = Club(name=form.club.data.title())
            fencer = Fencer(
                    firstName=form.firstName.data.title(),
                    lastName=form.lastName.data.title(),
                    club=club,
                    ratingClass=form.rating.data[0].upper(),
                    ratingYear=int(form.rating.data[1:] or 18),
                    isCheckedIn=form.checked_in.data)
            if club is not None:
                club.fencers.append(fencer)
            event.fencers.append(fencer)
            event.numFencers += 1
            if fencer.isCheckedIn:
                event.numFencersCheckedIn = Event.numFencersCheckedIn + 1
            db.session.add(fencer)
            db.session.commit()
            flash('Added fencer')
        return render_template('edit-registration.html', form=form, fencers=fencers, event=event, allCheckedIn=(event.numFencersCheckedIn == event.numFencers))


@app.route('/event/<int:event_id>/edit-pools')
@login_required
def editPools(event_id):
    user = User.query.filter_by(username=current_user.username).first()
    event = Event.query.filter_by(id=event_id).first()
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    pools = event.pools
    allPoolsDone = True
    for pool in pools:
        if pool.state is 0:
            allPoolsDone = False
    if allPoolsDone:
        event.stage = 5
        db.session.commit()
    return render_template('edit-pools.html', event=event, pools=pools)


@app.route('/event/<int:event_id>/pool/<int:pool_id>/edit', methods=['GET', 'POST'])
@login_required
def editPool(event_id, pool_id):
    pool = Pool.query.filter_by(id=pool_id).first()
    event = pool.event
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    user = User.query.filter_by(username=current_user.username).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    if request.method == "POST":
        validInput = True
        for key, val in request.form.items():
            #TODO: input validation, replace single v with v5
            if val[0].upper() not in ['V', 'D']:
                validInput = False
            if val[0].upper() is 'V' and request.form['result'+key[7]+key[6]][0] is not 'D':
                validInput = False
            if val[0].upper() is 'D' and request.form['result'+key[7]+key[6]][0] is not 'V':
                validInput = False
        if not validInput:
            flash('Invalid score')
            return redirect(url_for('editPool', event_id=evnt_id, pool_id=pool_id))
        for key, value in request.form.items():
            key = key.strip('result')
            fencer = Fencer.query.filter_by(pool_id=pool_id, numInPool=key[0]).first()
            opponent = Fencer.query.filter_by(pool_id=pool_id, numInPool=key[1]).first()
            result = Result(pool_id=pool.id, fencer=fencer.id, fencerScore=value[1:], opponent=opponent.id, fencerWin=(value[0].upper() == 'V'))
            fencer.victories = Fencer.victories + (1 if result.fencerWin else 0)
            fencer.touchesScored = Fencer.touchesScored + result.fencerScore
            fencer.indicator = Fencer.indicator + result.fencerScore
            opponent.touchesRecieved = Fencer.touchesRecieved + result.fencerScore
            opponent.indicator = Fencer.indicator - result.fencerScore
            pool.results.append(result)
            db.session.add(result)
        pool.state = 1
        db.session.commit()
        return redirect(url_for('editPools', event_id=event_id))
    elif request.method == "GET":
        fencers = pool.fencers.order_by(Fencer.numInPool.asc())
        return render_template('edit-pool.html', event=event, pool=pool, fencers=fencers)


@app.route('/event/<int:event_id>/generate-bracket')
@login_required
def generateBracket(event_id):
    event = Event.query.get(event_id)
    if not isTOofTourney(current_user, event):
        return redirect(url_for('index'))
    fencers = db.engine.execute('SET @row_num = 0; SELECT u.id, (u.victories*1.0 / (p.numFencers - 1)) as winPercent, @row_num := @row_num + 1 as row_index, FROM fencer u JOIN pool p ON u.pool_id = p.id WHERE u.isCheckedIn IS 1 AND u.event_id = {} ORDER BY winPercent DESC, u.indicator DESC;'.format(event_id))
    fencers = [(Fencer.query.get(i), j) for (i, _, j) in fencers]
    fencers = [(fencer[0].lastName + ", " + fencer[0].firstName, + " (" + fencer[1] + ")") for fencer in fencers]
    bracket = generate_tournament(fencers)


#TODO: append seed to fencer names
@app.route('/event/<int:event_id>/de/edit')
@login_required
def editDE(event_id):
    event = Event.query.filter_by(id=event_id).first()
    fencers = event.fencers.order_by(Fencer.victories.desc(), Fencer.indicator.desc())
    directElims = dict()
    #bracket = generate_tournament(fencers)

    fencers = [(fencer.lastName + ", " + fencer.firstName) for fencer in fencers]

    directElims["teams"] = generate_tournament(fencers)

    return render_template('edit-de.html', event=event, directElims=directElims)


@app.route('/event/<int:event_id>/check-in/<int:fencer_id>')
@login_required
def checkInFencer(event_id, fencer_id):
    event = Event.query.filter_by(id=event_id).first()
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    user = User.query.filter_by(username=current_user.username).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    fencer = Fencer.query.filter_by(id=fencer_id).first()
    fencer.isCheckedIn = True
    event.numFencersCheckedIn = Event.numFencersCheckedIn + 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/event/<int:event_id>/absent/<int:fencer_id>')
@login_required
def makeAbsent(event_id, fencer_id):
    event = Event.query.filter_by(id=event_id).first()
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    user = User.query.filter_by(username=current_user.username).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    fencer = Fencer.query.filter_by(id=fencer_id).first()
    fencer.isCheckedIn = False
    event.numFencersCheckedIn = Event.numFencersCheckedIn - 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/open-registration/<int:event_id>')
@login_required
def openRegistration(event_id):
    event = Event.query.filter_by(id=event_id).first()
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    user = User.query.filter_by(username=current_user.username).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    event.stage = 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/close-registration/<int:event_id>')
@login_required
def closeRegistration(event_id):
    event = Event.query.filter_by(id=event_id).first()
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    user = User.query.filter_by(username=current_user.username).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    fencers = event.fencers.order_by()
    event.stage = 2
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/<int:event_id>/create-pools', methods=['GET', 'POST'])
@login_required
def createPools(event_id):
    event = Event.query.filter_by(id=event_id).first()
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    user = User.query.filter_by(username=current_user.username).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    form = CreatePoolForm()
    fencers = event.fencers.order_by(Fencer.team_id.desc())
    fencers = fencers.filter_by(isCheckedIn=True)
    form.numFencers.data = event.numFencersCheckedIn
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
        pools.sort(key=attrgetter('numFencers'), reverse=True)

        poolNum = [0 for _ in pools]
        for i, fencer in enumerate(fencers.order_by(Fencer.lastName.asc())):
            pools[i % len(pools)].fencers.append(fencer)
            fencer.numInPool = poolNum[i % len(pools)] + 1
            poolNum[i % len(pools)] += 1
            fencer.pool = pools[i % len(pools)]

        event.stage = 3
        db.session.commit()
        return redirect(url_for('editPools', event_id=event_id))
    return render_template('create-pools.html', form=form, event=event, numFencers=event.numFencersCheckedIn)
