from app import app, db
from app.models import News
from flask import render_template

@app.route('/')
def index():

    return render_template('index.html')