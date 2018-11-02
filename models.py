from neomodel import StructuredNode, StringProperty, UniqueIdProperty, DateTimeProperty, IntegerProperty,\
    ArrayProperty, StructuredRel, RelationshipTo, RelationshipFrom
from datetime import datetime, timedelta
import pytz


class Added(StructuredRel):
    time = DateTimeProperty(default=lambda: datetime.now(pytz.utc))


class Booked(StructuredRel):
    time = DateTimeProperty(default=lambda: datetime.now(pytz.utc))

    hall = StringProperty(required=True)
    seat = StringProperty(required=True)


class Cancelled(StructuredRel):
    time = DateTimeProperty(default=lambda: datetime.now(pytz.utc))


class ShowingIn(StructuredRel):
    duration = DateTimeProperty(default=lambda: timedelta(hours=1))


class Staff(StructuredNode):
    uuid = UniqueIdProperty()
    username = StringProperty(unique_index=True)
    password = StringProperty(required=True)
    f_name = StringProperty(required=True)
    l_name = StringProperty(required=True)

    added = RelationshipTo("Movie", "ADDED", model=Added)


class Customer(StructuredNode):
    uuid = UniqueIdProperty()
    username = StringProperty(unique_index=True)
    password = StringProperty(required=True)
    f_name = StringProperty(required=True)
    l_name = StringProperty(required=True)
    email = StringProperty()

    booked = RelationshipTo("Movie", "BOOKED", model=Booked)
    cancelled = RelationshipTo("Movie", "CANCELLED", model=Cancelled)


class Movie(StructuredNode):
    uuid = UniqueIdProperty()
    title = StringProperty(required=True)
    description = StringProperty(required=True)
    duration = DateTimeProperty

    location = RelationshipTo("Hall", "IN", model=ShowingIn)


class Hall(StructuredNode):
    uuid = UniqueIdProperty()
    name = StringProperty(unique_index=True)
    num_seats = IntegerProperty(required=True)
    reserved = ArrayProperty(required=True)

    showing = RelationshipFrom("Movie", "IN", model=ShowingIn)
