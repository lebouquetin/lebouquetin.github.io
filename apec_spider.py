# -*- coding: utf-8 -*-
import re
import time

from scrapy import Spider, Item, Field, Request, FormRequest
import datetime

# Notes sur les sujets intéressants :
# Unicode dans les xpath (on est en python 2, pas en python 3)
#

from scrapy.contrib.loader import ItemLoader
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Join, Identity

class TakeFirstNotEmpty(TakeFirst):

    def __init__(self, prefix='', suffix=''):
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, values):
        for value in values:
            if 'SET_EMPTY'==value:
                return ''
            elif value is not None and value!='':
                return value

class TakeFirstSalaryIntValue(object):
    def __call__(self, values):
        for value in values:
            if value is not None and value!='':
                try:
                    int_values = map(int, re.findall(r'\d+', value))
                    int_values[:] = [x*1000 if x<1000 else x for x in int_values]
                    return min(int_values)
                except ValueError:
                    return 0

class TakeLastSalaryIntValue(object):
    def __call__(self, values):
        for value in values:
            if value is not None and value!='':
                try:
                    # print value
                    # print re.findall(r'\d+', value)
                    int_values = map(int, re.findall(r'\d+', value))
                    int_values[:] = [x*1000 if x<1000 else x for x in int_values]
                    # print int_values
                    # print '-----------'
                    return max(int_values)
                except ValueError:
                    return 0

class ConvertKiloValuesIntoInteger(object):
    # re.sub(r'([0-9]*)K', r'\g<1>000'

    def __call__(self, values):
        for value in values:
            with_compressed_numbers = re.sub(r'([0-9]*) ([0-9]*)', r'\1\2', value)
            yield re.sub(r'([0-9]*)K', r'\g<1>000', with_compressed_numbers)


class TakeLastNotEmpty(TakeFirst):

    def __init__(self, prefix='', suffix=''):
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, values):
        for value in reversed(values):
            if 'SET_EMPTY'==value:
                return ''
            elif value is not None and value!='':
                return value

class TakeFirstOrEmpty(TakeFirst):

    def __init__(self, prefix='', suffix=''):
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, values):
        for value in values:
            if 'SET_EMPTY'==value:
                return ''
            elif value is not None:
                return value


class TakeCompletedFirstOrEmpty(TakeFirst):

    def __init__(self, prefix='', suffix=''):
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, values):
        for value in values:
            if 'SHOW_EVEN_IF_EMPTY'==value:
                return ''
            if value is not None and value!='':
                return self.prefix+value+self.suffix
        return ''

class JobPostLoader(ItemLoader):

    default_input_processor = MapCompose()
    default_output_processor = TakeFirstNotEmpty()

    url_out = TakeCompletedFirstOrEmpty('http://cadres.apec.fr/offres-emploi-cadres/0_0_0_', '__________')

    company_logo_url_out = TakeCompletedFirstOrEmpty('http://www.apec.fr')

    ref_company_out = TakeCompletedFirstOrEmpty()

    company_out = TakeFirstNotEmpty()

    desc_text_out = Join()
    desc_html_out = Join()

    salary_min_in = ConvertKiloValuesIntoInteger()
    salary_min_out = TakeFirstSalaryIntValue()

    salary_max_in = ConvertKiloValuesIntoInteger()
    salary_max_out = TakeLastSalaryIntValue()


class JobPost(Item):
    title = Field() # Intitulé APEC
    url = Field() # An url to go directly to the post
    ref_apec = Field() # Reference APEC
    ref_company = Field() # Reference Société
    pub_date = Field() # Date de Publication 
    company = Field() # Société
    company_logo_url = Field() # Url du logo de la société
    # job_status = Field() # Statut lié au poste
    location = Field() # Lieu (région, ville ou autre)
    salary = Field() # True si la rémunération est indiquée
    salary_min = Field() # Fourchette basse de salaire (vide si with_salary est False)
    salary_max = Field() # Fourchette basse de salaire (vide si with_salary est False)

    # contact = Field() # Contact ("dossier suivi par")
    # desc_text = Field() # Contenu texte
    # desc_html = Field() # Contenu html brut
    



class ApecJobSpider(Spider):
    name = ('apec_job_spider')
    nb = 0

    start_urls = ['http://cadres.apec.fr/MesOffres/RechercheOffres/ApecRechercheOffre.jsp?keywords=python']

    def __init__(self, page=0, *args, **kwargs):
        super(ApecJobSpider, self).__init__(*args, **kwargs)
        self.search_result_url_tpl = 'http://cadres.apec.fr/%s'
        self.job_url_tpl = 'http://cadres.apec.fr/offres-emploi-cadres/0_0_0_%s__________'

    def parse(self, response):
        print 'PARSING PAGE %s' % response.url

        job_post_paths = response.xpath('//div[@id="offre-detail-title"]/h3/a/@href')
        # the path is something like 
        # /offres-emploi-cadres/0_0_18_121471250W__________offre-d-emploi-ingenieur-etudes-et-developpement-c-python-h-f.html?xtmc=python&xtnp=1&xtcr=19
        #
        # in this example, the unique id is "121471250W"
        #
        # And we want to get something like
        # /offres-emploi-cadres/0_0_0_121471250W__________
        for job_post_path in job_post_paths:
             ids = re.findall(r'_([0-9]{7,9}[a-zA-Z])__________', job_post_path.extract())
             if len(ids)>0:
                 id = ids[0]
                 job_url = self.job_url_tpl % id
                 # the job_url content is something like http://cadres.apec.fr/offres-emploi-cadres/0_0_0_121471250W__________
                 print 'about to scrap url: %s' % (job_url)
                 yield Request(job_url, self.parse_job_post)
                 time.sleep(1)

        next_path = response.xpath('//p[@class="pagesList"]/a[@class="lastItem"]/@href')[0].extract()
        next_results_url =  self.search_result_url_tpl % next_path
        yield Request(next_results_url, self.parse)
        time.sleep(1)

    def parse_job_post(self, response):
        print 'PARSING PAGE %s' % response.url

        remove_blanks_regexp = '\s*(.*)[\r\s]*'

        jpl = JobPostLoader(item=JobPost(), response=response)
        jpl.add_xpath('title', '//h1[@class="detailOffre"]/text()', re='.*offre :\s*(.*)')
        jpl.add_xpath('ref_apec', u'//table[@class="noFieldsTable"]/tr/th[.="Référence Apec :"]/following::td[1]/text()')

        jpl.add_xpath('url', u'//table[@class="noFieldsTable"]/tr/th[.="Référence Apec :"]/following::td[1]/text()', re='(.*)-.*-.*')

        jpl.add_xpath('ref_company', u'//table[@class="noFieldsTable"]/tr/th[.="Référence société :"]/following::td[1]/text()', re='\s*(.*)\s*')
        jpl.add_value('ref_company', 'SHOW_EVEN_IF_EMPTY')

        jpl.add_xpath('company', u'//table[@class="noFieldsTable"]/tr/th[.="Société :"]/following::td[1]/text()', re=remove_blanks_regexp)
        jpl.add_xpath('pub_date', u'//table[@class="noFieldsTable"]/tr/th[.="Date de publication :"]/following::td[1]/text()', re=remove_blanks_regexp)
        # jpl.add_xpath('job_status', u'//table[@class="noFieldsTable"]/tr/th[.="Statut :"]/following::td[1]/text()', re=remove_blanks_regexp)
        jpl.add_xpath('location', u'//table[@class="noFieldsTable"]/tr/th[.="Lieu :"]/following::td[1]/text()', re=remove_blanks_regexp)
        # jpl.add_xpath('contact', u'//table[@class="noFieldsTable"]/tr/th[.="Dossier suivi par :"]/following::td[1]/text()', re=remove_blanks_regexp)

        jpl.add_xpath('company_logo_url', u'//table[@class="noFieldsTable"]/tr/th[.="Société :"]/following::td[1]/img[1]/@src')
        jpl.add_value('company_logo_url', 'SHOW_EVEN_IF_EMPTY')

        jpl.add_xpath('salary', u'//table[@class="noFieldsTable"]/tr/th[.="Salaire :"]/following::td[1]/text()', re=remove_blanks_regexp)
        jpl.add_xpath('salary_min', u'//table[@class="noFieldsTable"]/tr/th[.="Salaire :"]/following::td[1]/text()')
        jpl.add_xpath('salary_max', u'//table[@class="noFieldsTable"]/tr/th[.="Salaire :"]/following::td[1]/text()')

        yield jpl.load_item()
