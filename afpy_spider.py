from scrapy import Spider, Item, Field, Request

class Job(Item):
    title = Field()
    url = Field()

class AfpyJobSpider(Spider):

    name = 'afpy_jobs'
    start_urls = ['http://www.afpy.org/jobs']

    def parse(self, response):

        for job in response.xpath('//div[@class="jobitem"]'):
            title_xpath = './a/h2[@class="tileHeadline"]/text()'
            url_xpath = './a/@href'
            
            title = job.xpath(title_xpath)[0].extract()
            url = job.xpath(url_xpath)[0].extract()

            yield Job(title=title, url=url)


        next_page_url_xpath = '//div[@class="listingBar"]/span[@class="next"]/a/@href'
        next_page_url = response.xpath(next_page_url_xpath)[0].extract()
        yield Request(url=next_page_url)
