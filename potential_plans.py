from datetime import date

from models import legs_to_str, Plan

def ensure_plans():
    for first_day in (12, 13):
        for last_day in (2, 3):
            ensure_plan((
                ('LON', 'NYC', date(2013, 7, first_day)),
                ('NYC', 'LAS', date(2013, 7, 20)),
                ('LAX', 'LON', date(2013, 8, last_day))
            ))

def ensure_plan(legs):
    legs_str = legs_to_str(legs)
    Plan.objects.get_or_create(legs_str=legs_str)
