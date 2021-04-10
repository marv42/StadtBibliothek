import re
import subprocess
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from LoginData import CARD_NUMBER, PASSWORD, COOKIES, MAIL_ADDRESS

WARN_DAYS_IN_ADVANCE = 3
OPAC_URL = "http://opac.st-ingbert.de/webopac/index.asp"
DATA = {'kontofenster': 'true',
        'AUSWEIS': CARD_NUMBER,
        'PWD': PASSWORD,
        'B1': '%A0%A0%A0Weiter%A0%A0%A0',
        'target': 'konto',
        'type': 'K'}


def get_html():
    result = requests.post(OPAC_URL, data=DATA, cookies=COOKIES)
    return result.text


def get_books(html):
    return html.find_all("td")


def get_first_date(books):
    match = re.search(r'\d{2}\.\d{2}\.\d{4}', str(books))
    if match:
        return match.group(0)
    return None


def is_in_less_than_x_days(date_in_question, x):
    today = date.today()
    return today + timedelta(days=x) > date_in_question


html = get_html()
parsed_html = BeautifulSoup(html)
books = get_books(parsed_html)
first_date = get_first_date(books)

if first_date and is_in_less_than_x_days(first_date, WARN_DAYS_IN_ADVANCE):
    subprocess.run(["mail", "-s", f"Bücher laufen in {WARN_DAYS_IN_ADVANCE} Tagen ab", MAIL_ADDRESS])
