import scrapy
import base64


class ProxyScrapySpider(scrapy.Spider):
    name = 'proxy_scrapy_spider'

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
            country = row.css('td a .table-country::text').get()  # Страна
            city = row.css('td:nth-child(4)::text').get()  # Город
            speed = row.css('td div.n-bar-wrapper p a::text').get()  # Скорость
            proxy_type = row.css('td:nth-child(6) a::text').get()  # Тип прокси
            anonymity = row.css('td:nth-child(7) a::text').get()  # Уровень анонимности
            last_check = row.css('td:nth-child(8)::text').get()  # Последняя проверка

            # Проверяем, что у нас есть IP адрес, иначе пропускаем пустые строки
            if ip_address:
                yield {
                    'IP Address': ip_address,
                    'Port': port,
                    'Country': country,
                    'City': city,
                    'Speed': speed,
                    'Type': proxy_type,
                    'Anonymity': anonymity,
                    'Last Check': last_check,
                }
