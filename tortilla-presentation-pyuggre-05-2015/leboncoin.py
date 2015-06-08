# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import tortilla
import xmltodict

def show_item(item):
    print '%s (%s)' % (item.title, item.price)
    print '-> image:    %s' % (item.image)
    print '-> url:      %s' % (item.url)
    print '-> location: %s' % (item.location)
    print

def parse_leboncoin_result(xml_input):
    res = []
    soup = BeautifulSoup(xml_input)

    for soupitem in soup.select('div.list-lbc a'):
        try:
            image = soupitem.select('img')[0]['src']
        except:
            image = ''

        try:
            location = ''.join(line.lstrip().rstrip() for line in soupitem.select('div.placement')[0].text)
        except:
            location = ''

        try:
            price = soupitem.select('div.price')[0].text.lstrip().rstrip()
        except:
            price = ''
        item = dict(title=soupitem['title'], url=soupitem['href'],
                    image=image, location=location, price=price)

        res.append(item)

    return res


if __name__=='__main__':

    tortilla.formats.register('leboncoin_xml', parse_leboncoin_result, xmltodict.unparse)

    lbc = tortilla.wrap('http://www.leboncoin.fr/', format='leboncoin_xml', delay=5)

    # recherche de sacs à dos sur Grenoble
    result = lbc('annonces').offres.get('rhone_alpes',
                            params=dict(f='a', th=1,
                                        q=u'sac à dos',
                                        location='Grenoble 38000,Grenoble 38100'))

    for item in result:
        show_item(item)

    # Recherche de ventes immobilières à Crolles et Bernin
    result = lbc('ventes_immobilieres').offres.get(
        'rhone_alpes',
        params=dict(f='a', th=1, q=u'',
                    location='Crolles 38190,Bernin 38190'))

    for item in result:
        show_item(item)
