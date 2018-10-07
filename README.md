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

## Running The Server
You should do this each time you update from upstream and want to run the server

Make and apply migrations:

`./manage.py makemigrations`

`./manage.py migrate`

Run the server:

`./manage.py runserver`

## Options

If you'd like to run the server on a different port you can use the ipaddress:port syntax like so:

`./manage.py runserver 127.0.0.1:9000`

For more information see:

`./manage.py help runserver`

And the settings reference in the Django documentation: https://docs.djangoproject.com/en/2.1/ref/settings/
