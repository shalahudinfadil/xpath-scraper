from app import db
from datetime import datetime

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, default='')
    url = db.Column(db.String(255), nullable=False, default='')
    content  = db.Column(db.Text)
    summary = db.Column(db.Text)
    article_ts = db.Column(db.BigInteger, nullable=False, default=0)
    published_date = db.Column(db.Date, nullable=True)
    inserted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return '<Artikel: {}, Publikasi: {}, Inserted: {}>'.format(self.title, self.published_date, self.inserted)