from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import requests
import bs4
import pprint

import pandas as pd
import time
from DBcm import UseDatabase

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

def get_jobs_postings() -> dict:
    jobs = {}
    for i in range(0,1,10):
        print('Getting job postings ' + str(i) + ' to ' + str(i+9)+'.')
        URL = 'https://www.indeed.com/jobs?q=software+engineer&l=Mountain+View%2C+CA&sort=date&start=' + str(i)
        #conducting a request of the stated URL above:
        page = requests.get(URL)
        time.sleep(2)
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
        return span.get_text().replace('\n', '')


def extract_job_title_from_result(soup) -> dict: 
    jobs = {}
    for div in soup.find_all(name='div', attrs={'data-tn-component':'organicJob'}):
        jobs[div['data-jk']] = {'id' : div['data-jk']}
        for a in div.find_all(name='a', attrs={'data-tn-element':'jobTitle'}):
            jobs[div['data-jk']]['title'] = a['title']
    return(jobs)

def write_to_database(jobs, ids) -> None:
    dbconfig = {'host': '127.0.0.1',
                'user': 'root',
                'password': 'password',
                'database': 'job_board_scraping', }
    print('Writing to database....', end = '')
    for k, v in jobs.items():
        #print(k + ' ' + v['title'] + ' '+ v['description'])
        if k not in ids:
            with UseDatabase(dbconfig) as cursor:
                _SQL = """insert into raw_data
                    (indeed_id, job_title, job_description)
                    values
                    (%s, %s, %s)"""
                cursor.execute(_SQL, (k,
                          v['title'],
                          v['description'], ))
    print('...done')

def get_stored_job_ids() -> set:
    dbconfig = {'host': '127.0.0.1',
                'user': 'root',
                'password': 'password',
                'database': 'job_board_scraping', }
    id_set = set()
    print('Getting job ids from database....', end = '')
    with UseDatabase(dbconfig) as cursor:
        _SQL = """select indeed_id FROM job_board_scraping.raw_data"""
        cursor.execute(_SQL)
        #print(cursor.fetchall())
        for id in cursor.fetchall():
            id_set.add(str(id).translate({ord(c): None for c in '({}),\''}))
    return id_set


jobs = get_jobs_postings()
#jobs = extract_job_title_from_result(bacon)
#pprint.pprint(jobs)
indeed_ids = get_stored_job_ids()


for job, dict in jobs.items():
    #print('Getting job description for job id:' + job)
    if job not in indeed_ids:
        print('Getting job description for job id:' + job)
        description = get_job_description(job)
        if description is None:
            jobs[job]['description'] = 'Blank'
        else:
            jobs[job]['description'] = description
        time.sleep(2)

#print("Writing to database...", end = '')
write_to_database(jobs, indeed_ids)
#print("...Done")
#print("indeed ids")
#pprint.pprint(indeed_ids)
#for id in indeed_ids:
    #print(id)


