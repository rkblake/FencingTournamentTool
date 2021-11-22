from app import app, db
from app.models import User, Event, Pool, Fencer

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'User': User,
            'Event': Event,
            'Pool': Pool,
            'Fencer': Fencer}

if __name__ == '__main__':
    app.run(use_debugger=False, use_reloader=False, passthrough_errors=True)