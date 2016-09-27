# coding=utf-8
from __future__ import print_function
import time
import os
import sys
import datetime
from shutil import copyfile
import re
import csv

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import click

TARGET_DATA_FOLDER = os.environ['TARGET_DATA_FOLDER'] if 'TARGET_DATA_FOLDER' in os.environ else '/data'
PAGE_TRANSITION_WAIT = 10  # seconds
DOWNLOAD_TIMEOUT = 20  # seconds


def eprint(*args, **kwargs):
    print("[ERROR]", *args, file=sys.stderr, **kwargs)


def iprint(*args, **kwargs):
    print("[INFO]", *args, **kwargs)
    sys.stdout.flush()


def init_chrome():
    iprint("Starting chrome...")
    chrome_options = webdriver.ChromeOptions()
    d = webdriver.Chrome(chrome_options=chrome_options)
    d.implicitly_wait(PAGE_TRANSITION_WAIT)
    return d


def quit_chrome(d):
    iprint("Closing chrome")
    d.quit()


def click_on(d, xpath):
    iprint("Waiting for " + xpath)
    WebDriverWait(d, PAGE_TRANSITION_WAIT).until(
        EC.element_to_be_clickable((By.XPATH, xpath)))
    iprint("Clicking " + xpath)
    d.find_element_by_xpath(xpath).click()


def wait_for_download(dirname):
    iprint("Waiting for download to finish (by checking the download folder)")
    waiting_time = 0
    sleep_interval = 0.1
    def is_downloaded():
        return os.listdir(dirname) and os.listdir(dirname)[0].endswith(".TAB")
    while waiting_time < DOWNLOAD_TIMEOUT and not is_downloaded():
        time.sleep(sleep_interval)
        waiting_time += sleep_interval

    if waiting_time >= DOWNLOAD_TIMEOUT:
        eprint("Something went wrong, file download timed out")
        sys.exit(1)

def get_angular_val(e, angular_var_name):
    xpath = ".//*[contains(@data-bind,'{}') and contains(@data-bind, 'text:')]".format(angular_var_name)
    elems = e.find_elements_by_xpath(xpath)
    if len(elems) == 1:
        return elems[0].text.strip()
    if len(elems) == 0:
        return ''
    else:
        assert False, 'More elements (n={}) correspond to xpath {}'.format(len(elems), xpath)


def download_with_chrome(
        card_number, expiration_date,
        month, filename):

    d = init_chrome()
    try:
        iprint("Loading login page")
        d.get("https://www.ov-chipkaart.nl/customer-service/self-service/travel-history-anonymous-card.htm")

        iprint("Filling in card details")
        card_chunks = card_number.split('-')
        for input_idx in range(4):
            sel = '.autoTabMediumInput span:nth-child({}) input'.format(input_idx + 1)
            d.find_element_by_css_selector(sel).send_keys(card_chunks[input_idx])
        d.find_element_by_id('anonymousEndDateInput').send_keys(expiration_date)

        month_text = '{:%B %Y}'.format(month)
        iprint("Selecting month {}".format(month_text))
        click_on(d, "//input[@name='daterangepicker_start']")
        click_on(d, "//li[text()='{}']".format(month_text))
        click_on(d, "//input[@value='Show']")

        transactions = []

        columns = [
            'transactionDate',
            'transactionTime',
            'transactionName',
            'transactionInfo',
            'modalType',
            'pto',
            'productText',
            'productInfo',
            'epurseMutLocale',
            'epurseMutInfo',
            'fareLocale'
        ]

        while True:
            rows = d.find_elements_by_css_selector('.known-transaction')
            iprint("Scraping " + str(len(rows)) + " rows")
            d.implicitly_wait(0)
            for row in rows:
                tx = {c: get_angular_val(row, c) for c in columns}
                transactions.append(tx)
            d.implicitly_wait(PAGE_TRANSITION_WAIT)
            elem_next_page = d.find_element_by_xpath("//a[text()='»']")
            if elem_next_page.is_displayed():
                iprint("Navigating to the next page")
                elem_next_page.click()
            else:
                break;

        iprint("Scraped " + str(len(transactions)) + " transactions")
        iprint("Saving to a CSV file")
        default_filename = 'ovchipkaart-{:%Y-%m}.csv'.format(month)
        dst_filepath = os.path.join(TARGET_DATA_FOLDER, filename or default_filename)
        with open(dst_filepath, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile,
                                delimiter=';',
                                quotechar='"',
                                fieldnames=columns,
                                quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            for tx in transactions:
                writer.writerow({k: unicode(v).encode("utf-8") for k,v in tx.iteritems()})
        iprint("Done! Transaction file is located at " + dst_filepath)

    except:
        quit_chrome(d)
        raise
    quit_chrome(d)


def get_env_var(name):
    if name in os.environ:
        return os.environ[name]
    else:
        eprint("Environmental variable " + name + " not found")
        sys.exit(1)


def parse_month(s):
    try:
        return datetime.datetime.strptime(s, '%Y-%m')
    except ValueError:
        eprint(s, "is not a month in YYYY-MM format")
        sys.exit(1)


@click.command()
@click.option('--month', help='Month whose data will be downloaded, format YYYY-MM', required=True)
@click.option('--export-filename', help='Name of the downloaded CSV file')
def run(month, export_filename):
    """Download a list of transactions from AirBank"""
    download_with_chrome(
        card_number=get_env_var("OVCHIPKAART_CARD_NUMBER"),
        expiration_date=get_env_var("OVCHIPKAART_EXPIRATION_DATE"),
        month=parse_month(month),
        filename=export_filename
    )


if __name__ == '__main__':
    run()
