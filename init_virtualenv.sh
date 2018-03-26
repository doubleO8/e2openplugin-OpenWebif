#!/bin/bash
pip install virtualenv

virtualenv venv

. venv/bin/activate

if [ -f requirements.txt ]
then
    pip install -r requirements.txt
fi

if [ -f requirements-testing.txt ]
then
    pip install -r requirements-testing.txt
fi

if [ -f requirements-documentation.txt ]
then
    pip install -r requirements-documentation.txt
fi

pip freeze
