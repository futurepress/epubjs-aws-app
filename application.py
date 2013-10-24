#! /usr/local/bin/python
import os
import xml.etree.ElementTree as ET

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
def books():

    if request.method == 'POST':
        # POST from book input form

        book_url = request.form.get('book_url', None)
        book_file = request.files.get('file', None)

        if book_url:
            # POST is a book url
            try:
                book = Book(book_url=book_url)
            except ValidationError as e:
                return render_template("404.html", error_msg=e)

            book_location = book.file_dir[:-1]
            return redirect('/book/'+book_location)

        elif book_file:
            # POST is a epub file upload
            if book_file.content_type == 'application/epub+zip':
                book = Book(book_file.filename, book_file=book_file)
                book_location = book.file_dir[:-1]
                return redirect('/book/'+book_location)
            else:
                return render_template("404.html", error_msg="Invalid Epub Uploaded")

        else:
            return render_template("404.html", error_msg="Not a valid Gutenberg URL")

    if request.method == 'GET':
        # GET /books returns JSON of books in S3
        # namespaces used by epub opf file
        namespaces = { 'opf': '{http://www.idpf.org/2007/opf}',
                        'dc': '{http://purl.org/dc/elements/1.1/}'
                    }

        conn = S3Connection(access, secret)
        bucket = conn.get_bucket('epubjs.books')

        # books list to return as JSON
        books = []

        for prefix in bucket.list(delimiter='/'): 
            book = { 'url': prefix.name[:-1] }
            for key in bucket.list(prefix=prefix.name):
                if key.name.endswith('content.opf') or key.name.endswith('package.opf'):
                    # Parse content.opf to find title, author, rights and cover
                    root = ET.fromstring(key.get_contents_as_string())
                    title = root.find('{opf}metadata/{dc}title'.format(**namespaces))
                    if title is not None:
                        book['title'] = title.text
                    author = root.find('{opf}metadata/{dc}creator'.format(**namespaces))
                    if author is not None:
                        book['author'] = author.text
                    rights = root.find('{opf}metadata/{dc}rights'.format(**namespaces))
                    if rights is not None:
                        book['rights'] = rights.text.lower()
                    # cover in the manifest does not contain the complete path to the coverpage...
                    #cover = root.find("{opf}manifest/*[@id='coverpage']".format(**namespaces))
                    #if cover is not None:
                    #    book['cover'] = cover.attrib['href']

                elif key.name.endswith('cover.jpg'):
                    # find file in book bucket that endswith cover.jpg (assume this is the cover)
                    book['cover'] = key.name

            # If book rights has public domain, this book is ok to return in JSON library list
            if 'public domain' in book['rights']:
                books.append(book)

        return jsonify(books=books)

@app.route('/book/<book>/<path:reader_locatiion>', methods=['GET'])
@app.route('/book/<book>/', methods=['GET'])
@app.route('/book/<book>', methods=['GET'])
def book(book=None, reader_locatiion=None):

    if book:
        # /book/<book>renders the reader with the correct book_location
        book_location = '/book/'+book+'/'
        book_assets = '../../s3/'+book+'/'
        app.logger.debug(book_location)
        return render_template("book_epubjs.html", book_location=book_location, book_assets=book_assets)

    else:
        return render_template("404.html", error_msg="URL Not Found")

@app.route('/s3/<path:resource_location>', methods=['GET'])
def resource(resource_location=None):

    if resource_location:
        # When epub.js requests book resources at /book/book_name/resource_location
        # get them from s3
        #app.logger.debug('/'+str(book) +'/'+resource_location)
        conn = S3Connection(access, secret)
        bucket = conn.get_bucket('epubjs.books')
        k = bucket.get_key('/'+resource_location)

        resp = make_response(k.get_contents_as_string())
        if k.content_type:
            resp.headers['Content-Type'] = k.content_type

        return resp

if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
