from datetime import datetime
from itertools import chain

from mongoengine import (connect, DateTimeField, Document,
        IntField, ReferenceField, StringField)

connect('kayak')

def group_n(i, n):
    while True:
        current, i = i[:n], i[n:]
        if not current:
            break
        assert len(current) == n
        yield current

def date_from_iso(dt_str):
    return datetime.strptime(dt_str, '%Y-%m-%d').date()

def str_to_legs(legs_str):
    for ends, date_str in group_n(legs_str.split('/'), 2):
        origin, dest = ends.split('-')
        date_ = date_from_iso(date_str)
        yield (origin, dest, date_)

def legs_to_str(legs):
    def leg_parts():
        for origin, dest, date_ in legs:
            ends = '-'.join((origin, dest))
            date_str = date_.isoformat()
            yield ends, date_str
    return '/'.join(chain.from_iterable(leg_parts()))


class Plan(Document):
    name = StringField()
    legs_str = StringField(required=True)

    @property
    def itinerary_set(self):
        return Itinerary.objects.filter(plan=self)

    @property
    def quote_set(self):
        return Quote.objects.filter(plan=self)

    @property
    def legs(self):
        return str_to_legs(self.legs_str)

    @staticmethod
    def leg_friendly(origin, dest, dt):
        return '{o} -> {d} on {dt}'.format(
                o=origin, d=dest, dt=dt.strftime('%a %d %b'))

    @property
    def legs_friendly(self):
        return ', '.join(self.leg_friendly(*f) for f in self.legs)

    @property
    def url(self):
        url_parts = ['http://www.kayak.co.uk/flights', self.legs_str, '2adults']
        return '/'.join(url_parts)


class Itinerary(Document):
    plan = ReferenceField(Plan, required=True)
    flights = StringField(required=True)

    @property
    def flights_friendly(self):
        return '\n'.join(
                ' '.join(f) for f in group_n(self.flights.split('\n'), 6))

    meta = {
            'indexes': [
                {'fields': ('plan', 'flights'), 'unique': True},
                ]
            }

    @property
    def quote_set(self):
        return Quote.objects.filter(itinerary=self)


class Quote(Document):
    plan = ReferenceField(Plan, required=True)
    itinerary = ReferenceField(Itinerary, required=True)
    price = IntField(required=True)
    position = IntField(required=True)
    collected_dt = DateTimeField(required=True, default=datetime.now)

    meta = {
            'indexes': [
                {'fields': ('itinerary', 'collected_dt')},
                ]
            }
