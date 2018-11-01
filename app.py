from flask import Flask
from flask_session import Session
from flask_jsglue import JSGlue
from neomodel import config, db
from db_creds import db_pass, db_user

# Flask initialisation
app = Flask(__name__)
JSGlue(app)

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connecting to neo4j database.
config.DATABASE_URL = "bolt://{username}:{password}@localhost:7687".format(username=db_user, password=db_pass)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
