# accordius
Alternative LessWrong 2 API backend with Django and Postgres

## Installation
First, git clone this repository or your fork:

`git clone git@github.com:JD-P/accordius.git`

`cd accordius`

Next we create a virtual environment for accordius:

`virtualenv --python=python3 env_accordius`

Activate the virtual environment:

`source env_accordius/bin/activate`

Install dependencies with pip:

`pip install -r requirements.txt `

Make and apply vigrations:

`./manage.py makemigrations`

`./manage.py migrate`

Run the server:

`./manage.py runserver`
