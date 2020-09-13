from lxml import etree
from urllib import request
from time import mktime
import datetime
from math import ceil

from app import db
from app.models import News

xparser = etree.XMLParser()
hparser = etree.HTMLParser()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
}

def convert_date(s, unix=False, antara=False):
    if antara:
        # print(s)
        # s = s[7:-4]
        # print(s)
        # print(type(s))
        # s= s.lstrip()
        dt_format = "%d %B %Y %H:%M"
    else:
        dt_format = "%a, %d %b %Y %H:%M:%S %z"
    dt = datetime.datetime.strptime(s, dt_format)

    if unix:
        return mktime(dt.timetuple())

    return dt

def join_string(s, separator=''):
    return separator.join(s)

def get_antaranews_pages(total,per_page=10):
    return ceil(total / per_page)

def check_duplicate(url):
    res = News.query.filter_by(url=url).count()
    return res == 0

def parse_antara(url):
    req = request.Request(url, headers=headers)
    res = request.urlopen(req)
    htree = etree.parse(res, hparser)

    # total_news = htree.xpath('//h1[@class="block-title"]/span/text()')[0]
    # total_news = total_news[26:-8]
    # total_news = int(total_news)

    title = htree.xpath('//article[@class="simple-post simple-big clearfix"]/header/h3/a/@title')
    link = htree.xpath('//article[@class="simple-post simple-big clearfix"]/header/h3/a/@href')

    for i,l in enumerate(link):
        
        if check_duplicate(l):
            req = request.Request(l,headers=headers)
            resp = request.urlopen(req)
            article_ts = htree.xpath('//span[@class="article-date"]/text()')

            db.session.add(
                News(
                    title=title[i],
                    url=l,
                    content=join_string( htree.xpath('//div[@class="post-content clearfix"]/text()') ),
                    article_ts=convert_date(article_ts[0], unix=True, antara=True),
                    published_date=convert_date(article_ts[0], antara=True)
                )
            )

            print(htree.xpath('//div[@class="post-content clearfix"]/text()'))
    
    db.session.commit()
    


def parse(url):
    req = request.Request(url,headers=headers)
    res = request.urlopen(req)
    xtree = etree.parse(res, xparser)

    title = xtree.xpath('//item/title/text()')
    link = xtree.xpath('//item/link/text()')
    article_ts = xtree.xpath('//item/pubDate/text()')

    for i,l in enumerate(link):
        if check_duplicate(l):
            full_link = l+"?page=all"
            req = request.Request(full_link, headers=headers)
            resp = request.urlopen(req)
            htree = etree.parse(resp, hparser)

            db.session.add(
                News(
                    title=title[i],
                    url=full_link,
                    summary=join_string( htree.xpath('//h4[@class="hide"]/text()') ),
                    content=join_string( htree.xpath('//div[@class="side-article txt-article"]/p[not(contains(text(),"\xa0"))]/text()') ),
                    article_ts=convert_date(article_ts[i], unix=True),
                    published_date=convert_date(article_ts[i])
                )
            )

    db.session.commit()


if __name__ == "__main__":
    print(parse('https://www.tribunnews.com/rss', 'app/tribun'))
