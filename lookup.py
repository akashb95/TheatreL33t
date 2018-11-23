from models import Movie
from neomodel import db
from datetime import datetime, timedelta
from pytz import utc


def lookup(query, order_by=None):
    # if query in lookup.cache:
    #     return lookup.cache[query]

    # Cypher command to match query string that starts with given string, ignoring case.
    cypher_command = """
                        MATCH (n:Movie)
                        WHERE (n.title =~ '(?i).*(?<!\\\\S){q}.*') OR 
                        (n.description =~ '(?i).*(?<!\\\\S){q}.*')
                        RETURN n 
                        """.format(q=query)

    # If order specified, order accordingly
    if order_by and type(order_by) == str:
        cypher_command += "ORDER BY n.{o) ASC".format(o=order_by)

    # Otherwise, order alphabetically
    else:
        cypher_command += "ORDER BY n.title ASC"

    movies, meta = db.cypher_query(cypher_command)

    movies = [Movie.inflate(row[0]) for row in movies]  # List of Movie Nodes
    # lookup.cache[query] = movies

    return movies


lookup.cache = {}


def lookup_by_date(query, order_by=None):
    # check cache first
    # if query in lookup.cache:
    #     return lookup.cache[query]

    try:
        dt_start = datetime.strptime(query, "%d/%m/%y").replace(tzinfo=utc)

    except ValueError:
        return lookup(query, order_by)

    # get 24 hour period of the day
    dt_end = dt_start + timedelta(hours=24)

    # convert to floats
    dt_start = dt_start.timestamp()
    dt_end = dt_end.timestamp()

    # create Cypher command
    cypher_command = """
                        MATCH (n:Showing)-[:SHOWING]-(m:Movie) 
                        WHERE (n.start>={start} AND n.end<{end}) 
                        RETURN m ORDER BY m.title ASC
                        """.format(start=dt_start, end=dt_end)

    movies, meta = db.cypher_query(cypher_command)

    movies = [Movie.inflate(row[0]) for row in movies]  # List of Movie Nodes

    # update cache
    # lookup.cache[query] = movies
    return movies


def user_history(username):
    """
    Run a Cypher command to find all shows Customer has booked/cancelled.
    :param username: str
    :return:
    """
    cypher_command = """MATCH (n:Customer)-[r:BOOKED]-(m:Showing)-[s:SHOWING]-(o:Movie) 
                        WHERE (n.username="{u}") 
                        RETURN r, m , o
                        """.format(u=username)

    cypher_command += "ORDER BY r.time DESC"

    bookings, meta = db.cypher_query(cypher_command)
    if len(bookings) < 0:
        raise LookupError("Sorry, no bookings found for {u}.".format(u=username))

    items = []
    for r in bookings:
        movie_details = r[2]._properties
        show_details = r[1]._properties
        booking_details = r[0]._properties

        action_time = datetime.fromtimestamp(booking_details["time"], tz=utc)
        action_time = action_time.strftime(format="%d/%m/%y @ %H:%M:%S")

        start_time = datetime.fromtimestamp(show_details["start"])
        start_time = start_time.strftime(format="%a %d %b %H:%M")

        cancelled_time = ""
        if booking_details["cancelled"]:
            cancelled_time = datetime.fromtimestamp(booking_details["cancelled_time"], tz=utc)\
                .strftime(format="%d/%m/%y @ %H:%M:%S")

        expired = False
        if datetime.fromtimestamp(show_details["start"], tz=utc) < datetime.now(utc):
            expired = True

        items.append({
            "action_time": action_time,
            "movie_name": movie_details["title"],
            "seat": booking_details["seat"],
            "start_time": start_time,
            "booking_uuid": show_details["uuid"],
            "cancelled": booking_details["cancelled"],
            "cancelled_time": cancelled_time,
            "expired": expired
        })

    return items


def cancel_booking(s_uuid, c_uuid, seat):
    """

    :param s_uuid: str Showing uuid
    :param c_uuid: str Customer uuid
    :param seat: int
    :return:
    """
    now = datetime.now(tz=utc).timestamp()
    command = """
                MATCH (c:Customer)-[r:BOOKED]-(s:Showing) 
                WHERE (s.uuid='{uuid}' AND c.uuid='{c}' AND r.seat={seat})
                SET r.cancelled=true, r.cancelled_time={now}
                RETURN r
                """.format(uuid=s_uuid, c=c_uuid, now=now, seat=seat)

    booking, meta = db.cypher_query(command)

    return booking


def recommends(movie_title, limit=10):
    command = """MATCH (m:Movie)-[:SHOWING]->(:Showing)<-[:BOOKED]-(:Customer)
                        -[popularity:BOOKED]->(:Showing)<-[:SHOWING]-(n:Movie) 
                 WHERE (m.title="{title}" AND NOT (m.title=n.title)) 
                 RETURN n, COUNT(popularity) AS p  
                 ORDER BY p DESC
                 LIMIT {limit}""".format(title=movie_title, limit=limit)

    movies, meta = db.cypher_query(command)
    movies = [Movie.inflate(row[0]) for row in movies]  # List of Movie Nodes
    return movies
