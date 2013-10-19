#! /usr/local/bin/python
from urllib2 import urlopen, HTTPError, Request
from urlparse import urlparse
import re
from zipfile import ZipFile
import StringIO
from mimetypes import guess_type

import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from settings import access, secret

S3Bucket = 'epubjs.books'

## also see gutenberg book mirror, where 135 =
## http://snowy.arsc.alaska.edu/gutenberg/cache/generated/135/pg135-images.epub
class Book():
    """ Book class 
    init with book_url to fetch epub file from url
    init with book_file hand an uploaded file
    """
    def __init__(self, book_url=None, book_file=None, unzipped=False):

        if book_file:
            self.zip_file = self.getZipFile(book_file)
            self.file_dir = self.getFileDir(self.zip_file)
            self.uploadS3(self.zip_file, self.file_dir) ## Only uploads unzipped epub
        
        if book_url:
            self.unzipped = unzipped
            self.url = self.completeUrl(book_url)
            ## fetch the epub file
            self.book, self.file_name = self.fetchBook(self.url)
            ## get book_id and future unzipped_dir_name from the file_name
            self.book_id = self.getBookId(self.file_name)

            ## store the book
            ## NOT IMPLEMENTED YET

    def getZipFile(self, book_file):
        return ZipFile(StringIO.StringIO(book_file.read()))

    def getFileDir(self, zip_file):

        file_dir = None

        for f in zip_file.filelist:
            m = re.match(r'([\d]+)', f.filename)
            if m and not file_dir:
                file_dir = m.group(0)

        return file_dir + '/'

    def uploadS3(self, zip_file, file_dir):
        for f in zip_file.filelist:

            file_mime = guess_type(f.filename)[0]

            conn = S3Connection(access, secret)
            bucket = conn.get_bucket(S3Bucket)

            k = Key(bucket)
            k.key = file_dir + f.filename

            if file_mime:
                k.set_metadata('Content-Type', file_mime)
            k.set_contents_from_string(zip_file.read(f))

    def completeUrl(self, book_url):

        if book_url[:7] != 'http://':
            url_str = 'http://' + book_url
        else:
            url_str = book_url

        return urlparse(url_str)

    def fetchBook(self, url):
        if '.epub' not in url.path:
            url_str = url.geturl()+'.epub'
        else:
            url_str = url.geturl()

        try:
            request = Request(url.geturl())
            request.add_header("User-Agent", "Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5")

            doc = urlopen(request)

        except HTTPError, e:
            print e.fp.read()

        return doc, self.getFileName(url)

    def getFileName(self, url):
        if '.epub' not in url.path:
            return url.path[url.path.rfind('/')+1:] + '.epub'
        else:
            return url.path[url.path.rfind('/')+1:]

    def getBookId(self, file_name):
        return file_name[:file_name.find('.')]

    def getDirName(self, book_file_name):
        book_dir_name = book_file_name[:book_file_name.find('.')]
        return book_dir_name + '/'

class ValidationError(Exception):
    pass
