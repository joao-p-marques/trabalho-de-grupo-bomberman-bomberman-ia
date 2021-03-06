[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/joao-p-marques/trabalho-de-grupo-bomberman-bomberman-ia) 

# iia-ia-bomberman
Bomberman clone for AI teaching

## How to install

Make sure you are running Python 3.5.

`$ pip install -r requirements.txt`

*Tip: you might want to create a virtualenv first*

** OR **

Create a virtual environment with Pipenv

( 
1. Install pipenv
`$ pip install pipenv`
)
2. Create virtual environment with pipenv
`$ pipenv shell`

Pipenv will enter the virtualenv and install dependencies from Pipfile (created from requirements.txt)

3. Install dependencies (in pipenv virtualenv)
`> pipenv install --skip-lock`
(lock takes too long)

## How to play

open 3 terminals:

`$ python3 server.py`

`$ python3 viewer.py`

`$ python3 client.py`

to play using the sample client make sure the client pygame hidden window has focus

### Keys

Directions: arrows

*A*: 'a' - detonates (only after picking up the detonator powerup)

*B*: 'b' - drops bomb

## Debug Installation

Make sure pygame is properly installed:

python -m pygame.examples.aliens

# Tested on:
- Ubuntu 18.04
- OSX 10.14.6
- Windows 10.0.18362

