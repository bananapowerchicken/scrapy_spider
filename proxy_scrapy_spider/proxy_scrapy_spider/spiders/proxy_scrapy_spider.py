import scrapy
import base64


class ProxyScrapySpider(scrapy.Spider):
    name = 'proxy_scrapy_spider'
    start_urls = [
        # f'http://free-proxy.cz/en/proxylist/main/{page}' for page in range(1, 2)
        'https://www.freeproxy.world/?type=&anonymity=&country=&speed=&port=&page=2'
    ]

    # def parse(self, response):
    #     print('start')
    #     print(response)
    #     for row in response.css('table#proxy_list tbody tr'):
    #         ip_encoded = row.css('script::text').re_first(r'\"(.+?)\"')  # Извлечение закодированного IP
    #         port = row.css('td:nth-child(2)::text').get()  # Извлечение порта
    #         print(f'AAA {ip_encoded} {port}')

    #         if ip_encoded and port:
    #             # Форматируем прокси как IP:PORT
    #             proxy = f'{ip_encoded}:{port}'
    #     print('stop')

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