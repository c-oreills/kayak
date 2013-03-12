from time import sleep

from selenium import webdriver
from selenium.common import exceptions

from models import Itinerary, Plan, Quote
from potential_plans import ensure_plans

browser = webdriver.Firefox()

def get_quotes(plan):
    browser.get(plan.url)
    while True:
        try:
            browser.find_element_by_id('progressDiv')
        except exceptions.NoSuchElementException:
            break
        else:
            sleep(1)
    content_div = browser.find_element_by_id('content_div')

    def nth_cheapest(n):
        index = n + 1
        nth_el = content_div.find_element_by_xpath('./*[{index}]'.format(index=index))

        price_el = nth_el.find_element_by_class_name('results_price')
        price = price_el.text[1:]

        flight_holder_el = nth_el.find_element_by_class_name('legholder')
        flights = flight_holder_el.text

        price = int(float(price))
        return price, flights

    for position in (1, 2, 3):
        price, flights = nth_cheapest(position)
        itinerary, _ = Itinerary.objects.get_or_create(
                flights=flights, plan=plan)
        Quote.objects.create(
                itinerary=itinerary, price=price, position=position)

        if position == 1:
            print plan.legs_friendly
            print price, 'quid'
            print itinerary.flights_friendly
            print

def safe_get_quotes(plan):
    try:
        get_quotes(plan)
    except Exception, e:
        print 'Caught exception processing', plan.legs_friendly, e

def run():
    while True:
        ensure_plans()
        for plan in Plan.objects.all():
            safe_get_quotes(plan)
        sleep(60*60)

if __name__ == '__main__':
    run()
