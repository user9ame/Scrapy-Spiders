# -*- coding: utf-8 -*-
import re
import scrapy

from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, Compose

from inspect import isgenerator

from truck_info.items import Company
from truck_info.spiders.carrier import make_all


def join_with_semicolon(args):
    '''
    Join strings with semicolon as a separator.
    '''
    return '; '.join(args)


def remove_tabs(args):
    for idx, item in enumerate(args):
        args[idx] = ' '.join(item.split())
    return args


class CompanyItemLoader(ItemLoader):
    name_out = Compose(lambda v: v[0])
    address_out = Compose(remove_tabs, Join(', '))
    phone_out = Join('-')
    usdot_number_out = Compose(lambda v: int(v[0]))
    safety_rating_out = Compose(lambda v: v[0])
    last_update_out = Join('.')


class CompanyInfoSpider(scrapy.Spider):
    name = 'company_info'
    allowed_domains = ['truckdriver.com']
    start_urls = ['https://www.truckdriver.com/trucking-company-directory/']

    def parse(self, response):
        '''
        @url https://www.truckdriver.com/trucking-company-directory/
        @returns requests 51
        '''
        state_links = response.xpath("//div[@id='content']/ \
            div[@class='row'][2]//a/@href").extract()
        for s in state_links:
            yield scrapy.Request(response.url + s, callback=self.parse_in_state)

    def parse_in_state(self, response):
        '''
        Parses company initials.

        @url https://www.truckdriver.com/trucking-company-directory//ShowDOTCoByState.cfm?PHY_NATN=US&PHY_ST=AL
        @returns requests 27
        '''
        yield scrapy.Request(response.url, callback=self.parse_page)
        com_initials = response.xpath("//a[@class='btn btn-xs btn-info'] \
             /@href").extract()
        for i in com_initials:
            yield scrapy.Request(response.urljoin(i), callback=self.parse_page)

    def parse_page(self, response):
        """
        Parses all the pages available.
        
        Must return 8 requests (8 pages) for this url:
        @url https://www.truckdriver.com/trucking-company-directory/ShowDOTCoByState.cfm?PHY_NATN=US&PHY_ST=AL&vcAStart=A&vcAEnd=A&SR=1&MT=2
        @returns requests 8 8
        """
        yield scrapy.Request(response.url, callback=self.parse_carriers)
        pages = response.xpath("//div[@class='row'][6]/ \
            div[@class='col-sm-12 text-center']//a/@href").extract()
        for page in pages:
            yield scrapy.Request(response.urljoin(page), 
                                    callback=self.parse_carriers)

    def parse_carriers(self, response):
        '''
        Parses company's records.

        Must return 4 requests (4 records) for this url:
        @url https://www.truckdriver.com/trucking-company-directory//ShowDOTCoByState.cfm?PHY_NATN=US&PHY_ST=AL
        @returns requests 4
        '''
        path = "//div[@id='content']/div[@class='row'][5] \
            //div[@class='col-sm-6']//a/@href"
        carriers = response.xpath(path).extract()
        for c in carriers:
            yield scrapy.Request(self.start_urls[0]+c, callback=self.parse_info)
        
    def parse_info(self, response):
        """
        Parses carrier's info.

        @url https://www.truckdriver.com/trucking-company-directory/ShowDOTCo.cfm?CENSUS_NUM=1750114
        @scrapes name address phone usdot_number safety_rating cargo_types fleet_info last_update
        """
        l = CompanyItemLoader(item=Company(), response=response)
        profile_path = "//div[@id='dot-truck-co-profile']"
        raw = response.xpath(profile_path + '//text()').extract()
        carrier = make_all(raw)
        l.add_value('name', carrier['name'])
        l.add_value('address', carrier['address'])
        l.add_value('phone', carrier['phone'], re=r'[0-9]+')
        l.add_value('usdot_number', carrier['usdot_number'])
        l.add_value('safety_rating', carrier['safety_rating'])
        l.add_value('cargo_types', carrier['cargo_types'], remove_tabs)
        l.add_value('fleet_info', carrier['fleet_info'])
        l.add_value('last_update', carrier['last_update'], re=r'[0-9]+')
        return l.load_item()

