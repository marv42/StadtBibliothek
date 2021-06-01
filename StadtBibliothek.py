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
        'type': 'K'}
COOKIES_FILE = "cookies.pickle"


def get_data_with_target(target):
    data = DATA
    data['target'] = target
    return data


def get_html():
    cookies = handle_cookies()
    data = get_data_with_target('konto')
    result = requests.post(OPAC_URL, data=data, cookies=cookies)
    return result.text


def handle_cookies():
    cookies = load_cookies()
    data = get_data_with_target('konto')
    logging.info(f"{len(cookies)} cookies")
    result = requests.post(OPAC_URL, data=data, cookies=cookies)
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


def get_books():
    html = get_html()
    parsed_html = BeautifulSoup(html, 'lxml')
    list_of_books = []
    one_book = []
    all_tds = parsed_html.find_all("td")
    for td in all_tds:
        match = re.search(r'>(.*)</td>', str(td))
        content = match.group(1)
        one_book.append(content)
        if "a href" in content:
            list_of_books.append(one_book)
            one_book = []
    return list_of_books


def get_first_date(something):
    match = re.search(r'\d{2}\.\d{2}\.\d{4}', str(something))
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


def extend_books(books, end_date):
    result = ""
    for book in books:
        if book[2] == end_date:
            result += try_extend_book(book)
    return result


def try_extend_book(book):
    name_and_author = get_name_and_author(book)
    if "Verlängern" in book[3]:
        extend()
        return f"Erfolgreich verlängert: {name_and_author}\n"
    else:
        return f"Konnte nicht mehr verlängert werden: {name_and_author}. ABGEBEN!\n"


def get_name_and_author(book):
    return f"{book[1]} ({book[0]})"


def extend():
    cookies = load_cookies()
    data = get_data_with_target('verl_1')
    requests.post(OPAC_URL, data=data, cookies=cookies)
    data = get_data_with_target('make_vl')
    requests.post(OPAC_URL, data=data, cookies=cookies)


def list_books(books):
    book_list = "Alle Bücher:\n"
    for book in books:
        book_list += book[2] + ": " + get_name_and_author(book) + "\n"
    return book_list


def main():
    logging.basicConfig(level=DEBUG)
    books = get_books()
    first_date = get_first_date(books)
    if first_date and is_in_less_than_x_days(first_date, WARN_DAYS_IN_ADVANCE):
        mail_body = f"... am {first_date.strftime('%d.%m.')} (in weniger als {WARN_DAYS_IN_ADVANCE} Tagen).\n" \
                    f"(Zum Verlängern: http://opac.st-ingbert.de/webopac/index.asp?kontofenster=start)\n\n"
        mail_body += extend_books(books, books[0][2]) + "\n"
        mail_body += list_books(books)
        send_mail("Bücher laufen ab", mail_body)


if __name__ == "__main__":
    main()
