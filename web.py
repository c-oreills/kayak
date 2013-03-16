from json import dumps
from time import mktime

from flask import Flask, render_template

from models import Plan

app = Flask(__name__)
#app.debug = True

def get_series(plan):
    series = [{
        'data': [[1000 * int(mktime(q.collected_dt.timetuple())), q.price] for q in i.quote_set],
        'label': i.flights_friendly}
            for i in plan.itinerary_set]
    return series

@app.route('/')
def all_plans():
    plans = Plan.objects.all()
    series = {p: dumps(get_series(p)) for p in plans}
    return render_template('plans.html',
            plans=plans, series=series)

if __name__ == '__main__':
    app.run()
