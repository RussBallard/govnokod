import re
import time

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider


class WBspider(Spider):
    name = 'wildberries.ru'
    unique_products = set()
    start_urls = ['https://www.wildberries.ru/catalog/tovary-dlya-zhivotnyh/dlya-koshek/amunitsiya']
    custom_settings = {
        'DOWNLOAD_TIMEOUT': 20,
        'DOWNLOAD_DELAY': .2
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 meta=self.custom_settings)

    def parse(self, response):
        section = response.xpath('//span[@itemprop="title"]/text()').getall()
        products_url = response.xpath('//a[@class="ref_goods_n_p"]/@href').getall()
        for url in products_url:
            self.custom_settings.update({'url': url,
                                         'section': section})
            yield scrapy.Request(url=url,
                                 callback=self.parse_product,
                                 meta=self.custom_settings)

        next_page = response.xpath('//a[@class="next"]/@href').get()
        if next_page is not None:
            yield scrapy.Request(url='https://www.wildberries.ru' + next_page,
                                 callback=self.parse,
                                 meta=self.custom_settings)

    def parse_product(self, response):
        multi_variants = response.xpath('//*[@class="color j-color"]/a/@href').getall()
        RPC = response.xpath('//span[@class="j-article"]/text()').get()
        # Проверка на дубликат
        if RPC not in self.unique_products:
            self.unique_products.add(RPC)

            title = response.xpath('//span[@class="name"]/text()').get()
            brand = response.xpath('//span[@class="brand"]/text()').get()
            description = response.xpath('//div[contains(@class, "j-description")]/p/text()').get()
            set_images = response.xpath('//a[contains(@class, "j-carousel-image")]/@rev').getall()
            current_price = response.xpath('//span[@class="final-cost"]/text()').get()
            original_price = response.xpath('//del[@class="c-text-base"]/text()').get()
            metadata_keys = response.xpath('//div[@class="pp"]/span[1]/b/text()').getall()
            metadata_values = response.xpath('//div[@class="pp"]/span[2]/text()').getall()
            video = response.xpath('//meta[@property="og:video"]/@content').get()
            sale_tag = response.xpath('//div[@class="discount-tooltipster-content"]/p[2]/span[1]/text()').get()
            composition = response.xpath(
                '//span[@class="j-composition collapsable-content j-toogle-height-instance"]/text()').get()

            section = response.meta['section']
            url = response.meta['url'].replace('?targetUrl=GP', '')

            timestamp = str(time.strftime("%s", time.gmtime()))
            title = " ".join(title.split())
            video = list(video[2:]) if video is not None else None
            set_images = [image[2:] for image in set_images] if set_images else []
            main_image = set_images[0] if set_images else ''
            description = description if description is not None else ''
            current_price = float(re.sub('[^0-9]', '', current_price)) if current_price is not None else 0.0
            original_price = float(re.sub('[^0-9]', '', original_price)) if original_price is not None else 0.0
            in_stock = True if original_price != 0.0 else False

            product = {
                'timestamp': timestamp,
                'RPC': RPC,
                'url': url,
                'title': title,
                'marketing_tags': [],  # Не нашел применения этому полю на сайте
                'brand': brand,
                'section': section,
                'price_data': {
                    'current': current_price,
                    'original': original_price,
                    'sale_tag': sale_tag
                },
                'stock': {
                    'in_stock': in_stock,
                    "count": 0  # На сайте не указываются остатки
                },
                'assets': {
                    'main_image': main_image,
                    'set_images': set_images,
                    'view360': [],
                    'video': video
                },
                'metadata': {
                    '__description': description,
                }
            }

            if metadata_keys is not None and metadata_values is not None:
                for key, values in dict(zip(metadata_keys, metadata_values)).items():
                    product['metadata'].update({key.strip(): values.strip()})

            if composition is not None:
                product['metadata']['Состав'] = composition

            yield product

        # У некоторых товаров есть похожие варианты с уникальным RPC
        if multi_variants and response.meta.get('stop', True):
            for url in multi_variants:
                yield scrapy.Request(url=url,
                                     callback=self.parse_product,
                                     meta={'stop': False,
                                           'url': url,
                                           'section': response.meta['section']})


if __name__ == '__main__':
    p = CrawlerProcess()
    p.crawl(WBspider)
    p.start()
