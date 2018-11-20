#!/usr/bin/env bash

source ./venv/bin/activate
./neo4j/bin/neo4j console &

export FLASK_DEBUG=0
export FLASK_ENV=production
export FLASK_APP=app.py
./venv/bin/flask run
