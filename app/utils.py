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


class Score():
    
    def __new__(self, score):
        if len(score) == 0:
            
        elif len(score) == 1:
            if score.upper() == 'V':
                self.letter = 'V'
                self.touches = 5
            elif score in [str(i) for i in range(1,6)]:
                self.letter = 'D'
                self.touches = int(score)
            else:
                return False
        elif len(score) == 2:
            self.letter = score[0].upper()
            self.touches = int(score[1])
        else:
            return False

    def is_winner(self):
        return self.letter == 'V'

    def __lt__(self, other):
        return self.touches < other.touches


def is_valid_pair(first, second):
    if first.is_winner() ^ second.is_winner() == False:
        return False
    (winner, loser) = (first, second) if first.is_winner() else (second, first)
    if winner < loser:
        return False
    return True
