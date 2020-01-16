# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class ProductData(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    timestamp = Field()
    RPC = Field()
    url = Field()
    title = Field()
    marketing_tags = Field()
    brand = Field()
    section = Field()
    price_data = Field()
    stock = Field()
    assets = Field()
    metadata = Field()
    price_data = Field()
    stock = Field()
    assets = Field()
    metadata = Field()


class PriceData(Item):
    current = Field()
    original = Field()
    sale_tag = Field()


class Stock(Item):
    in_stock = Field()
    count = Field()


class Assets(Item):
    main_image = Field()
    set_images = Field()
    view360 = Field()
    video = Field()


class Metadata(Item):
    description = Field()
