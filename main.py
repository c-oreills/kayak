from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.common import exceptions

browser = webdriver.Firefox()

def group_n(i, n):
    while True:
        current, i = i[:n], i[n:]
        if not current:
            break
        assert len(current) == n
        yield current

class Plan(object):
    def __init__(self, *flights):
        self.flights = flights

    @staticmethod
    def flight_url_part(origin, dest, dt):
        return '{o}-{d}/{dt}'.format(o=origin, d=dest, dt=dt.date().isoformat())

    @staticmethod
    def flight_friendly(origin, dest, dt):
        return '{o} -> {d} on {dt}'.format(
                o=origin, d=dest, dt=dt.strftime('%a %d %b'))

    @property
    def url(self):
        url_parts = ['http://www.kayak.co.uk/flights']
        url_parts.extend(self.flight_url_part(*f) for f in self.flights)
        url_parts.append('2adults')
        return '/'.join(url_parts)

    @property
    def friendly(self):
        return ', '.join(self.flight_friendly(*f) for f in self.flights)

    def get_cheapest(self, display=True):
        browser.get(self.url)
        while True:
            try:
                browser.find_element_by_id('progressDiv')
            except exceptions.NoSuchElementException:
                break
            else:
                sleep(1)
        content_div= browser.find_element_by_id('content_div')
        first_el = content_div.find_element_by_xpath('./*[2]')
        price_el = first_el.find_element_by_class_name('results_price')
        price = price_el.text[1:]
        leg_holder_el = first_el.find_element_by_class_name('legholder')
        legs = leg_holder_el.text.split('\n')

        self.cheapest_price = int(price)
        self.cheapest_legs = legs
        if display:
            self.display()

    def display(self):
        print self.friendly
        print self.cheapest_price, 'quid'
        print self.friendly_legs
        print

    @property
    def friendly_legs(self):
        return '\n'.join(
                ' '.join(leg) for leg in group_n(self.cheapest_legs, 6))


PLAN_FF = Plan(
        ('LON', 'NYC', datetime(2013, 7, 12)),
        ('NYC', 'LAS', datetime(2013, 7, 20)),
        ('LAX', 'LON', datetime(2013, 8, 2)))

PLAN_FS = Plan(
        ('LON', 'NYC', datetime(2013, 7, 12)),
        ('NYC', 'LAS', datetime(2013, 7, 20)),
        ('LAX', 'LON', datetime(2013, 8, 3)))

PLAN_SF = Plan(
        ('LON', 'NYC', datetime(2013, 7, 13)),
        ('NYC', 'LAS', datetime(2013, 7, 20)),
        ('LAX', 'LON', datetime(2013, 8, 2)))

PLAN_SS = Plan(
        ('LON', 'NYC', datetime(2013, 7, 13)),
        ('NYC', 'LAS', datetime(2013, 7, 20)),
        ('LAX', 'LON', datetime(2013, 8, 3)))

PLANS = [PLAN_FF, PLAN_FS, PLAN_SF, PLAN_SS]

for plan in PLANS:
    plan.get_cheapest()
