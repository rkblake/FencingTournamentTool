import math

def nextPow2(v):
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    v += 1
    return v

def tournament_round( no_of_teams , matchlist ):
    new_matches = []
    for team_or_match in matchlist:
        if type(team_or_match) == type([]):
            new_matches += [ tournament_round( no_of_teams, team_or_match ) ]
        else:
            new_matches += [ [ team_or_match, no_of_teams + 1 - team_or_match ] ]
    return new_matches

def flatten_list( matches ):
    teamlist = []
    for team_or_match in matches:
        if type(team_or_match) == type([]):
            teamlist += flatten_list( team_or_match )
        else:
            teamlist += [team_or_match]
    return teamlist

def generate_tournament( num, teamNames ):
    num = nextPow2(num)
    teams = 1
    result = [1]
    while teams != num:
        teams *= 2
        result = tournament_round( teams, result )
    result = flatten_list( result )

    for _ in range(num - len(teamNames)):
        teamNames.append(None)

    for i, j in enumerate(result):
        result[i] = teamNames[j-1]
    pairs = [list(i) for i in zip(*[iter(result)]*2)]
    return pairs
