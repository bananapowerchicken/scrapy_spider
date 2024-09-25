import scrapy
import requests
import json
import os
import time
from datetime import datetime


class ProxyScrapySpider(scrapy.Spider):
    name = 'proxy_scrapy_spider'
    upload_url = 'https://test-rg8.ddns.net/api/post_proxies'
    get_token_url = 'https://test-rg8.ddns.net/api/get_token'
    save_file = 'results.json'
    time_file = 'time.txt'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxies_batch = []
        self.form_token = None
        self.cookies = None
        self.request_count = 0  # Счётчик запросов
        self.start_time = datetime.now()

        if not os.path.exists(self.save_file):
            with open(self.save_file, 'w') as f:
                json.dump({}, f, indent=4)


    def start_requests(self):
        urls = [f'https://www.freeproxy.world/?type=&anonymity=&country=&speed=&port=&page={page}' for page in range(1, 6)]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        rows = response.css('table.layui-table tbody tr')

        for row in rows:
            ip_address = row.css('td.show-ip-div::text').get()
            if ip_address:
                ip_address = ip_address.strip()
            port = row.css('td a::text').get()

            if ip_address:
                proxy = f'{ip_address}:{port}'
                self.proxies_batch.append(proxy)

                # send every 10 proxies to server
                if len(self.proxies_batch) == 10:
                    self.upload_proxies()
                    print(f'10 proxies: {self.proxies_batch}')
                    self.proxies_batch = []


    def get_new_token(self):
        response = requests.get(self.get_token_url) # reload page
        if response.status_code == 200:
            self.cookies = response.cookies
            self.form_token = self.cookies.get('form_token')
            print(f"New form_token received: {self.form_token}")
            print(f"Cookies received: {self.cookies}")
        else:
            print(f"Failed to get token - Status: {response.status_code}")
            self.form_token = None


    def save_proxies(self, save_id):
        try:
            try:
                with open(self.save_file, 'r') as f:
                    results = json.load(f)
            except FileNotFoundError:
                results = {}

            # new save_id
            results[save_id] = self.proxies_batch
            print(f'write to file {self.proxies_batch}')

            with open(self.save_file, 'w') as f:
                json.dump(results, f, indent=4)
            self.log(f'Successfully saved proxies with save_id {save_id}')
        except Exception as e:
            self.log(f'Error saving proxies: {e}')


    def upload_proxies(self):
        self.get_new_token()
        if not self.form_token or not self.cookies:
            print("Unable to get form_token or cookies, skipping upload.")
            return            

        proxy_data = {
            "len": len(self.proxies_batch),
            "user_id": "t_7850941c",
            "proxies": ', '.join(self.proxies_batch)
        }

        max_attempts = 10 
        attempt = 0
        wait_time = 30

        while attempt < max_attempts:
            response = requests.post(self.upload_url, json=proxy_data, cookies=self.cookies)
            print(f'Attempt {attempt + 1} - Response status: {response.status_code}')

            if response.status_code == 200:
                response_data = response.json()
                save_id = response_data.get("save_id", "unknown_id")
                self.save_proxies(save_id)
                print(f'Successfully uploaded with save_id: {save_id}')
                break
            elif response.status_code == 429:
                print(f'Received 429 - Waiting {wait_time} seconds before retry...')
                time.sleep(wait_time)
                attempt += 1
                wait_time += 15
                self.get_new_token()
            else:
                print(f'Failed to upload - Status: {response.status_code}')
                break

        if attempt == max_attempts:
            print(f"Failed to upload after {max_attempts} attempts")

    
    def save_execution_time(self):
        try:
            self.end_time = datetime.now()
            execution_time = self.end_time - self.start_time
            execution_time_str = str(execution_time).split('.')[0] # format

            with open(self.time_file, 'a') as f:
                f.write(f"Total execution time: {execution_time_str}\n")
            print(f"Total execution time {execution_time_str} saved to {self.time_file}")
        except Exception as e:
            print(f"Error saving execution time: {e}")


    def closed(self, reason):
        # when spider stops
        self.save_execution_time()
        self.log(f"Spider closed because: {reason}")