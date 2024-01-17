#!/usr/bin/env python3

import logging
from logging import DEBUG
import re
from subprocess import Popen, PIPE
from datetime import timedelta, datetime

import requests
from bs4 import BeautifulSoup
from LoginData import CARD_NUMBER, PASSWORD, MAIL_ADDRESS

WARN_DAYS_IN_ADVANCE = 3
OPAC_URL = "http://opac.st-ingbert.de/webopac/index.asp"
DATA = {'kontofenster': 'true',
        'AUSWEIS': CARD_NUMBER,
        'PWD': PASSWORD,
        'B1': '%A0%A0%A0Weiter%A0%A0%A0',
        'type': 'K'}
EXTEND_SUCCESS = "Erfolgreich verlängert"

cookies = {}


def post_request(target):
    data = get_data_with_target(target)
    result = requests.post(OPAC_URL, data=data, cookies=cookies)
    return result


def get_data_with_target(target):
    data = DATA
    data['target'] = target
    return data


def get_html():
    result = post_request('konto')
    return result.text


def retrieve_cookies():
    result = post_request('konto')
    global cookies
    cookies = result.cookies


def get_books():
    html = get_html()
    parsed_html = BeautifulSoup(html, 'lxml')
    list_of_books = []
    one_book = []
    all_tds = parsed_html.find_all("td")
    for td in all_tds:
        match = re.search(r'>(.*)</td>', str(td))
        content = match.group(1)
        content = content.encode("ISO-8859-1").decode("UTF-8")
        one_book.append(content)
        if len(one_book) == 4:
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


def extend_books(books):
    return extend_books_with_new_list_of_books(books, "")


def extend_books_with_new_list_of_books(books, result):
    for b in range(len(books)):
        day_of_book = get_first_date(books[b])
        if is_in_less_than_x_days(day_of_book, WARN_DAYS_IN_ADVANCE):
            extend_result = try_extend_book(books[b], b + 1)
            if extend_result not in result:
                result += extend_result
            if extend_result.startswith(EXTEND_SUCCESS):
                books = get_books()
                result = extend_books_with_new_list_of_books(books, result)
                break
    return result


def try_extend_book(book, number_of_book):
    name_and_author = get_name_and_author(book)
    if "target=verl_" in book[3]:
        extend(number_of_book)
        return f"{EXTEND_SUCCESS}: {name_and_author}\n"
    else:
        return f"Konnte nicht mehr verlängert werden: {name_and_author}. ABGEBEN!\n"


def get_name_and_author(book):
    return f"{book[1]} ({book[0]})"


def extend(number_of_book):
    post_request(f"verl_{number_of_book}")
    post_request('make_vl')


def list_books(books):
    book_list = "Alle Bücher:\n"
    for book in books:
        book_list += book[2] + ": " + get_name_and_author(book) + "\n"
    book_list += str(len(books)) + " Bücher\n"
    return book_list


def main():
    logging.basicConfig(level=DEBUG)
    try:
        retrieve_cookies()
    except requests.exceptions.ConnectionError as e:
        send_mail("Stadtbibliothek nicht erreichbar", str(e.args))
    books = get_books()
    first_date = get_first_date(books)
    if first_date and is_in_less_than_x_days(first_date, WARN_DAYS_IN_ADVANCE):
        mail_body = f"... am {first_date.strftime('%d.%m.')} (in weniger als {WARN_DAYS_IN_ADVANCE} Tagen).\n" \
                    f"(Zum Verlängern: http://opac.st-ingbert.de/webopac/index.asp?kontofenster=start)\n\n"
        mail_body += list_books(books) + "\n"
        mail_body += extend_books(books)
        send_mail("Bücher laufen ab", mail_body)


if __name__ == "__main__":
    main()
