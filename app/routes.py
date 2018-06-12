from datetime import datetime
import copy
from urllib.parse import urlparse
from operator import attrgetter
import json
import math

from sqlalchemy import func
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db

from app.forms import *
from app.models import *
from app.utils import generate_tournament, quicksort


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
    q = db.session.query(User, AccessTable, Tournament).filter(AccessTable.user_id == user.id).filter(Tournament.id == AccessTable.tournament_id).distinct()
    q = [i for _,_,i in q]
    return render_template('user.html', title=user.username, user=user, tournaments=q, public=False)


@app.route('/tournament/<int:tournament_id>')
def tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    events = tournament.events
    return render_template('tournament.html', tournament=tournament, events=events, public=True)


@app.route('/explore')
def explore():
    tournaments = Tournament.query.all()
    return render_template('explore.html', title='Explore', tournaments=tournaments, public=True)


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


@app.route('/tournament/<int:tournament_id>/create-event', methods=['GET', 'POST'])
@login_required
def createEvent(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    if isTOofTourney(current_user, tournament) is False:
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
    event = Event.query.get_or_404(event_id)
    return render_template('registration.html', event=event)


@app.route('/event/<int:event_id>/initial-seeding')
def initialSeeding(event_id):
    event = Event.query.get_or_404(event_id)
    if event.tournament.format == 'SWIFA':
        teams = event.teams.filter_by(isCheckedIn=True)
        return render_template('initial-seed-teams.html', event=event, teams=teams)
    elif event.tournament.format == 'USFA Individual':
        fencers = event.fencers.filter_by(isCheckedIn=True)
        fencers = fencers.order_by(Fencer.ratingClass.asc(), Fencer.ratingYear.desc())
        return render_template('initialSeed.html', event=event, fencers=fencers)


@app.route('/event/<int:event_id>/pool-results')
def poolResults(event_id):
    event = Event.query.get_or_404(event_id)
    #q = db.session.query(Fencer, Pool).filter(Fencer.event == event).filter(Fencer.pool_id == Pool.id).order_by(func.div(Fencer.victories, Pool.numFencers).desc(), Fencer.indicator.desc())
    #(fencers, _) = q
    #TODO: convert to sqlalchemy statement, needs more tie checking
    fencers = db.engine.execute('SELECT u.id, (u.victories*1.0 / (p.numFencers - 1)) as winPercent FROM fencer u JOIN pool p ON u.pool_id = p.id WHERE u.isCheckedIn IS 1 AND u.event_id = {} ORDER BY winPercent DESC, u.indicator DESC;'.format(event_id))
    fencers = [(Fencer.query.get(i), j) for (i, j) in fencers]
    return render_template('pool-results.html', event=event, fencers=fencers)


@app.route('/event/<int:event_id>/pools')
def pools(event_id):
    event = Event.query.get_or_404(event_id)
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
    event = Event.query.get_or_404(event_id)
    pools = event.pools
    fencers = event.fencers
    return render_template('pool-assignments.html', title='Pool Assignments', event=event, pools=pools, fencers=fencers)


#TODO: live des for public
@app.route('/event/<int:event_id>/de')
def de(event_id):
    event = Event.query.get_or_404(event_id)
    #return render_template('de.html', event=event)
    return "in progress"


#TODO: final results for public
@app.route('/event/<int:event_id>/final')
def final(tournament_id, event_id):
    return "in progress"


@app.route('/tournament/<int:tournament_id>/edit', methods=['GET', 'POST'])
@login_required
def editTournament(tournament_id):
    tournament = Tournament.query.filter_by(id=tournament_id).first()
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    form = AddTOForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            #TODO: send user email to register, requires a mail server
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
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))

    if tournament.format == 'SWIFA':
        teams = event.teams.all()
        form = AddTeamForm()
        if form.validate_on_submit():
            club = Club.query.filter_by(name=form.club.data.lower()).first()
            if club is None:
                club = Club(name=form.club.data.lower())
            team = Team(name=form.teamName.data, isCheckedIn=True)
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
            else: #create dummy fencer to fill c slot
                fencerC = Fencer(
                    firstName='',
                    lastName='',
                    teamPosition='C'
                )
                team.fencers.append(fencerC)
                db.session.add(fencerC)
            if form.fencerD.data is not '':
                fencerD = Fencer(
                    firstName=form.fencerD.data.split()[0].title(),
                    lastName=form.fencerD.data.split()[1].title(),
                    teamPosition='D')
                team.fencers.append(fencerD)
                db.session.add(fencerD)
            else: #create dummy fencer to fill d slot
                fencerD = Fencer(
                    firstName='',
                    lastName='',
                    teamPosition='D'
                )
                team.fencers.append(fencerD)
                db.session.add(fencerD)
            club.teams.append(team)
            event.teams.append(team)
            event.numFencersCheckedIn = Event.numFencersCheckedIn + 1
            event.numFencers += 1
            db.session.add_all([club, team, fencerA, fencerB])
            db.session.commit()
            flash('Added team')
            return redirect(url_for('editRegistration', event_id=event_id))
        return render_template('edit-registration-teams.html', form=form, teams=teams, event=event, allCheckedIn=(event.numFencersCheckedIn == event.numFencers))

    elif tournament.format == 'USFA Individual':
        fencers = event.fencers
        form = AddFencerForm()
        if form.validate_on_submit():
            club = Club.query.filter_by(name=form.club.data).first()
            if form.club.data is not None and club is None:
                club = Club(name=form.club.data.upper())
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
    event = Event.query.get_or_404(event_id)
    tournament = Tournament.query.filter_by(id=event.tournament_id).first()
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    pools = event.pools
    allPoolsDone = True
    for pool in pools:
        if pool.state is 0 and pool.poolLetter is not 'O':
            allPoolsDone = False
    if allPoolsDone:
        event.stage = 5
        if tournament.format == 'SWIFA':
            pass
        db.session.commit()
    if tournament.format == 'SWIFA':
        return render_template('edit-pools-teams.html', event=event, pools=pools)
    elif tournament.format == 'USFA Individual':
        return render_template('edit-pools.html', event=event, pools=pools)


@app.route('/event/<int:event_id>/pool/<int:pool_id>/edit', methods=['GET', 'POST'])
@login_required
def editPool(event_id, pool_id):
    pool = Pool.query.filter_by(id=pool_id).first()
    event = pool.event
    tournament = event.tournament
    user = User.query.filter_by(username=current_user.username).first()
    if not isTOofTourney(user, tournament):
        return redirect(url_for('index'))
    if request.method == "POST":
        validInput = True
        for key, val in request.form.items():
            #TODO: input validation, replace single v with v5
            if val[0].upper() not in ['V', 'D']:
                validInput = False
            elif val[0].upper() is 'V' and request.form['result'+key[7]+key[6]][0] is not 'D':
                validInput = False
            elif val[0].upper() is 'D' and request.form['result'+key[7]+key[6]][0] is not 'V':
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
            if tournament.format == 'SWIFA':
                fencer.team.victories = Team.victories + (1 if result.fencerWin else 0)
                fencer.team.touchesScored = Team.touchesScored + result.fencerScore
                fencer.team.indicator = Team.indicator + result.fencerScore
                opponent.team.touchesRecieved = Team.touchesRecieved + result.fencerScore
                opponent.team.indicator = Team.indicator - result.fencerScore
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
    event = Event.query.get_or_404(event_id)
    if not isTOofTourney(current_user, event.tournament):
        return redirect(url_for('index'))
    q = db.engine.execute('SELECT u.id, (u.victories*1.0 / (p.numFencers - 1)) as winPercent FROM fencer u JOIN pool p ON u.pool_id = p.id WHERE u.isCheckedIn IS 1 AND u.event_id = {} ORDER BY winPercent DESC, u.indicator DESC;'.format(event_id))
    fencers = [Fencer.query.get(id) for (id, _) in q]
    fencerNames = [(fencer.lastName + ", " + fencer.firstName + " (" + str(i+1) + ")") for i, fencer in enumerate(fencers)]
    bracket = generate_tournament(fencers)
    for _ in range(int((1 - 2 ** math.log(len(bracket), 2))/(1 - 2))):
        de = DE(state = 4)
        db.session.add(de)
        event.des.append(de)
    for fencer1, fencer2 in bracket:
        if fencer2 is None:
            de = DE(fencer1_id=fencer1.id, state=3)
            event.des.append(de)
            des = de.event.des.order_by(DE.id.asc()).all()
            print(de)
            nextDE = des[int(((des.index(de) + 1) & ~(1 << 0))/2)]
            print(nextDE)
            if (des.index(de)) % 2 is 0:
                nextDE.fencer1 = de.fencer1
            else:
                nextDE.fencer2 = de.fencer2
            if nextDE.fencer1 is not None and nextDE.fencer2 is not None:
                nextDE.state = 0
        else:
            de = DE(fencer1_id=(fencer1.id if fencer1 is not None else None), fencer2_id=(fencer2.id if fencer2 is not None else None), state=0)
            event.des.append(de)
        db.session.add(de)

    tableau = dict()
    tableau['teams'] = generate_tournament(fencerNames)
    tableau['results'] = [[] for _ in range(int(math.log(len(tableau['teams'])*2,2)))]
    i = 1
    #print(math.log(len(tableau['teams'])*2, 2))
    for round in range(int(math.log(len(tableau['teams'])*2,2))):
        tableau['results'][round] = [[] for _ in range(2 ** round)]
        for match in range(2 ** round):
            tableau['results'][round][match] = [None, None, 'match' + str(i)]
            i += 1
    tableau['results'] = tableau['results'][::-1]
    event.tableauJson = json.dumps(tableau)
    db.session.commit()
    return redirect(url_for('editDE', event_id=event_id))


@app.route('/de/<int:de_id>/submit', methods=['POST'])
@login_required
def submitDE(de_id):
    de = DE.query.get(de_id)
    de.fencer1Score = int(request.form['fencer1'])
    de.fencer2Score = int(request.form['fencer2'])
    if de.fencer1Score is de.fencer2Score:
        de.fencer1Win = request.form['fencer1Win']
    else:
        de.fencer1Win = True if de.fencer1Score > de.fencer2Score else False
    de.state = 2
    tableau = json.loads(de.event.tableauJson)
    #tableau['results'].append([de.fencer1Score, de.fencer2Score])

    des = de.event.des.order_by(DE.id.asc()).all()
    #print(des)
    match = len(tableau['teams']) - int(math.log(des.index(de), 2))
    print(len(tableau['teams']), int(math.log(des.index(de) + 1, 2)))
    #print(tableau)
    round = tableau['results'][match].index([None, None, 'match' + str(des.index(de)+1)])
    tableau['results'][match][round] = [de.fencer1Score, de.fencer2Score]
    de.event.tableauJson = json.dumps(tableau)
    nextDE = des[int(((des.index(de) + 1) & ~(1 << 0))/2)] #TODO: not finding parent de
    if (des.index(de)) % 2 is 0:
        nextDE.fencer1 = de.fencer1 if de.fencer1Win else de.fencer2
    else:
        nextDE.fencer2 = de.fencer1 if de.fencer1Win else de.fencer2
    if nextDE.fencer1 is not None and nextDE.fencer2 is not None:
        nextDE.state = 0
    db.session.commit()
    return redirect(url_for('editDE', event_id=de.event.id))


@app.route('/event/<int:event_id>/de/edit')
@login_required
def editDE(event_id):
    event = Event.query.get_or_404(event_id)
    fencers = event.fencers.order_by(Fencer.victories.desc(), Fencer.indicator.desc())
    des = event.des
    return render_template('edit-de.html', event=event, directElims=json.loads(event.tableauJson), des=des)


@app.route('/event/<int:event_id>/check-in/<int:fencer_id>')
@login_required
def checkInFencer(event_id, fencer_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    fencer = Fencer.query.get(fencer_id)
    fencer.isCheckedIn = True
    event.numFencersCheckedIn = Event.numFencersCheckedIn + 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))

@app.route('/event/<int:event_id>/check-in-team/<int:team_id>')
@login_required
def checkInTeam(event_id, team_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    team = Team.query.get(team_id)
    team.isCheckedIn = True
    event.numFencersCheckedIn = Event.numFencersCheckedIn + 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))

@app.route('/event/<int:event_id>/absent/<int:fencer_id>')
@login_required
def makeAbsent(event_id, fencer_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    fencer = Fencer.query.get(fencer_id)
    fencer.isCheckedIn = False
    event.numFencersCheckedIn = Event.numFencersCheckedIn - 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/event/<int:event_id>/absent-team/<int:team_id>')
@login_required
def makeAbsentTeam(event_id, team_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    team = Team.query.get(team_id)
    team.isCheckedIn = False
    event.numFencersCheckedIn = Event.numFencersCheckedIn - 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/event/<int:event_id>/edit-team/<int:team_id>', methods=['POST', 'GET'])
@login_required
def editTeamInfo(event_id, team_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    team = Team.query.get(team_id)
    fencerA = Fencer.query.filter_by(team_id=team.id, teamPosition='A').first()
    fencerB = Fencer.query.filter_by(team_id=team.id, teamPosition='B').first()
    fencerC = Fencer.query.filter_by(team_id=team.id, teamPosition='C').first()
    fencerD = Fencer.query.filter_by(team_id=team.id, teamPosition='D').first()
    form = AddTeamForm()
    if form.validate_on_submit():
        team.name = form.teamName.data
        if form.fencerA.data is not (fencerA.firstName + ' ' + fencerA.lastName):
            fencerA.firstName = form.fencerA.data.split()[0]
            fencerA.lastName = form.fencerA.data.split()[1]
        if form.fencerB.data is not (fencerB.firstName + ' ' + fencerB.lastName):
            fencerB.firstName = form.fencerB.data.split()[0]
            fencerB.lastName = form.fencerB.data.split()[1]
        if form.fencerC.data is not (fencerC.firstName + ' ' + fencerC.lastName):
            fencerC.firstName = form.fencerC.data.split()[0] or None
            fencerC.lastName = form.fencerC.data.split()[1] or None
        if form.fencerD.data is not (fencerD.firstName + ' ' + fencerD.lastName):
            fencerD.firstName = form.fencerD.data.split()[0] or None
            fencerD.lastName = form.fencerD.data.split()[1] or None
        flash('Edited team')
        db.session.commit()
        return redirect(url_for('editRegistration', event_id=event_id))
    elif request.method == 'GET':
        form.submit.label.text = "Edit Team"
        form.teamName.data = team.name
        form.fencerA.data = fencerA.firstName + ' ' + fencerA.lastName
        form.fencerB.data = fencerB.firstName + ' ' + fencerB.lastName
        form.fencerC.data = fencerC.firstName + ' ' + fencerC.lastName
        form.fencerD.data = fencerD.firstName + ' ' + fencerD.lastName
        form.club.data = Club.query.get(team.club_id).name
        return render_template('edit-team.html', form=form)


@app.route('/event/<int:event_id>/delete-team/<int:team_id>')
@login_required
def deleteTeam(event_id, team_id):
    pass


@app.route('/event/<int:event_id>/open-registration')
@login_required
def openRegistration(event_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    event.stage = 1
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/event/<int:event_id>/close-registration')
@login_required
def closeRegistration(event_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    fencers = event.fencers.order_by()
    event.stage = 2
    db.session.commit()
    return redirect(url_for('editRegistration', event_id=event_id))


@app.route('/event/<int:event_id>/create-pools', methods=['GET', 'POST'])
@login_required
def createPools(event_id):
    event = Event.query.get_or_404(event_id)
    tournament = event.tournament
    if not isTOofTourney(current_user, tournament):
        return redirect(url_for('index'))
    form = CreatePoolForm()
    if tournament.format == 'SWIFA':
        teams = event.teams.filter_by(isCheckedIn=True).order_by(Team.club_id.asc())
    elif tournament.format == 'USFA Individual':
        fencers = event.fencers.order_by(Fencer.team_id.desc())
        fencers = fencers.filter_by(isCheckedIn=True)
    form.numFencers.data = event.numFencersCheckedIn
    if form.validate_on_submit():
        pools = []
        poolNum = 1
        for _ in range(0, form.numPools1.data):
            if tournament.format == 'SWIFA':
                poolA = Pool(event_id = event.id, numFencers=form.numFencers1.data, poolNum=poolNum, poolLetter='A')
                poolB = Pool(event_id = event.id, numFencers=form.numFencers1.data, poolNum=poolNum, poolLetter='B')
                poolC = Pool(event_id = event.id, numFencers=form.numFencers1.data, poolNum=poolNum, poolLetter='C')
                poolOverall = Pool(event_id = event.id, numFencers=form.numFencers1.data, poolNum=poolNum, poolLetter='O')
                pools.append([poolA, poolB, poolC, poolOverall])
                db.session.add_all([poolA, poolB, poolC, poolOverall])
            elif tournament.format == 'USFA Individual':
                pool = Pool(event_id=event.id, numFencers=form.numFencers1.data, poolNum=poolNum)
                pools.append(pool)
                db.session.add(pool)
            poolNum += 1
        for _ in range(0, form.numPools2.data):
            if tournament.format == 'SWIFA':
                poolA = Pool(event_id = event.id, numFencers=form.numFencers2.data, poolNum=poolNum, poolLetter='A')
                poolB = Pool(event_id = event.id, numFencers=form.numFencers2.data, poolNum=poolNum, poolLetter='B')
                poolC = Pool(event_id = event.id, numFencers=form.numFencers2.data, poolNum=poolNum, poolLetter='C')
                poolOverall = Pool(event_id = event.id, numFencers=form.numFencers2.data, poolNum=poolNum, poolLetter='O')
                pools.append([poolA, poolB, poolC, poolOverall])
                db.session.add_all([poolA, poolB, poolC, poolOverall])
            elif tournament.format == 'USFA Individual':
                pool = Pool(event_id=event.id, numFencers=form.numFencers2.data, poolNum=poolNum)
                pools.append(pool)
                db.session.add(pool)
            poolNum += 1

        if event.tournament.format == 'SWIFA':
            pools = quicksort(pools)
        elif event.tournament.format == 'USFA Individual':
            pools.sort(key=attrgetter('numFencers'), reverse=True)

        poolNum = [0 for _ in pools]
        if tournament.format == 'SWIFA':
            for i, team in enumerate(teams):
                pools[i % len(pools)][3].teams.append(team)
                team.numInPool = poolNum[i % len(pools)] + 1
                team.pool = pools[i % len(pools)][3]
                fencers = team.fencers.order_by(Fencer.teamPosition.asc())
                for j in range(3):
                    pools[i % len(pools)][j].fencers.append(fencers[j])
                    fencers[j].numInPool = poolNum[i % len(pools)] + 1
                    fencers[j].pool = pools[i % len(pools)][j]
                poolNum[i % len(pools)] += 1

        elif tournament.format == 'USFA Individual':
            for i, fencer in enumerate(fencers.order_by(Fencer.lastName.asc())):
                pools[i % len(pools)].fencers.append(fencer)
                fencer.numInPool = poolNum[i % len(pools)] + 1
                poolNum[i % len(pools)] += 1
                fencer.pool = pools[i % len(pools)]

        event.stage = 3
        db.session.commit()
        return redirect(url_for('editPools', event_id=event_id))
    return render_template('create-pools.html', form=form, event=event, numFencers=event.numFencersCheckedIn)
