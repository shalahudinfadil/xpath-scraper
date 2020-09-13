from app import app, db
from app.models import News
from app import parser
from flask import render_template

@app.route('/')
def index():
    parser.parse("http://www.tribunnews.com/rss")
    parser.parse_antara("http://www.antaranews.com/indeks")
    news = News.query.order_by(News.article_ts.desc()).all()
    return render_template('index.html', news=news)