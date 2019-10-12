import datetime
import re

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
from w3lib.html import remove_tags

from wildberries.items import *


class WBspider(CrawlSpider):
    name = 'wildberries_spider'
    start_urls = ['https://www.wildberries.ru/catalog/obuv/zhenskaya/sabo-i-myuli/myuli']
    custom_settings = {
        'FEED_EXPORT_FIELDS': ["timestamp", "RPC", "url", "title", "marketing_tags", "brand", "section", "price_data",
                               "stock", "assets", "metadata"]
    }

    rules = (
        Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="next"]',)), callback="parse_start_url",
             follow=True),)

    def current_or_original(self, original, current):
        return re.sub("[^0-9]", "", original) if original is not None else current

    def convert_to_dict(self, to_dict):
        return dict((y, x) for x, y in [(y, x) for x, y in zip(*[iter(to_dict)] * 2)])

    def parse_start_url(self, response):
        section = [x for x in response.xpath('//span[@itemprop="title"]/text()').extract()]
        for product in response.xpath('//a[@class="ref_goods_n_p"]/@href').extract():
            yield scrapy.Request(url=product[:-13], callback=self.parse_product, meta={'section': section})

    def parse_product(self, response):
        if response.xpath('//div[@itemtype="http://schema.org/Product"]').extract_first() is not None:
            self.log('I just visited:' + response.url)
            price_data = PriceData()
            stock = Stock()
            assets = Assets()
            metadata = Metadata()
            product_data = ProductData()

            description = response.xpath('//div[@class="j-description description-text"]/p').extract_first()
            metadata_update = self.convert_to_dict(
                response.xpath('//div[@class="params"]/div[@class="pp"]//text()').getall())
            structure = ''.join(response.xpath('normalize-space(//p[@class="composition"])').extract())
            metadata_update.update({'Состав': structure.replace('Состав ', '')})
            # Костыль для исправления лишних пробелов
            metadata_update = {k.strip(): v.strip() for k, v in metadata_update.items()}
            images = [x for x in response.xpath('//ul[@class="carousel"]//a/@href').extract() if "//" in x]

            if response.xpath('//meta[@itemprop="price"]/@content').extract_first() == '0':
                current = original = 0.0
            else:
                # Цена, которую видно при наличии скидки скидки
                current = re.sub("[^0-9]", "", response.xpath('//meta[@itemprop="price"]').extract_first())[:-2]
                # Всегда на виду
                original = response.xpath('//span[@class="price-popup old-price"]').extract_first()

            product_data['timestamp'] = str(int(datetime.datetime.now().timestamp()))
            product_data['RPC'] = metadata_update['Артикул']
            product_data['url'] = response.xpath('//meta[@property="og:url"]/@content').extract_first()
            product_data['title'] = response.xpath('//span[@class="name"]/text()').extract_first().strip()
            product_data['marketing_tags'] = ""  # Не нашел применение этому полю
            product_data['brand'] = metadata_update['Бренд']
            product_data['section'] = response.meta['section']
            price_data['current'] = current if current == 0.0 else float(current)
            price_data['original'] = original if current == 0.0 else float(self.current_or_original(original, current))

            current = price_data['current']
            original = price_data['original']

            price_data['sale_tag'] = None if price_data['current'] == price_data[
                'original'] else 'Скидка {0:.0%}'.format(
                current / original)
            product_data['price_data'] = dict(price_data)
            stock['in_stock'] = False if current == 0.0 else True
            stock['count'] = 0  # Не нашел применение этому полю
            product_data['stock'] = dict(stock)
            assets['main_image'] = images[0]
            assets['set_images'] = images
            assets['view360'] = next(
                (s for s in response.xpath('//ul[@class="carousel"]//img/@src').extract() if '360' in s), [])
            assets['video'] = []  # Не нашел товар с видео
            product_data['assets'] = dict(assets)
            metadata['description'] = "" if description is None else remove_tags(description)
            product_data['metadata'] = dict(metadata)
            product_data['metadata'].update(metadata_update)

            yield product_data


if __name__ == '__main__':
    p = CrawlerProcess()
    p.crawl(WBspider)
    p.start()
