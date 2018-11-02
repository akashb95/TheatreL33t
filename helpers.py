from functools import wraps
from flask import session, redirect, url_for, request
from hashlib import sha256


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


def parse_showtimes(screen, times):

    return


def check_collisions(screen, dt):

    return
