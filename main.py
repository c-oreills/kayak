from time import sleep

from selenium import webdriver
from selenium.common import exceptions

from models import Itinerary, Plan, Quote
from potential_plans import ensure_plans

try:
    from email_creds import EMAIL_CREDENTIALS, TO_ADDRS
except ImportError:
    EMAIL_CREDENTIALS = None
else:
    import libgmail
    mail_account = libgmail.GmailAccount(*EMAIL_CREDENTIALS)

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
        quote = Quote.objects.create(
                itinerary=itinerary, price=price, position=position)

        if position == 1:
            display(plan, itinerary, quote)
            send_email(plan, itinerary, quote)

def display(plan, itinerary, quote):
    print plan.legs_friendly
    print quote.price, 'quid'
    print itinerary.flights_friendly
    print

def send_email(plan, itinerary, quote):
    if not EMAIL_CREDENTIALS:
        print 'No email creds, skipping'
        return
    quotes = itinerary.quote_set.order_by('-collected_dt').limit(2)
    if len(quotes) < 2:
        return
    last_quote, sec_last_quote = quotes
    assert last_quote.id == quote.id
    if last_quote.price >= sec_last_quote.price:
        return

    print 'Cheaper, sending mail'
    to_addrs = '; '.join(TO_ADDRS)
    price_diff = sec_last_quote.price - last_quote.price
    subject = '£{pd} drop in {l}'.format(pd=price_diff, l=plan.legs_friendly)

    body = '\n'.join((
        '£{p} (was £{pp})'.format(p=quote.price, pp=sec_last_quote.price),
        itinerary.flights_friendly,))

    message = libgmail.GmailComposedMessage(
            to=to_addrs,
            subject=subject,
            body=body)
    mail_account.sendMessage(message)

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
