from flask import Flask, render_template, request, url_for, redirect, session, flash
from helpers import login_required, hash_password, parse_showtimes, collides, hall_diagram
from lookup import lookup, user_history, lookup_by_date, cancel_booking, recommends
from datetime import datetime, timedelta
from pytz import utc
from flask_session import Session
from flask_jsglue import JSGlue
from neomodel import config
from db_creds import db_pass, db_user
from tempfile import mkdtemp
from models import Staff, Customer, Movie, Hall, Showing, Added

# Flask initialisation
app = Flask(__name__)
JSGlue(app)

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connecting to neo4j database.
config.DATABASE_URL = "bolt://{username}:{password}@localhost:11001".format(username=db_user, password=db_pass)


@app.route('/')
def index():
    results = lookup(query="")
    return render_template("index.html", query="", films=results)


@app.route('/search', methods=["POST", "GET"])
def search(query=None):
    if not query:
        query = request.values.get("q")

    if query:
        results = lookup_by_date(query)
        title = "\"" + query + "\" - Search Results"
        return render_template("index.html", films=results, query=query, title=title)

    return redirect(url_for('index'))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_film():
    if request.method == "POST":
        # sanity check
        if not session["admin"]:
            flash("Insufficient privileges to complete this action!", "error")
            render_template("index.html")

        film_name = request.form.get("film-name").title()
        film_desc = request.form.get("film-description")
        film_duration = request.form.get("film-duration")
        hall_number = request.form.get("film-hall")
        film_times = request.form.get("film-times")
        added_by = session["user_id"]

        # sanity check - make sure hall number exists!
        try:
            hall_number = int(hall_number)
        except TypeError:
            flash("Hall must be a positive integer!")
            render_template("add_film.html")

        hall = Hall.nodes.get_or_none(name=hall_number)
        if not hall:
            flash("Sorry, this hall does not exist!", "error")

        # sanity check - make sure number of hours can be changed to timedelta object.
        try:
            film_duration_minutes = int(film_duration)
            film_duration = timedelta(minutes=film_duration_minutes)
        except TypeError:
            flash("Please enter number of minutes as a positive integer!", "error")
            return render_template("add_film.html")

        # sanity check - ensure the entered showings don't collide with each other..
        try:
            showtimes = parse_showtimes(film_times, film_duration)
        except ValueError as e:
            flash("{e}".format(e=e), "error")
            return render_template("add_film.html")

        # check for collisions with pre-existing shows.
        for showtime in showtimes:
            hall = Hall.nodes.get_or_none(name=hall_number)
            collision = collides(hall, showtime, film_duration)
            if collision:
                flash("Sorry, show at {showtime} collides with another!"
                      .format(showtime=showtime.strftime(format="%d/%m/%y %H:%M")),
                      "error")
                for c in collision:
                    flash('{movie} at {time}'.format(movie=c.movie.all()[0].title,
                                                     time=c.start.strftime(format="%H:%M")),
                          "error")
                return render_template("add_film.html")

        # find staff who is creating this.
        staff = Staff.nodes.get(uuid=added_by)

        # check if movie exists
        movie = Movie.nodes.get_or_none(title=film_name)
        if not movie:
            # create movie node
            movie = Movie(title=film_name, description=film_desc, duration=film_duration_minutes).save()

        if not staff.added.is_connected(movie):
            staff.added.connect(movie)

        for showtime in showtimes:
            # create and save node for this showing
            showing = Showing(start=showtime, end=showtime + film_duration, num_available=hall.num_seats).save()

            # connect showing to the hall where it's taking place
            showing.location.connect(hall)

            # connect movie to showing
            movie.showing.connect(showing)

            movie.refresh()
            showing.refresh()

        # clear search cache
        lookup.cache = {}

    return render_template("add_film.html")


@app.route("/<string:title>/showings", methods=["GET"])
def showings(title):
    movie = Movie.nodes.get_or_none(title=title)

    if not movie:
        return render_template("404.html")

    available = {}
    for showing in movie.showing.order_by("start").all():
        if showing.start > datetime.now(tz=utc) and showing.num_available > 0:
            date = showing.start.strftime(format="%a %d %b")

            if not available.get(date):
                available[date] = []
            available[date].append({"uuid": showing.uuid,
                                    "start": showing.start.strftime(format="%H:%M"),
                                    "reserved": showing.reserved,
                                    "num_available": showing.num_available})

    recommendations = recommends(title)
    if len(recommendations) == 0:
        recommendations = None

    return render_template("showings.html", film=movie, available=available, recommendations=recommendations)


@app.route("/<string:title>/<string:uuid>/book", methods=["GET", "POST"])
@login_required
def book(title, uuid):
    """
    Ticket booking page
    :return:
    """
    # check if title exists
    movie = Movie.nodes.get_or_none(title=title)
    showing = Showing.nodes.get_or_none(uuid=uuid)
    user = Customer.nodes.get_or_none(uuid=session["user_id"])
    if not movie or not showing:
        render_template("404.html")

    hall = showing.location.all()[0]

    if request.method == "POST":
        seat_number = request.form.get("book-seat")

        try:
            seat_number = int(seat_number)

        except ValueError:
            flash("Please enter valid seat number!", "error")
            return redirect(url_for("/{title}/{uuid}/book.html".format(title=title, uuid=uuid)))

        if seat_number in showing.reserved:
            flash("Sorry, seat {seat_number} is already reserved!".format(seat_number=seat_number), "error")
            return redirect(url_for("book", title=title, uuid=uuid))

        showing.reserved.append(seat_number)
        showing.num_available -= 1

        showing.save()
        showing.refresh()

        user.booked.connect(showing, {"seat": seat_number})

        table = {
            "name": " ".join([user.f_name, user.l_name]),
            "movie": movie.title,
            "hall": hall.name,
            "seat": seat_number,
            "time": showing.start.strftime(format="%a %d %b %y @ %H:%M"),
            "duration": str(movie.duration) + " minutes"
        }

        hall_diagram.cache = {}

        recommendations = recommends(title)
        if len(recommendations) == 0:
            recommendations = None

        return render_template("summary.html", table=table, uuid=showing.uuid, recommendations=recommendations)

    rows = 10
    columns = hall.num_seats // rows
    diagram = hall_diagram(hall.name, showing.reserved, row=rows, column=columns)

    show = {"uuid": showing.uuid,
            "start": showing.start.strftime(format="%H:%M"),
            "end": showing.end.strftime(format="%H:%M"),
            "num_available": showing.num_available}

    return render_template("book.html", diagram=diagram, hall=hall, film=movie, show=show, maximum=hall.num_seats)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page for Customers.
    :return:
    """
    session.clear()  # Forget any user_id

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed = None

        # Check if password given. If not, redirect to login page with error message.
        if password:
            hashed = hash_password(password)  # hash password

        else:
            flash("No password given!", "error")
            render_template("login.html")

        user = Customer.nodes.get_or_none(username=username, password=hashed)

        if user:
            session["user_id"] = user.uuid
            session["username"] = user.username
            session["admin"] = False
            flash("Welcome back, {user}!".format(user=user.f_name), "notification")
            return redirect(url_for("index"))

        else:
            flash("Username or password incorrect!", "error")
            render_template("login.html")
    return render_template("login.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    """
    Login page for Staff
    :return:
    """
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if password given. If not, redirect to login page with error message.
        if password:
            hashed = hash_password(password)  # hash password

        else:
            flash("No password given!", "error")
            return render_template("admin.html")

        user = Staff.nodes.get_or_none(username=username, password=hashed)

        if user:
            session["user_id"] = user.uuid
            session["username"] = user.username
            session["admin"] = True
            return redirect(url_for("index"))

        else:
            flash("Username or password incorrect!", "error")
            return render_template("admin.html")
    return render_template("admin.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        errors = False
        f_name = request.form.get("fname").title()
        l_name = request.form.get("lname").title()
        username = request.form.get("username")
        password = request.form.get("password")
        repeat_password = request.form.get("repeat-password")
        hashed = None

        if password and repeat_password and repeat_password == password:
            hashed = hash_password(password)

        # If something is wrong with the password.
        else:
            flash("Passwords do not match. Please try again.", "error")
            errors = True

        if Customer.nodes.get_or_none(username=username):
            flash("This username already exists! Please choose another. \n", "error")
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
            flash("Welcome, {user}. You have been registered and logged in.".format(user=new_user.f_name),
                  "notification")
            return redirect(url_for("index"))

        else:
            return render_template("register.html")
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect((url_for("index")))


@app.route("/unregister", methods=["GET", "POST"])
@login_required
def unregister():
    return render_template("404.html")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """
    Allows customer to change their details. Needs password.
    :return:
    """
    username = session["username"]
    user = Customer.nodes.get(username=username)

    if request.method == "POST":
        f_name = request.form.get("fname")
        l_name = request.form.get("lname")
        email = request.form.get("email")
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")
        repeated_password = request.form.get("repeat-password")

        if hash_password(old_password) != user.password:
            flash("Incorrect Password!", "error")
            return render_template("profile.html", user=user)

        user.f_name = f_name
        user.l_name = l_name
        user.email = email

        if len(new_password) > 0 and new_password == repeated_password:

            # if the new password is not repeated properly.
            if new_password != repeated_password:
                flash("Sorry, passwords do not match", "error")
                return render_template("profile.html", user=user)

            flash("Password changed.", "notification")
            user.password = hash_password(new_password)

        user.save()
        user.refresh()
        flash("Details updated.", "notification")

    user = user.serialize
    return render_template("profile.html", user=user)


@app.route("/history", methods=["GET"])
@login_required
def history():
    """

    :return:
    """

    username = session.get("username")
    items = user_history(username)
    return render_template("history.html", history=items)


@app.route("/cancel/<string:uuid>/<int:seat>")
@login_required
def cancel(uuid, seat):
    """

    :param uuid:
    :param seat:
    :return:
    """
    user = Customer.nodes.get(uuid=session["user_id"])
    showing = Showing.nodes.get(uuid=uuid)

    # seat is now free for other Customers to book
    showing.reserved.remove(seat)
    showing.num_available += 1

    # change relationship details
    cancel_booking(showing.uuid, user.uuid, int(seat))

    showing.save()
    hall_diagram.cache = {}

    return redirect(url_for("history"))


@app.route("/export")
@login_required
def export():
    if not session.get("admin"):
        flash("403. Insufficient privileges to complete this action.", "error")
        return redirect(url_for("index"))

    exports = []

    movies = Movie.nodes.order_by("title").all()
    for movie in movies:
        title = movie.title
        shows = movie.showing.all()
        for show in shows:
            details = dict()
            details["title"] = title
            details["start"] = show.start.strftime(format="%d/%m/%y,%H:%M")
            details["num_available"] = show.num_available
            details["num_reserved"] = len(show.reserved)
            exports.append(details)

    return render_template("exports.html", exports=exports)


@app.route("/about", methods=["GET"])
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
