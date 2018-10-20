import requests
from bs4 import BeautifulSoup as Soup
import dateparser
from models import Transaction
from database import db_session, init_db
from flask import jsonify
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
config = config['AIB']
init_db()
URL = 'https://onlinebanking.aib.ie/inet/roi/login.htm?'
STATEMENT_URL = 'https://onlinebanking.aib.ie/inet/roi/statement.htm'
HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://onlinebanking.aib.ie/inet/roi/login.htm?',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://onlinebanking.aib.ie'}
TOKEN_SELECTOR = 'input[id="transactionToken"]'
PASS_LABEL_SELECTOR = 'div[class*="x3-login"] strong'
TABLE_SELECTOR = 'table[class="transaction-table"]'
DATE_SELECTOR = 'strong'
TRANSACTION_SELECTOR = 'td[class="forceWrap"]'
CREDIT_SELECTOR = 'td[class="alignr credit"]'
DEBIT_SELECTOR = 'td[class="alignr debit"]'
PASSWORD = [config['dig1'], config['dig2'], config['dig3'], config['dig4'], config['dig5']]
session = requests.Session()


def build_password(page):
    positions = [0,0,0]
    for i in range(0, 3):
        digit = page.select(PASS_LABEL_SELECTOR)[i].text
        positions[i] = [int(s) for s in digit.split() if s.isdigit()][0]
    password_digits = [PASSWORD[i-1] for i in positions]
    return password_digits


def login():
    response = session.get(URL, verify=False)

    #first login post, reg number
    soup = Soup(response.text, "html.parser")
    reg_num_data = dict(jsEnabled=False, _target1=True, transactionToken=soup.select(TOKEN_SELECTOR)[0]['value'], regNumber=config['regNumber'])
    response = session.post(URL, data=reg_num_data, verify=False, headers=HEADERS)

    #second login post, passphrase
    soup = Soup(response.text, "html.parser")
    password = build_password(soup)
    pass_num_data = dict(jsEnabled=False, _finish=True, transactionToken=soup.select(TOKEN_SELECTOR)[0]['value'])
    for i in range(0,3):
        pass_num_data['pacDetails.pacDigit{}'.format(i+1)] = password[i]
    response = session.post(URL, data=pass_num_data, verify=False, headers=HEADERS)

    return response


def get_transactions():
    response = login()
    soup = Soup(response.text, "html.parser")
    transaction_data = dict(jsEnabled=False, transactionToken=soup.select(TOKEN_SELECTOR)[0]['value'], index=0, displayExportRecentTransactions = 'true')
    response = session.post(STATEMENT_URL, data=transaction_data, verify=False, headers= HEADERS)
    return response

def parse_transactions():
    response = get_transactions()
    soup = Soup(response.text, "html.parser")
    soup = soup.select(TABLE_SELECTOR)[1]
    rows = soup.find_all('tr')
    transaction_list = []
    for row in rows:

        if row.select(DATE_SELECTOR):
            date = dateparser.parse(row.select(DATE_SELECTOR)[0].text)
        if row.select(TRANSACTION_SELECTOR):
            payee = row.select(TRANSACTION_SELECTOR)[0].text
            if row.select(DEBIT_SELECTOR):
                debit = (row.select(DEBIT_SELECTOR)[0].text)
                print('\n' + str(date) + ' {}: {}'.format(payee, debit))
                transaction = Transaction(payee, abs(float(debit)), True, date)
                db_session.add(transaction)
                transaction_list.append(transaction.as_dict())
            if row.select(CREDIT_SELECTOR):
                credit = row.select(CREDIT_SELECTOR)[0].text
                print ('\n'+str(date)+' {}: {}'.format(payee, credit))
                transaction = Transaction(payee, abs(float(credit)), False, date)
                db_session.add(transaction)
                transaction_list.append(transaction.as_dict())

    return transaction_list

def save_transactions():
    list = parse_transactions()
    db_session.commit()
    return jsonify(list)