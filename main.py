import os
import logging
import sys
import requests
from requests.exceptions import RequestException
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s [%(levelname)s]: %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# get startup time
startupTime = time.time()

# return number of seconds elapsed since start of the program
def elapsed():
    return int(time.time() - startupTime)

class ApiResponse:
    status = 200
    data = None

    def __init__(self, data = None, status = 200):
        self.status = status
        self.data = data
    
    def ok(self):
        if not isinstance(self.status, int): return False
        if 200 <= self.status <= 299:
            return True
        else:
            return False

def httpGet(url, key, params=None):
    try:
        headers = {'X-Api-Key': key}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return ApiResponse(status = response.status_code, data = response.json())
        
    except (RequestException, ValueError) as e:
        return ApiResponse(status = None, data = f'Failed get request to {url}. Reason: {e}')

def httpDelete(url, key, params=None):
    try:
        headers = {'X-Api-Key': key}
        response = requests.delete(url, params=params, headers=headers)
        response.raise_for_status()
        return ApiResponse(status = response.status_code, data = response.json())
        
    except (RequestException, ValueError) as e:
        return ApiResponse(status = None, data = f'Failed delete request to {url}. Reason: {e}')
    
# Define the failure-check criteria
def isFailed(record):
    if record['status'] == 'warning' and 'stalled' in record['errorMessage'].lower():
        return True
    else:
        return False

# delete expired items
def processQueue(api_url, api_key, queue, cache):
    if not queue:
        return
    
    cacheKeys = cache.keys()
    temp = {}
    
    for el in queue:
        if el not in cacheKeys:
            logging.info(f'Added {el}')
            temp.update({el: elapsed()})
        else:
            logging.info(f'Updated {el}, {elapsed()}/{cache[el]+3600}')
            temp.update({el: cache[el]})

    cache.clear()

    for id,time in temp.items():
        if (time + 3600) < elapsed(): # 1h 
            res = httpDelete(f'{api_url}/queue/{id}', api_key, {'removeFromClient': 'true', 'blocklist': 'true'})
            if res.ok():
                logging.info(f'Removed {id}')
            else:
                logging.info(f'Error when removing {id}')
        else:
            cache.update({id:time})

# return an array of failed IDs
def fetchQueue(api_url, api_key, size):
    queue_url = f'{api_url}/queue'
    queue = httpGet(queue_url, api_key, {'page': '1', 'pageSize': size})

    if not queue.ok():
        logging.error('Failure in fetching queue')
        return None

    if 'records' not in queue.data:
        logging.info('queue is empty')
        return None

    ret=[]

    for item in queue.data['records']:
        if isFailed(item):
            ret.append(item['id'])

    return ret

# Function to count records in the queue
def count_records(api_url, api_key):
    queue_url = f'{api_url}/queue'
    queue = httpGet(queue_url, api_key)
    if not queue.ok(): return None
    if not isinstance(queue.data, dict): return 0
    return queue.data.get('totalRecords', 0)

def task(api_url, api_key, cache):
    size = count_records(api_url, api_key)

    # query issue
    if not isinstance(size, int):
        logging.error('Failure in getting size, aborting')
        return
    
    if size == 0:
        # queue is empty, abort silently
        cache.clear()
        return
    
    logging.info(f'Processing {size} elements')
    
    processQueue(api_url, api_key, fetchQueue(api_url, api_key, size), cache)

def main():
    RADARR_api_url = os.environ.get('RADARR_URL')
    RADARR_api_key = os.environ.get('RADARR_API_KEY')

    SONARR_api_url = os.environ.get('SONARR_URL')
    SONARR_api_key = os.environ.get('SONARR_API_KEY')

    if not RADARR_api_key:
        RADARR_api_url = ''
    if not SONARR_api_key:
        SONARR_api_url = ''

    if not RADARR_api_url and not SONARR_api_url:
        logging.error('No system provided, aborting')
        sys.exit(1)

    logging.info(f'Running with: {RADARR_api_url} {SONARR_api_url}')


    # caches
    radarrCache = {}
    sonarrCache = {}

    while True:
        if RADARR_api_url: task(f'{RADARR_api_url}/api/v3', RADARR_api_key, radarrCache)
        if SONARR_api_url: task(f'{SONARR_api_url}/api/v3', SONARR_api_key, sonarrCache)
        time.sleep(600) # 10 minutes cycle

# Entry point
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Exiting')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
