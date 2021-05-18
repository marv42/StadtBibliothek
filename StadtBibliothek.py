import logging
from logging import DEBUG
import pickle
import re
from subprocess import Popen, PIPE
from datetime import timedelta, datetime

import requests
from bs4 import BeautifulSoup
from LoginData import CARD_NUMBER, PASSWORD, MAIL_ADDRESS

WARN_DAYS_IN_ADVANCE = 7
OPAC_URL = "http://opac.st-ingbert.de/webopac/index.asp"
DATA = {'kontofenster': 'true',
        'AUSWEIS': CARD_NUMBER,
        'PWD': PASSWORD,
        'B1': '%A0%A0%A0Weiter%A0%A0%A0',
        'target': 'konto',
        'type': 'K'}
COOKIES_FILE = "cookies.pickle"


def get_html():
    cookies = handle_cookies()
    result = requests.post(OPAC_URL, data=DATA, cookies=cookies)
    return result.text


def handle_cookies():
    cookies = load_cookies()
    result = requests.post(OPAC_URL, data=DATA, cookies=cookies)
    add_new_cookies(cookies, result.cookies)
    save_cookies(cookies)
    logging.debug(cookies)
    return cookies


def load_cookies():
    with open(COOKIES_FILE, 'rb') as f:
        return pickle.load(f)


def save_cookies(cookies):
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(cookies, f)


def add_new_cookies(cookies, result_cookies):
    new_cookies = result_cookies.items()
    for cookie in new_cookies:
        cookies[cookie[0]] = cookie[1]


def get_books(html):
    return html.find_all("td")


def get_first_date(books):
    match = re.search(r'\d{2}\.\d{2}\.\d{4}', str(books))
    if match:
        return datetime.strptime(match.group(0), "%d.%m.%Y")
    return None


def is_in_less_than_x_days(date_in_question, x):
    today = datetime.today()
    return today + timedelta(days=x) > date_in_question


def send_mail(subject, body=''):
    command = ["mail", "-s", subject, MAIL_ADDRESS]
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate(body.encode())
    return_code = process.returncode
    if return_code != 0:
        logging.error(f"Error sending mail: return code: {return_code}, stderr: {stderr}")


def main():
    # logging.basicConfig(level=DEBUG)
    html = get_html()
    parsed_html = BeautifulSoup(html, 'lxml')
    books = get_books(parsed_html)
    first_date = get_first_date(books)
    if first_date and is_in_less_than_x_days(first_date, WARN_DAYS_IN_ADVANCE):
        send_mail("Bücher laufen ab", f"... am {first_date.strftime('%d. %m.')} (in weniger als {WARN_DAYS_IN_ADVANCE} Tagen).\nZum Verlängern: http://opac.st-ingbert.de/webopac/index.asp?kontofenster=start")


if __name__ == "__main__":
    main()
