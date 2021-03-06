# Copyright (c) Johns Hopkins University and its affiliates.
# This source code is licensed under the Apache 2 license found in the
# LICENSE file in the root directory of this source tree.
"""
JHU bloomberg crawler
Expected page to crawl is
https://www.globalhealthnow.org/2020-02/coronavirus-expert-reality-check
"""
__author__ = "Max Fleming"
__copyright__ = "Copyright 2020, Johns Hopkins University"
__credits__ = ["Max Fleming"]
__license__ = "Apache 2.0"
__version__ = "0.1"
__maintainer__ = "JHU-COVID-QA"
__email__ = "covidqa@jhu.edu"
__status__ = "Development"

import datetime
import time
import requests
from bs4 import BeautifulSoup
from covid_scraping import Conversion, Scraper


class JHUBloombergScraper(Scraper):

    def _valid_responce(self, x):
        return (x.find_next_sibling().name is 'p' or x.find_next_sibling().name is 'ul')\
            and (x.find_next_sibling().find_next_sibling().name is 'p' or x.find_next_sibling().find_next_sibling().name is 'ul')

    """
    In some parts of the artical there is very little difference
    in the HTML structure between sources and question answer
    responce, this need hard coded points to cut responces.
    Also, there is one point where the
    artical is refering people to participate in a study. This
    did not seem in context of QA pairs.
    """

    def _truncate_responce(self, x):
        truncate_points = ["Preeti N. Malani",
                           "Eric Toner, MD",
                           "Sulzhan Bali",
                           "William Moss",
                           "Nahid Bhadelia",
                           "We have launched"]
        for point in truncate_points:
            if point in x:
                x = x.split(point)[0]
        return x

    def _filter_h3_headers(self, x):
        return not x.find('a') and x.getText().strip() is not ''

    def _get_responces(self, x):
        x = x.find_next_sibling()
        responce = x.getText().strip()
        while self._valid_responce(x):
            if x.em:
                x.em.decompose()
            responce += ' ' + x.getText().strip()
            x = x.find_next_sibling()
        return responce

    def _get_final_responce(self, x):
        x = x.find_next_sibling()
        responce = ''
        while 'dkerecm1' not in x.find_next_sibling().find_next_sibling().getText():
            responce += ' ' + x.getText().strip()
            x = x.find_next_sibling()
        return responce

    def _get_topic(self, x):
        return x.find_previous_sibling('h2').get_text().strip()

    def scrape(self):
        url = 'https://www.globalhealthnow.org/2020-02/coronavirus-expert-reality-check'
        html = requests.get(url).text
        lastUpdateTime = time.mktime(
            time.strptime(
                BeautifulSoup(
                    html, 'lxml').find(
                    'div', {
                        'class': 'article-meta-wrap'}).getText().strip(), '%B %d, %Y'))
        soup = BeautifulSoup(
            html, 'lxml').find('div', {'property': 'schema:text'}).findAll('h3')
        questions_list = list(filter(self._filter_h3_headers, soup))
        questions = [x.getText().strip() for x in questions_list]
        responces = list(map(self._get_responces, questions_list[:-1]))
        responces.append(self._get_final_responce(questions_list[-1]))
        responces = list(map(self._truncate_responce, responces))
        topics = list(map(self._get_topic, questions_list))
        converter = Conversion(
            self._filename,
            self._path)
        for q, a, t in zip(questions, responces, topics):
            converter.addExample({
                'sourceUrl': url,
                'sourceName': "Johns Hopkins Bloomberg School of Public Health",
                "needUpdate": True,
                "typeOfInfo": "QA",
                "isAnnotated": False,
                "responseAuthority": "",
                "question": q,
                "answer": a,
                "hasAnswer": True,
                "targetEducationLevel": "College",
                "topic": [t],
                "extraData": {},
                "targetLocation": "",
                'language': 'en'
            })
        return converter.write()


def main():
    scraper = JHUBloombergScraper(path="./", filename="JHU-Bloomberg")
    scraper.scrape()


if __name__ == '__main__':
    main()
