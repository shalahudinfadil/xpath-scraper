from lxml import etree
from urllib import request
from time import mktime
import datetime
from math import ceil
from threading import Thread

from app import app, db
from app.models import News

# Init Parser untuk XML dan HTML
xparser = etree.XMLParser()
hparser = etree.HTMLParser()
parser_list = [xparser, hparser]


def convert_date(s, unix=False, antara=False):
    """Return = obyek datetime ATAU unix timestamps
     Parameter:
        s = string datetime
        unix = untuk menentukan apakah return obyek datetime (False) atau unix timestamps (True), default True
        antara = untuk menentukan apakah string datetime dari website antaranews, default False
    Melakukan konversi dari string datetime ke obyek datetime ATAU unix timestamps
    """
    if antara:
        s = s[8:-4]
        s = s.strip()
        dt_format = "%d %B %Y %H:%M"
    else:
        dt_format = "%a, %d %b %Y %H:%M:%S %z"
    dt = datetime.datetime.strptime(s, dt_format)

    if unix:
        return mktime(dt.timetuple())

    return dt
def join_string(s, separator=''):
    return separator.join(s)

def check_duplicate(url):
    """Return = True jika url belum ada di database
     Parameter:
        url = url sbg identifier entry news
    Melakukan pencarian entry news berdasarkan url (unique) untuk mengecek apakah sudah ada atau belum di database
    """
    res = News.query.filter_by(url=url).count()
    return res == 0

def request_page(url, pagetype='HTML', headers=None):
    """Return = Obyek Tree LXML dari page yang di-request
    Parameter: 
        url = url dari page, not null
        pagetype = tipe page yang di-request (HTML/XML), default HTML
        headers = headers untuk request yg dikirim, default None
    Melakukan request untuk url yang disediakan, lalu mem-parse page yang didapat menjadi Tree LXML untuk dilakukan scraping
    """
    if pagetype not in ['HTML', 'XML']:
        raise Exception(
            "Page Type must be either HTML or XML. Your value: {}".format(pagetype))

    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
        }

    req = request.Request(url)
    res = request.urlopen(req)
    parser = hparser if pagetype == 'HTML' else xparser

    return etree.parse(res, parser)


def parse_antara(url):
    """Return = None
     Parameter:
        url = url page yang ingin di scrape
    Melakukan scraping thd page indeks antaranews.com
    """
    htree = request_page(url)

    title = htree.xpath(
        '//article[@class="simple-post simple-big clearfix"]/header/h3/a/@title')
    link = htree.xpath(
        '//article[@class="simple-post simple-big clearfix"]/header/h3/a/@href')

    for i, l in enumerate(link):

        if check_duplicate(l):
            htree = request_page(l)
            article_ts = htree.xpath('//span[@class="article-date"]/text()')
            # XPath bagian kiri untuk page berita biasa Antara
            # XPath bagian kanan untuk page berita Video Antara
            content = htree.xpath(
                '//div[@class="post-content clearfix"]/text()|//div[@class="margin-top-15 margin-bottom-15 clearfix"]/text()|//div[@class="flex-caption"]/text()')

            db.session.add(
                News(
                    title=title[i],
                    url=l,
                    summary=content if isinstance(content,str) else content[0],
                    content=join_string(content),
                    article_ts=convert_date(article_ts[0], unix=True, antara=True),
                    published_date=convert_date(article_ts[0], antara=True)
                )
            )


def parse_tribun(url):
    """Return = None
     Parameter:
        url = url page yang ingin di scrape
    Melakukan scraping thd page rss feed tribunnews.com
    """
    xtree = request_page(url, pagetype='XML')

    title = xtree.xpath('//item/title/text()')
    link = xtree.xpath('//item/link/text()')
    article_ts = xtree.xpath('//item/pubDate/text()')

    for i, l in enumerate(link):
        # Untuk tribun, agar page berita menampilkan seluruh isi berita
        full_link = l+"?page=all"
        if check_duplicate(full_link):
            htree = request_page(full_link)

            db.session.add(
                News(
                    title=title[i],
                    url=full_link,
                    summary=join_string(htree.xpath(
                        '//h4[@class="hide"]/text()')),
                    content=join_string(htree.xpath(
                        '//div[@class="side-article txt-article"]/p[not(contains(text(),"\xa0"))]/text()')),
                    article_ts=convert_date(article_ts[i], unix=True),
                    published_date=convert_date(article_ts[i])
                )
            )


def parse(site, url):
    if site == "tribun":
        parse_tribun(url)
    elif site == "antara":
        parse_antara(url)

    db.session.commit()
