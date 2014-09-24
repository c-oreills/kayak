from datetime import datetime, timedelta
import sys
from time import sleep
from traceback import format_tb, print_tb

from selenium import webdriver
from selenium.common import exceptions

from models import Itinerary, Plan, Quote
from mailer import sendmail
from potential_plans import ensure_plans

NOISY = False
HEADLESS = True

browser = None
display = None
last_checkin = datetime.now()

def set_browser():
    global browser, display
    if HEADLESS:
        from pyvirtualdisplay import Display

        display = Display(visible=0, size=(800, 600))
        display.start()
    browser = webdriver.Firefox()

def unset_browser():
    if browser:
        browser.quit()
    if display:
        display.stop()

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
        try:
            nth_el = content_div.find_element_by_xpath('./*[{index}]'.format(index=index))

            price_el = nth_el.find_element_by_class_name('results_price')
            price = price_el.text[1:]

            flight_holder_el = nth_el.find_element_by_class_name('legholder')
            flights = flight_holder_el.text
        except exceptions.NoSuchElementException:
            print 'Could not find price', n, 'for', plan.legs_friendly
            return None, None

        price = int(float(price))
        return price, flights

    for position in (1, 2, 3):
        price, flights = nth_cheapest(position)
        if not price:
            break
        itinerary, _ = Itinerary.objects.get_or_create(
                flights=flights, plan=plan)
        quote = Quote.objects.create(
                plan=plan, itinerary=itinerary, price=price, position=position)

        if position == 1:
            if NOISY:
                term_display(plan, itinerary, quote)
            send_price_email(plan, itinerary, quote)

def term_display(plan, itinerary, quote):
    print plan.legs_friendly
    print quote.price, 'quid'
    print itinerary.flights_friendly
    print

def send_price_email(plan, itinerary, quote):
    quotes = plan.quote_set.order_by('-collected_dt').filter(position=1).limit(2)
    if len(quotes) < 2:
        return
    last_quote, sec_last_quote = quotes
    assert last_quote.id == quote.id
    if last_quote.price >= sec_last_quote.price:
        return

    term_display(plan, itinerary, quote)
    price_diff = sec_last_quote.price - last_quote.price
    if price_diff < 3:
        print 'Only a bit cheaper, probably exchange rate, ignorez'
        return
    print 'Cheaper, sending mail'
    subject = '{pd} quid drop in {l}'.format(pd=price_diff, l=plan.legs_friendly)

    body = '\n'.join((
        '{p} quid (was {pp})'.format(p=quote.price, pp=sec_last_quote.price),
        itinerary.flights_friendly,))

    sendmail(subject, body)

def error_mail(plan, e, tb):
    subject = 'Error: {e}'.format(e=e)
    body = '\n'.join([
        plan.legs_friendly,
        format_tb(tb)
        ])
    sendmail(subject, body)

def checkin_mail():
    global last_checkin
    if datetime.now() - last_checkin < timedelta(1):
        return
    last_checkin = datetime.now()
    sendmail('Just checkin\' in ', 'I\'m still alive and checking flights for ye! =)')

def safe_get_quotes(plan):
    try:
        get_quotes(plan)
    except Exception, e:
        print 'Caught exception processing', plan.legs_friendly
        _, _, tb = sys.exc_info()
        print_tb(tb)
        print e
        try:
            error_mail(plan, e, tb)
        except Exception, e:
            print 'Oh error mail!', e
            _, _, tb = sys.exc_info()
            print_tb(tb)

def run():
    ensure_plans()
    attempt = 0
    while True:
        try:
            set_browser()
            for plan in Plan.objects.all():
                safe_get_quotes(plan)
        except Exception, e:
            attempt += 1
            print 'Caught exception in main loop, trying again:', e
        else:
            attempt = 0
            print 'Checkin:', datetime.now()
            checkin_mail()
            sleep(60*60)
        finally:
            try:
                unset_browser()
            except Exception, e:
                print 'Exception trying to unset browser', e

if __name__ == '__main__':
    run()
