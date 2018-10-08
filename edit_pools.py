from app import db
from app.models import Event, Pool, Fencer, Team

if __name__ == "__main__":
    event_num = int(input("Enter the number of the event you want to edit: "))
    event = Event.query.get(event_num)
    print("The current pools are:")
    for pool in event.pools:
        if pool.pool_letter != 'O':
            continue
        print(pool)
        for team in pool.teams:
            print('\t' + str(team))

    print('\nEditing Pools')
    for pool in event.pools:
        if pool.pool_letter != 'O':
            continue
        for team in pool.teams.order_by(Team.num_in_pool.asc()):
            old_pool = team.pool
            new_pool = int(input("Enter new pool for " + str(team) + ": "))
            new_pool_num = int(input("Enter new pool number for " + str(team) + ": "))
            pool = Pool.query.filter_by(poolNum = new_pool).first()
            team.pool = pool
            team.num_in_pool = new_pool_num
            pool.num_fencers = Pool.num_fencers + 1
            old_pool.num_fencers = Pool.num_fencers - 1

    db.session.commit()
