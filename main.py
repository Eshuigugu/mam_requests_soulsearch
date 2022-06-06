import os
import requests
import urllib.parse
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
from bs4 import BeautifulSoup


def query_soulsearch(query, num_files_to_print=3):
    params = {'query': query}
    r = sess.get(soulsearch_url, params=params, stream=True)

    ss_results = []
    for line in r.iter_lines():
        line = line.decode()
        if line.startswith('data: '):
            json_dict = json.loads(line[6:])
            file_exts = [x['ext'] for x in json_dict['files']]
            if set(ebook_exts).intersection(set(file_exts)):
                for ss_file in json_dict['files']:
                    if not num_files_to_print:continue
                    # change it to nicotine+ url format
                    # slsk://user/share_name/share_path/filename.ext
                    ss_file_url = 'slsk://' + '/'.join([ss_file['user'], * [urllib.parse.quote(x) for x in os.path.normpath(ss_file['file']).split(os.path.sep)]])
                    ss_results.append(ss_file_url)
                    num_files_to_print -= 1
        if num_files_to_print == 0:
            break
        if line == 'event: done':
            break
    r.close()
    return ss_results


def fetch_requests():
    keepGoing = True
    start_idx = 0
    req_books = []
    # fetch list of requests to search for
    while keepGoing:
        time.sleep(1)
        url = 'https://www.myanonamouse.net/tor/json/loadRequests.php'
        headers = {
            'cookie': 'get cookie header(s) and user-agent from developer tools > network activity',
            'user-agent': ''
        }

        params = {
            'tor[text]': '',
            'tor[srchIn][title]': 'true',
            'tor[viewType]': 'unful',
            'tor[cat][]': 'm14',  # search ebooks category
            'tor[startDate]': '',
            'tor[endDate]': '',
            'tor[startNumber]': f'{start_idx}',
            'tor[sortType]': 'dateD'
        }
        data = MultipartEncoder(fields=params)
        headers['Content-type'] = data.content_type
        r = sess.post(url, headers=headers, data=data)
        req_books += r.json()['data']
        total_items = r.json()['found']
        start_idx += 100
        keepGoing = total_items > start_idx

    req_books_reduced = [x for x in req_books if
                         x['cat_name'].startswith('Ebooks') and x['filled'] == 0 and x['torsatch'] == 0 and x[
                             'lang_code'] == 'ENG']
    return req_books_reduced


sess = requests.Session()
ebook_exts = ['pdf', 'azw3', 'mobi', 'epub']
soulsearch_url = 'http://localhost:3000/api/search'

req_books = fetch_requests()
reduce_query_str = lambda query_str: ' '.join([x for x in query_str.split(' ') if len(x) > 1])

for book in req_books[:20]:
    book['url'] = 'https://www.myanonamouse.net/tor/viewRequest.php/' + str(book['id'])[:-5] + '.' + str(book['id'])[
                                                                                                     -5:]
    title = BeautifulSoup(f'<h1>{book["title"]}</h1>', features="lxml").text
    for k, author in json.loads(book['authors']).items():
        break

    query = reduce_query_str(f'{title} {author}')
    results = query_soulsearch(query, num_files_to_print=3)
    if results:
        print(f'{title} by {author}')
        print(book['url'])
        print('\n'.join(results))
        print()
