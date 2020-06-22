# -*- coding: utf-8 -*-
import scrapy
import requests
from scrapy.crawler import CrawlerProcess


class OregonSpider(scrapy.Spider):
    name = 'oregon'
    custom_settings = {
            'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
            '(KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36',
            'ROBOT_OBEY': True,
            'RANDOMIZE_DOWNLOAD_DELAY': True,
            # Configure a delay for requests for the same website (default: 0)
            'DOWNLOAD_DELAY': 3,
            'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
            'CONCURRENT_REQUESTS_PER_IP': 1,
            # Disable cookies (enabled by default)
            #'COOKIES_ENABLED': False,
            'AUTOTHROTTLE_ENABLED': True,
            # The initial download delay
            'AUTOTHROTTLE_START_DELAY': 5,
            # The maximum download delay to be set in case of high latencies
            'AUTOTHROTTLE_MAX_DELAY': 60,
            # The average number of requests Scrapy should be sending in parallel to
            # each remote server
            'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
            # Enable showing throttling stats for every response received:
            'AUTOTHROTTLE_DEBUG': True,
            'HTTPCACHE_ENABLED': True,
            }
    allowed_domains = ['ltclicensing.oregon.gov']
    start_urls = ['https://ltclicensing.oregon.gov/Facilities?GeoLocationString=&RangeValue=50&LocationSearchString=&FacilitySearchString=&AFH=true&AFH=false&ALF=true&ALF=false&NF=true&NF=false&RCF=true&RCF=false&Medicaid=true&Medicaid=false&Medicare=true&Medicare=false&PrivatePay=true&PrivatePay=false&OpenOnly=false']

    def parse(self, response):
        table_data = response.xpath('//body//table//tr')
        for row in table_data:
            for item in row:
                xpath('.//text()').extract()

        rows = []
        for tr in theader:
            rows.append(tr.xpath('.//text()').extract())
        print(rows)
        yield scrapy.Request(url=response.url, callback=self.get_records)

    def get_records(self, response):

        # get table header
        theader = response.xpath('//body//table[@class="table"]/tr[1]/th'
                                 '//text()').extract()
        # get list of table records
        table = response.xpath('//body//table[@class="table"]'
                            '//tr[@class="clickable-row"]')
        # get data records
        for r in table:
            # detailedinfo_link = r.xpath('./@data-href').extract()[0]
            # trow = r.xpath('./td/text()').extract()
            yield scrapy.Request(
                    url=response.urljoin(r.xpath('./@data-href').extract()[0]),
                    callback=self.get_details,
                    meta={'rec': r.xpath('./td/text()').extract(),
                          'theader': theader})

    def get_details(self, response):
        # clean the data
        header = [i.strip()
                  for i in response.meta['theader']
                  if i.strip()]
        trecord = [i.strip()
                   for i in response.meta['rec']
                   if i.strip()]
        item = dict(zip(header, trecord))
        #
        # PARSE DETAILED INFORMATION
        #
        address = [i.strip()
                   for i in response.xpath('//*[@id="facilityTab"]'
                                           '/div[1]/div[1]/text()').extract()
                   if i.strip()]
        zip_code = address[1].split()[-1]
        if not zip_code.isnumeric():
            raise IndexError('Zip code is not numeric!')
        item.update({'Street': address[0],
                     'Zip': zip_code,
                     'Url': response.url})
        facility_detail_table = response.xpath('//*[@id="facilityTab"]/div[1]/'
                                               'div[1]/table/tr')
        for row in facility_detail_table:
            label = [i.strip()
                     for i in row.xpath('td[1]//text()').extract()
                     if i.strip()]
            if len(label) > 1:
                raise IndexError('Multiple rows label in the table!')
            data = [i.strip()
                    for i in row.xpath('td[2]//text()').extract()
                    if i.strip()]
            data = [' '.join([i.strip() for s in data for i in s.split()])]
            item.update(zip(label, data))

        return item

if __name__ == '__main__':
    url = 'https://ltclicensing.oregon.gov/Facilities?GeoLocationString=&RangeValue=50&LocationSearchString=&FacilitySearchString=&AFH=true&AFH=false&ALF=true&ALF=false&NF=true&NF=false&RCF=true&RCF=false&Medicaid=true&Medicaid=false&Medicare=true&Medicare=false&PrivatePay=true&PrivatePay=false&OpenOnly=false'

    headers = {
            b'Accept': b'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            b'Accept-Language': b'en',
            b'User-Agent': b'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome /57.0.2987.110 Safari/537.36',
            b'Accept-Encoding': b'gzip,deflate'
            }
    with open('response_with_requests.html', 'wb') as f:
        f.write(requests.get(url, headers=headers).text.encode('utf-8'))

    process = CrawlerProcess()
    process.crawl(OregonSpider)
    process.start()
