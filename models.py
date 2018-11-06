from neomodel import StructuredNode, StringProperty, UniqueIdProperty, DateTimeProperty, IntegerProperty, BooleanProperty,\
    ArrayProperty, StructuredRel, RelationshipTo, RelationshipFrom
from datetime import datetime
import pytz


class Added(StructuredRel):
    time = DateTimeProperty(default=lambda: datetime.now(pytz.utc))


class Booked(StructuredRel):
    time = DateTimeProperty(default=lambda: datetime.now(pytz.utc))
    cancelled = BooleanProperty(default=False)
    cancelled_time = DateTimeProperty()
    seat = IntegerProperty(required=True)


class Staff(StructuredNode):
    uuid = UniqueIdProperty()
    username = StringProperty(unique_index=True)
    password = StringProperty(required=True)
    f_name = StringProperty(required=True)
    l_name = StringProperty(required=True)

    added = RelationshipTo("Movie", "ADDED", model=Added)

    @property
    def serialize(self):
        result = {
            "username": self.username,
            "password": self.password,
            "f_name": self.f_name,
            "l_name": self.l_name
        }
        return result


class Customer(StructuredNode):
    uuid = UniqueIdProperty()
    username = StringProperty(unique_index=True)
    password = StringProperty(required=True)
    f_name = StringProperty(required=True)
    l_name = StringProperty(required=True)
    email = StringProperty(default="")

    booked = RelationshipTo("Showing", "BOOKED", model=Booked)

    @property
    def serialize(self):
        result = {
            "username": self.username,
            "password": self.password,
            "f_name": self.f_name,
            "l_name": self.l_name,
            "email": self.email
        }
        return result


class Movie(StructuredNode):
    uuid = UniqueIdProperty()
    title = StringProperty(required=True)
    description = StringProperty(required=True)
    duration = IntegerProperty(required=True)

    showing = RelationshipTo("Showing", "SHOWING")


class Showing(StructuredNode):
    uuid = UniqueIdProperty()
    start = DateTimeProperty(required=True)
    end = DateTimeProperty(required=True)
    reserved = ArrayProperty(default=[])
    num_available = IntegerProperty(required=True)

    location = RelationshipTo("Hall", "IN")
    movie = RelationshipFrom("Movie", "SHOWING")

    @property
    def serialize(self):
        return {"start": self.start, "end": self.end, "reserved": self.reserved, "num_available": self.num_available}


class Hall(StructuredNode):
    uuid = UniqueIdProperty()
    name = IntegerProperty(unique_index=True)
    num_seats = IntegerProperty(required=True)

    shows = RelationshipFrom("Showing", "IN")

    @property
    def serialize(self):
        return {"name": self.name, "num_seats": self.num_seats}
