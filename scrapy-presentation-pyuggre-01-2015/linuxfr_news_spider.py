# -*- coding: utf-8 -*-
import time
import re
from scrapy import Spider, Item, Field, Request, FormRequest, log

class LinuxNewsPost(Item):
    title = Field()
    score = Field()
    pub_date = Field()
    url = Field()
    comment_nb = Field()
    visited = Field()

class LinuxfrNewsSpider(Spider):

    name = ('linuxfr_news_spider')

    def __init__(self, login, password, page=0, *args, **kwargs):
        super(LinuxfrNewsSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://linuxfr.org/compte/connexion']
        self.start_page_id = page
        self.login = login
        self.password = password

    def parse(self, response):
        return FormRequest.from_response(
            response,
            formxpath = '//form[@id="new_account"]',
            formdata = {
                'account[login]': self.login,
                'account[password]': self.password,
            },
            callback = self.after_login
        )

    def after_login(self, response):
        if "Identifiant ou mot de passe invalide" in response.body:
            self.log("Login failed", level=log.ERROR)
            return

        print ''
        print ''
        print 'IDENTIFIED as '+response.xpath('//aside[@id="sidebar"]/div[@class="login box"]/h1/a/text()')[0].extract()
        print ''
        print 'waiting 5 seconds before continue...'
        print ''
        time.sleep(5)
        exit()
        yield Request('https://linuxfr.org/news?page=%s' % self.start_page_id, self.authenticated_parse)

    def authenticated_parse(self, response):
        # self.settings['DOWNLOAD_DELAY'] = 2
        articles = response.xpath('//article')

        for article in articles:
            title = article.xpath('./header/h1/a/text()')[0].extract()
            path = article.xpath('./header/h1/a/@href')[0].extract()
            pub_date = article.xpath('./header/div[@class="meta"]/time/@datetime')[0].extract()
            score = article.xpath('.//figure[@class="score"]/text()')[0].extract()
            comment_nb = article.xpath('./footer//span[@class="nb_comments"]/text()').re(r'\d+')[0] ## HERE
            visited = article.xpath('./footer//span[@class="visit"]/text()').re(r', (.*)')[0] ## HERE
            yield LinuxNewsPost(
                title = title,
                url = 'https://linuxfr.org'+path,
                score = score,
                pub_date = pub_date,
                comment_nb = int(comment_nb),
                visited = visited
            )

        next_page_path = response.xpath('//nav[@class="toolbox"]/nav[@class="pagination"]/span[@class="next"]/a/@href')[0].extract()
        yield Request('https://linuxfr.org'+next_page_path, self.authenticated_parse)
