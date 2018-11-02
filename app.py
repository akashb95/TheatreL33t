from flask import Flask, render_template, request, url_for, redirect, jsonify, session, flash
from helpers import login_required, hash_password
from lookup import lookup
from flask_session import Session
from flask_jsglue import JSGlue
from neomodel import config, db
from db_creds import db_pass, db_user
from tempfile import mkdtemp
from models import Staff, Customer, Movie, Hall, ShowingIn, Booked, Added, Cancelled

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
def index():
    return render_template("index.html", query="")


@app.route('/search', methods=["POST", "GET"])
def search(query=None):
    results = lookup(query)
    return redirect(url_for('index'))


@login_required
@app.route('/add')
def add_film():
    if not session["admin"]:
        flash("Insufficient privileges to complete this action!")
        render_template("index.html")

    film_name = request.form.get("film-name")
    film_desc = request.form.get("film-description")
    film_duration = request.form.get("film-duration")
    film_hall = request.form.get("film-hall")
    film_times = request.form.get("film-times")
    added_by = session["user_id"]

    return render_template("add_film.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()  # Forget any user_id

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed = None

        # Check if password given. If not, redirect to login page with error message.
        if password:
            hashed = hash_password(password)  # hash password

        else:
            flash("No password given!")
            render_template("login.html")

        user = Customer.nodes.get_or_none(username=username, password=hashed)

        if user:
            session["user_id"] = user.uuid
            session["username"] = user.username
            session["admin"] = False
            return redirect(url_for("index"))

        else:
            flash("Username or password incorrect!")
            render_template("login.html")

    return render_template("login.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if password given. If not, redirect to login page with error message.
        if password:
            hashed = hash_password(password)  # hash password

        else:
            flash("No password given!")
            return render_template("admin.html")

        user = Staff.nodes.get_or_none(username=username, password=hashed)

        if user:
            session["user_id"] = user.uuid
            session["username"] = user.username
            session["admin"] = True
            return redirect(url_for("index"))

        else:
            flash("Username or password incorrect!")
            return render_template("admin.html")
    return render_template("admin.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        errors = False
        f_name = request.form.get("fname")
        l_name = request.form.get("lname")
        username = request.form.get("username")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat-password")
        hashed = None

        if password and repeat_password and repeat_password == password:
            hashed = hash_password(password)

        # If something is wrong with the password.
        else:
            flash("Passwords do not match. Please try again.")
            errors = True

        if Customer.nodes.get_or_none(username=username):
            flash("This username already exists! Please choose another. \n")
            errors = True

        # If all is well, make user, log in and continue to home page.
        if not errors:
            # Save user to database and reload (to get generated User.uid)
            new_user = Customer(username=username, password=hashed, f_name=f_name, l_name=l_name).save()

            # Remember which user has logged in.
            session["user_id"] = new_user.uuid
            session["username"] = new_user.username
            session["admin"] = False

            # Redirect user to home page.
            flash("Welcome, {user}. You have been registered and logged in.".format(user=new_user))
            return redirect(url_for("index"))

        else:
            return render_template("register.html")
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect((url_for("index")))


@login_required
@app.route("/unregister")
def unregister():
    return render_template("404.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


if __name__ == '__main__':
    app.run()
