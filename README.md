# FencingTournamentTool
> Tool for running fencing tournaments and displaying live results

## Installation

OS X & Linux:

```sh
pip install -r requirements.txt
flask db init
flask db migrate
flask db upgrade
export FLASK_APP=fencingtournamenttool.py
flask run
```

Windows:

```sh
pip install -r requirements.txt
flask db init
flask db migrate
flask db upgrade
set FLASK_APP=fencingtournamenttool.py
flask run
```

## Release History

* 0.0.0
    * everything up to pools working

## Meta

Randall Blake – blakerandall0@gmail.com

Distributed under the MIT license.
