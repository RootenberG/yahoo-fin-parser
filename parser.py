import os
import time
from time import strptime
import csv
from datetime import timedelta, datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

PAGE_SCROLING_TIME = 0.5
SITE_URL = "https://finance.yahoo.com/"
COMPANIES = ['DOCU']

NEXT = False


class YahooParser():
    """Simple finance yahoo parser """

    def __init__(self, name):
        self.driver = webdriver.Chrome()
        self.name = name

    def scroll(self) -> None:
        """Scrolls page to bottom"""
        self.driver.execute_script("window.scrollTo(0, 123123123)")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, 123123123)")

    def get_site_data(self) -> None:
        """Gets all site data such as tables and news"""
        self.driver.get(SITE_URL)
        self.driver.implicitly_wait(30)

        self.driver.find_element_by_id(
            "yfin-usr-qry").send_keys(self.name)
        try:
            self.driver.find_element_by_xpath(
                r'//*[@id="header-desktop-search-button"]'
            ).click()
            self.driver.implicitly_wait(3)
            self.news = self.driver.find_elements_by_xpath(
                r'//*[@id="quoteNewsStream-0-Stream"]/ul/li')
            self.news_records = []
            for i in self.news:
                try:
                    self.driver.implicitly_wait(1)
                    link = i.find_element_by_xpath(
                        r'div/div/div[2]/h3/a').get_attribute('href')
                    title = i.find_element_by_xpath(
                        r'div/div/div[2]/h3/a').text
                    self.news_records.append([link, title])
                except NoSuchElementException:
                    continue
            self.driver.find_element_by_xpath(
                r'//*[@id="quote-nav"]/ul/li[6]/a'
            ).click()
            self.driver.find_element_by_xpath(
                r'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[1]/div[1]/div[1]/div/div/div'
            ).click()
            self.driver.implicitly_wait(30)

            self.driver.find_element_by_xpath(
                r'//*[@id="dropdown-menu"]/div/ul[2]/li[4]/button'
            ).click()

            self.scroll()
            headers = self.driver.find_elements_by_xpath(
                r'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/thead/tr/th')
            self.headers = [header.find_element_by_xpath(
                r'span').text for header in headers]
            self.records = self.driver.find_elements_by_xpath(
                r'//*[@id="Col1-1-HistoricalDataTable-Proxy"]/section/div[2]/table/tbody/tr')
            self.records = [[rec.find_element_by_xpath(
                r'span').text for rec in record.find_elements_by_xpath('td')
            ] for record in self.records]

            self.driver.close()
        except NoSuchElementException:
            global NEXT
            NEXT = True

    def store_into_csv(self) -> None:
        """Stores records from table and  links with titles of news into cvs"""
        with open(f'test-{self.name}.csv', 'w', newline='') as csvinput:
            writer = csv.writer(
                csvinput, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(self.headers)
            three_day_before_change = []
            for rec in self.records:
                three_day_before_change.append([rec[0], rec[4]])
                writer.writerow(rec)
            self.three_day_before_change = self.days_selection(
                three_day_before_change)

        with open(f'test-{self.name}.csv', 'r', newline='') as csvoutput:
            with open(f'{self.name}.csv', 'w') as finally_csv:
                writer = csv.writer(
                    finally_csv, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                i = 0
                for row in csv.reader(csvoutput):
                    if row[0] == self.headers[0]:
                        writer.writerow(row + ["3day_before_change"])
                        i -= 1
                    else:
                        writer.writerow(row + [self.three_day_before_change[i]])
                        i += 1
        with open(f'{self.name}-news.csv', 'w', newline='') as news:
            writer = csv.writer(
                news, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["link", 'title'])
            for rec in self.news_records:
                writer.writerow(rec)
        os.remove(f'test-{self.name}.csv')

    def days_selection(self, data) -> list:
        """Creates list with price ratio"""
        delta = timedelta(days=3)
        data = dict(data)
        three_day_before_change = []
        for date in data:
            new_date = date.replace(',', '').split(' ')
            new_date[0] = strptime(new_date[0], '%b').tm_mon
            new_date = '-'.join(map(str, new_date))
            entered_date = datetime.strptime(new_date, '%m-%d-%Y')
            entered_date = entered_date.date()
            delta_date = entered_date - delta
            entered_date = entered_date.strftime(
                "%B")[:3] + ' ' + entered_date.strftime("%d, %Y")
            delta_date = delta_date.strftime(
                "%B")[:3] + ' ' + delta_date.strftime("%d, %Y")
            enter = float(data[entered_date])
            close = float(data[delta_date])
            three_day_before_change.append(
                enter / close) if data.get(delta_date) else three_day_before_change.append('-')
        return three_day_before_change


if __name__ == '__main__':
    for name in COMPANIES:
        NEXT = False
        parser = YahooParser(name)
        parser.get_site_data()
        if NEXT:
            continue
        parser.store_into_csv()
