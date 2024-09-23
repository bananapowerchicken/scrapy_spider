import scrapy
import requests
import json
import os


class ProxyScrapySpider(scrapy.Spider):
    name = 'proxy_scrapy_spider'
    upload_url = 'https://test-rg8.ddns.net/api/post_proxies'
    save_file = 'results.json'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxies_batch = []  # Инициализация атрибута здесь

        # Создаем файл results.json, если его нет
        if not os.path.exists(self.save_file):
            with open(self.save_file, 'w') as f:
                json.dump({}, f, indent=4)  # Записываем пустой JSON

    def start_requests(self):
        # Генерируем URL'ы для всех страниц (например, с 1 по 5)
        urls = [f'https://www.freeproxy.world/?type=&anonymity=&country=&speed=&port=&page={page}' for page in range(1, 6)]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Ищем все строки таблицы с прокси
        rows = response.css('table.layui-table tbody tr')

        for row in rows:
            ip_address = row.css('td.show-ip-div::text').get()  # IP адрес
            port = row.css('td a::text').get()  # Порт

            # Проверяем, что у нас есть IP адрес, иначе пропускаем пустые строки
            if ip_address:
                proxy = f'{ip_address}:{port}'
                self.proxies_batch.append(proxy)

                # Отправляем каждые 10 прокси на сервер
                if len(self.proxies_batch) == 10:
                    self.upload_proxies()
                    self.proxies_batch = []  # Очищаем после отправки

    def upload_proxies(self):
        """
        Отправляет текущий набор из 10 (или менее) прокси на сервер.
        """
        proxy_data = {
            "len": len(self.proxies_batch),
            "user_id": "t_7850941c",  # Замените на ваш user_id
            "proxies": ', '.join(self.proxies_batch)
        }

        try:
            response = requests.post(self.upload_url, json=proxy_data)
            if response.status_code == 429:
                response_data = response.json()
                save_id = response_data.get("save_id", "unknown_id")  # Получаем save_id из ответа
                self.log(f'Successfully uploaded proxies: {proxy_data["proxies"]}')
                self.save_proxies(save_id)
            else:
                self.log(f'Failed to upload proxies: {proxy_data["proxies"]} - Status: {response.status_code}')
        except requests.exceptions.RequestException as e:
            self.log(f'Error uploading proxies: {e}')

    def save_proxies(self, save_id):
        """
        Сохраняет загруженные прокси с save_id в файл results.json.
        """
        try:
            # Загружаем уже сохраненные данные, если файл существует
            try:
                with open(self.save_file, 'r') as f:
                    results = json.load(f)
            except FileNotFoundError:
                results = {}

            # Добавляем новую запись
            results[save_id] = self.proxies_batch

            # Сохраняем обратно в файл
            with open(self.save_file, 'w') as f:
                json.dump(results, f, indent=4)
            self.log(f'Successfully saved proxies with save_id {save_id}')
        except Exception as e:
            self.log(f'Error saving proxies: {e}')