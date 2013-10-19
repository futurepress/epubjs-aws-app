#! /usr/local/bin/python
import os
import flask
from flask import (
    Flask,
    request,
    render_template,
    redirect
)

import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from settings import access, secret

S3Static = 'http://epubjs.books.s3.amazonaws.com'
from book import Book, ValidationError

application = Flask(__name__)
app = application
app.debug = True

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        book_url = request.form['book_input']

        try:
            book_obj = Book(book_url, unzipped=True)
        except ValidationError as e:
            return str(e)

        return redirect('/book/'+book_obj.book_id)

    else:
        return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():

    book_file = request.files['file']
    book = Book(book_file=book_file)
    book_location = book.file_dir[:-1]
    return redirect('/book/'+book_location)

@app.route('/book/<int:book>')
@app.route('/book/<int:book>/<path:resource_location>', methods=['GET'])
def book(book=None, resource_location=None):

    if book and not resource_location:
        book_location = 'book/'+str(book)+'/'

        return render_template("book.html", book_location=book_location)

    elif book and resource_location:
        #app.logger.debug('/'+str(book) +'/'+resource_location)
        conn = S3Connection(access, secret)
        bucket = conn.get_bucket('epubjs.books')
        k = Key(bucket=bucket, name='/'+str(book)+'/'+resource_location)
        #app.logger.debug(k)

        meta_data = k.get_metadata('Content-Type')
        app.logger.debug(meta_data)

        return k.get_contents_as_string()
    else:
        return render_template("404.html")

if __name__ == "__main__":

    application.run(host='0.0.0.0', debug=True)
