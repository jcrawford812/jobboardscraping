from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import requests
import bs4
import pprint

import pandas as pd
import time

def simple_get(url:str) -> str:
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None
    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)

def log_error(e):
    print(e)

def get_hits_on_name(name):
    """
    Accepts a `name` of a mathematician and returns the number
    of hits that mathematician's Wikipedia page received in the 
    last 60 days, as an `int`
    """
    # url_root is a template string that is used to build a URL.
    url_root = 'https://xtools.wmflabs.org/articleinfo/en.wikipedia.org/{}'
    response = simple_get(url_root.format(name))

    if response is not None:
        html = BeautifulSoup(response, 'html.parser')

        hit_link = [a for a in html.select('a')
                    if a['href'].find('latest-60') > -1]

        if len(hit_link) > 0:
            # Strip commas
            link_text = hit_link[0].text.replace(',', '')
            try:
                # Convert to integer
                return int(link_text)
            except:
                log_error("couldn't parse {} as an `int`".format(link_text))

    log_error('No pageviews found for {}'.format(name))
    return None

def get_jobs_postings() -> dict:
    jobs = {}
    for i in range(0,101,10):
        URL = 'https://www.indeed.com/jobs?q=software+engineer&l=Mountain+View%2C+CA&sort=date&start=' + str(i)
        #conducting a request of the stated URL above:
        page = requests.get(URL)
        time.sleep(1)
        #specifying a desired format of “page” using the html parser - this allows python to read the various components of the page, rather than treating it as one long string.
        soup = BeautifulSoup(page.text, 'html.parser')

        for div in soup.find_all(name='div', attrs={'data-tn-component':'organicJob'}):
            if div['data-jk'] not in jobs:
                jobs[div['data-jk']] = {'id' : div['data-jk']}
                for a in div.find_all(name='a', attrs={'data-tn-element':'jobTitle'}):
                    jobs[div['data-jk']]['title'] = a['title']

    #printing soup in a more structured tree format that makes for easier reading
    #print(soup.prettify())
    return jobs

def get_job_description(id) -> str:
    URL = 'https://www.indeed.com/viewjob?jk=' + id
    page = requests.get(URL)
    soup = BeautifulSoup(page.text, 'html.parser')
    for span in soup.find_all(name='span', attrs={'id':'job_summary'}):
        return span.get_text()


def extract_job_title_from_result(soup) -> dict: 
    jobs = {}
    for div in soup.find_all(name='div', attrs={'data-tn-component':'organicJob'}):
        jobs[div['data-jk']] = {'id' : div['data-jk']}
        for a in div.find_all(name='a', attrs={'data-tn-element':'jobTitle'}):
            jobs[div['data-jk']]['title'] = a['title']
    return(jobs)

jobs = get_jobs_postings()
#jobs = extract_job_title_from_result(bacon)
#pprint.pprint(jobs)

for job, dict in jobs.items():
    jobs[job]['description'] = get_job_description(job)
    time.sleep(1)

pprint.pprint(jobs)