def nextPow2(v):  # rounds up to next power of 2
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    v += 1
    return v


def tournament_round(no_of_teams, matchlist):
    new_matches = []
    for team_or_match in matchlist:
        if type(team_or_match) == type([]):
            new_matches += [tournament_round(no_of_teams, team_or_match)]
        else:
            new_matches += [[team_or_match, no_of_teams + 1 - team_or_match]]
    return new_matches


def flatten_list( matches ):
    teamlist = []
    for team_or_match in matches:
        if type(team_or_match) == type([]):
            teamlist += flatten_list(team_or_match)
        else:
            teamlist += [team_or_match]
    return teamlist


def generate_tournament(fencers):
    fencers = [fencer for fencer in fencers]
    num = nextPow2(len(fencers))
    teams = 1
    result = [1]
    while teams != num:
        teams *= 2
        result = tournament_round(teams, result)
    result = flatten_list(result)

    for _ in range(num - len(fencers)):
        fencers.append(None)

    for i, j in enumerate(result):
        result[i] = fencers[j-1]
    pairs = [list(i) for i in zip(*[iter(result)]*2)]
    return pairs


def quicksort(x):  # descending sort
    if len(x) < 2:
        return x
    else:
        pivot = x[0]
        less = [i for i in x[1:] if i[0].num_fencers <= pivot[0].num_fencers]
        greater = [i for i in x[1:] if i[0].num_fencers > pivot[0].num_fencers]
        return quicksort(greater) + [pivot] + quicksort(less)


def validate_score_pair(score1, score2):
    if ((score1 == '') ^ (score2 == '')):
        return False
    #elif not (score1 == '') and (score2 == ''):
    #    return False
    if score1[0].upper() not in ['V', 'D']:
        return False
    if int(score1[1]) > int(score2[1]) and score1[0].upper() == 'D':
        return False
    if int(score2[1]) > int(score1[1]) and score2[0].upper() == 'D':
        return False
    if int(score1[1]) < int(score2[1]) and score1[0].upper() == 'V':
        return False
    if int(score2[1]) < int(score1[1]) and score2[0].upper() == 'V':
        return False


def validate_scores(form):  # TODO: only check upper right triangle; accept same score ties as long as one is a victory
    for key, score in form.items():
        score1 = score
        score2 = form['result'+key[7]+key[6]]
        
    return True
