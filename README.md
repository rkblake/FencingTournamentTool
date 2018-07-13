# FencingTournamentTool
> Tool for running fencing tournaments and displaying live results

## Installation

OS X & Linux:

```sh
pip install -r requirements.txt
export FLASK_APP=fencingtournamenttool.py
flask db init
flask db migrate
flask db upgrade
flask run
```

Windows:

```sh
pip install -r requirements.txt
set FLASK_APP=fencingtournamenttool.py
flask db init
flask db migrate
flask db upgrade
flask run
```

## Release History

* 0.1.0
    * All basic features working
    * Split project into SWIFA and USFA parts
    * Added more checking on user registration

## Meta

Randall Blake – blakerandall0@gmail.com

Distributed under the MIT license.
