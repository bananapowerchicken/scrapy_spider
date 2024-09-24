import scrapy
import requests
import json
import os
import time


class ProxyScrapySpider(scrapy.Spider):
    name = 'proxy_scrapy_spider'
    upload_url = 'https://test-rg8.ddns.net/api/post_proxies'
    get_token_url = 'https://test-rg8.ddns.net/api/get_token'
    save_file = 'results.json'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxies_batch = []  # Инициализация атрибута здесь
        self.form_token = None  # Хранение текущего токена формы
        self.cookies = None  # Хранение текущих кук

        # Создаем файл results.json, если его нет
        if not os.path.exists(self.save_file):
            with open(self.save_file, 'w') as f:
                json.dump({}, f, indent=4)  # Записываем пустой JSON

    def start_requests(self):
        # Генерируем URL'ы для всех страниц (например, с 1 по 5)
        urls = [f'https://www.freeproxy.world/?type=&anonymity=&country=&speed=&port=&page={page}' for page in range(1, 2)]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Ищем все строки таблицы с прокси
        rows = response.css('table.layui-table tbody tr')

        for row in rows:
            ip_address = row.css('td.show-ip-div::text').get()  # IP адрес
            if ip_address:
                ip_address = ip_address.strip()
            port = row.css('td a::text').get()  # Порт

            # Проверяем, что у нас есть IP адрес, иначе пропускаем пустые строки
            if ip_address:
                proxy = f'{ip_address}:{port}'
                self.proxies_batch.append(proxy)

                # Отправляем каждые 10 прокси на сервер
                if len(self.proxies_batch) == 10:
                    self.upload_proxies()
                    print(f'10 proxies: {self.proxies_batch}')
                    self.proxies_batch = []  # Очищаем после отправки

    def get_new_token(self):
        """
        Получаем новый токен с сервера и сохраняем его вместе с куки.
        """
        headers = {
            'Cookie': f'x-user_id=t_7850941c',  # Передаем user_id в cookie
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'  # Пример User-Agent
        }
        response = requests.get(self.get_token_url, headers=headers)
        if response.status_code == 200:
            # Сохраняем куки и токен из ответа
            self.cookies = response.cookies
            self.form_token = self.cookies.get('form_token')
            print(f"New form_token received: {self.form_token}")
            print(f"Cookies received: {self.cookies}")
        else:
            print(f"Failed to get token - Status: {response.status_code}")
            self.form_token = None


    # def save_proxies(self, save_id):
    #     """
    #     Сохраняет загруженные прокси с save_id в файл results.json.
    #     """
    #     try:
    #         # Загружаем уже сохраненные данные, если файл существует
    #         try:
    #             with open(self.save_file, 'r') as f:
    #                 results = json.load(f)
    #         except FileNotFoundError:
    #             results = {}

    #         # Добавляем новую запись
    #         results[save_id] = self.proxies_batch

    #         # Сохраняем обратно в файл
    #         with open(self.save_file, 'w') as f:
    #             json.dump(results, f, indent=4)
    #         self.log(f'Successfully saved proxies with save_id {save_id}')
    #     except Exception as e:
    #         self.log(f'Error saving proxies: {e}')

    def upload_proxies(self):
        """
        Отправляет текущий набор из 10 (или менее) прокси на сервер.
        """
        # Получаем новый токен и куки перед отправкой данных
        self.get_new_token()
        if not self.form_token or not self.cookies:
            print("Unable to get form_token or cookies, skipping upload.")
            return

        proxy_data = {
            "len": len(self.proxies_batch),
            "user_id": "t_7850941c",
            "proxies": ', '.join(self.proxies_batch)
        }

        # Отправляем данные с куки и токеном
        response = requests.post(self.upload_url, json=proxy_data, cookies=self.cookies)
        print(f'First try response: {response.status_code}')

        # Если статус 429 (слишком много запросов)
        if response.status_code == 429:
            print('Received 429, waiting and refreshing token...')
            time.sleep(15)  # Ожидание перед повторной попыткой

            # Получаем новый токен
            self.get_new_token()
            if not self.form_token or not self.cookies:
                print("Unable to get token or cookies after 429, skipping upload.")
                return

            # Вторая попытка отправки данных
            response = requests.post(self.upload_url, json=proxy_data, cookies=self.cookies)
            print(f'Second try response: {response.status_code}')
            if response.status_code == 200:
                response_data = response.json()
                save_id = response_data.get("save_id", "unknown_id")
                # self.save_proxies(save_id)
                print(f'Successfully uploaded with save_id: {save_id}')
            else:
                print(f'Failed to upload after 429 - Status: {response.status_code}')
        elif response.status_code == 200:
            response_data = response.json()
            save_id = response_data.get("save_id", "unknown_id")
            print(f'Successfully uploaded with save_id: {save_id}')
        else:
            print(f'Failed to upload - Status: {response.status_code}')