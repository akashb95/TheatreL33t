from functools import wraps
from flask import session, redirect, url_for, request
from hashlib import sha256
from datetime import datetime
from pytz import utc
from models import Hall


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def hash_password(password):
    """
    Encodes password using SHA256 protocol to generate a hash.
    :param password: [str] user entered password.
    :return: [str] digest/hash.
    """
    return sha256(password.encode()).hexdigest()


def parse_showtimes(times, hall_number, duration):
    """

    :param hall_number: int
    :param times: str comma separated datetime strings
    :param duration: timedelta
    :return:
    """
    times_array = times.split(",")
    showtimes_dt = []

    for dt in times_array:
        stripped = dt.strip()
        showtime = datetime.strptime(stripped, "%d/%m/%y %H:%M")
        showtimes_dt.append(showtime.replace(tzinfo=utc))

    # check for collisions with pre-existing shows.
    for showtime in showtimes_dt:
        hall = Hall.nodes.get_or_none(name=hall_number)
        if collides(hall, showtime, duration):
            raise ValueError("Sorry, this film overlaps with another viewing!")

    for i in range(1, len(showtimes_dt)):
        # check if previous showtime for this movie overlaps with the start of the next viewing
        if showtimes_dt[i - 1] + duration > showtimes_dt[i]:
            raise ValueError("Show doesn't end before the next one starts!")

    return showtimes_dt


def collides(hall, dt, duration):
    """

    :param hall: neomodel.Node.Hall
    :param dt: datetime.datetime
    :param duration: datetime.timedelta
    :return: bool
    """

    # check if new film starts before another ends, and whether new film ends after another ends.
    # If true, this is a collision
    collisions = hall.shows.filter(end__gt=dt, start__lt=dt+duration)

    if len(collisions) > 0:
        return True

    return False


def hall_diagram(hall_number, reserved, row=10, column=12, draw=False):
    """

    :param hall_number: int
    :param reserved: List of reserved seat indeces
    :param row: int
    :param column: int
    :param draw: bool
    :return: str
    """
    diagram = hall_diagram.cache.get(hall_number)

    if not diagram:
        diagram = []
        for i in range(row):
            diagram.append([" "] * column)

    for seat_number in reserved:
        r = seat_number // column
        c = seat_number % column
        diagram[r][c] = "R"

    hall_diagram.cache[hall_number] = diagram

    if draw:
        divider = "\n|" + "---|" * column + "\n"
        diagram_str = divider

        for i in range(0, len(diagram)):
            diagram_str += "|"
            for j in range(0, len(diagram[i])):
                diagram_str += "{:^3}|".format(diagram[i][j])
            diagram_str += divider

        return diagram, diagram_str

    return diagram


hall_diagram.cache = {}
