#! /usr/local/bin/python
import os
import flask
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    jsonify,
    make_response
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

@app.route('/', methods=['GET'])
def index():

    return render_template("index.html")

@app.route('/books', methods=['GET','POST'])
def upload():

    if request.method == 'POST':
        # POST from book input form
        if request.files['file']:
            # POST is a file upload
            book_file = request.files['file']
            if book_file.content_type == 'application/epub+zip':
                book = Book(book_file.filename, book_file=book_file)
                book_location = book.file_dir[:-1]
                return redirect('/book/'+book_location)
            else:
                return "Invalid Epub Uploaded"

    if request.method == 'GET':
        # GET books returns json of books in S3
        conn = S3Connection(access, secret)
        bucket = conn.get_bucket('epubjs.books')
        books = []
        for prefix in bucket.list(delimiter='/'):
            cover_page = ''
            for key in bucket.get_all_keys(prefix=prefix.name):
                if key.name.endswith('cover.jpg'):
                    cover_page = key.name
            books.append({ 'title':prefix.name[:-1], 'cover_url': cover_page })

        return jsonify(books=books)

@app.route('/book/<book>', methods=['GET'])
@app.route('/book/<book>/<path:resource_location>', methods=['GET'])
def book(book=None, resource_location=None):

    if book and not resource_location:
        book_location = 'book/'+book+'/'
        app.logger.debug(book_location)
        return render_template("book.html", book_location=book_location)

    elif book and resource_location:
        #app.logger.debug('/'+str(book) +'/'+resource_location)
        conn = S3Connection(access, secret)
        bucket = conn.get_bucket('epubjs.books')
        k = bucket.get_key('/'+str(book)+'/'+resource_location)

        resp = make_response(k.get_contents_as_string())
        if k.content_type:
            resp.headers['Content-Type'] = k.content_type

        return resp
    else:
        return "bad url"

if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
