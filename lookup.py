from models import Movie
from neomodel import db


def lookup(query, order_by=None):
    if query in lookup.cache:
        return lookup.cache[query]

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

    movies = [Movie.inflate(row[0]) for row in movies]  # List of Topic Nodes
    lookup.cache[query] = movies

    return movies


lookup.cache = {}
