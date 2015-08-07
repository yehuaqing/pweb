#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import urllib, posixpath
from SimpleHTTPServer import SimpleHTTPRequestHandler
from pweb import utils, conf

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

server = None
b_gevent = False

def rungevent(func, addr=('localhost', 8000)):
    ret, _server = False, None
    try:
        from gevent import wsgi
        ret, _server = True, wsgi.WSGIServer(addr, func)
    except:
        pass

    print "*"*40
    if _server is None:
        print "*    Use wsgiref Server runing...      *"
    else:
        print "*    Use gevent Server runing...       *"
    print "*"*40

    return (ret, _server)

def runbase(func, addr=('localhost', 8000)):
    from wsgiref import simple_server as wsgi
    server = wsgi.WSGIServer(addr, wsgi.WSGIRequestHandler)
    server.set_app(func)
    return server

def runsimple(func, addr=("0.0.0.0", 8080)):
    global server, b_gevent

    #static root index options
    static_index = conf.settings.STATIC_INDEX

    #static root tuple
    static_root = list(set(conf.settings.STATIC_PATH + conf.settings.STATIC_DIRS))

    func = StaticMiddleware(func, index=static_index, prefix=static_root)
    b_gevent, server = rungevent(func, addr)
    if not b_gevent: server = runbase(func, addr)

    print "http://%s:%d/" % addr

    try: server.serve_forever()
    except: stop()

def stop():
    global server, b_gevent
    if server:
        if b_gevent:
            server.stop(10)
        else:
            server.shutdown()
    server = None

class StaticApp(SimpleHTTPRequestHandler):
    def __init__(self, environ, start_response, index=False):
        self.headers = []
        self.environ = environ
        self.start_response = start_response
        self.soft_ware = environ.get("SERVER_SOFTWARE","-")
        self.index = index
        self.deploy_path = conf.settings.DEPLOY_PATH.strip()

    def send_response(self, status, msg=""):
        self.status = str(status) + " " + msg

    def send_header(self, name, value):
        if name.lower() != 'connection' or \
          not self.soft_ware.startswith('WSGIServer'):  #if run as base, fix Connection set close
            self.headers.append((name, value))

    def end_headers(self): pass

    def address_string(self):
        host, port = self.client_address[:2]
        #return socket.getfqdn(host)
        return host

    def trans_path(self, path):
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.unquote(path))

        if self.deploy_path != '/' and path.startswith(self.deploy_path):
            path = path[len(self.deploy_path):]

        words = path.split('/')
        words = filter(None, words)

        path = conf.settings.HERE
        for word in words:
            path = os.path.join(path, word)
        return path

    def send_head(self):
        path = self.trans_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                if self.index:
                    return self.list_directory(path)
                else:
                    return self.do_forbidden_index()

        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return None

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except:
            self.send_error(403, "Access denied")
            return None

        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def do_forbidden_index(self):
        f = StringIO()

        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>403 Forbidden</title>\n")
        f.write("<body>\n<center><h1>403 Forbidden</h1></center>\n")
        f.write("<hr><center>%s</center>\n"% self.soft_ware)
        f.write("</body>\n</html>\n")

        length = f.tell()
        f.seek(0)

        self.send_response(403)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def __iter__(self):
        environ = self.environ

        self.path = environ.get('PATH_INFO', '')
        self.client_address = environ.get('REMOTE_ADDR','-'), \
                              environ.get('REMOTE_PORT','-')
        self.command = environ.get('REQUEST_METHOD', '-')

        from cStringIO import StringIO
        self.wfile = StringIO() # for capturing error

        try:
            path = self.translate_path(self.path)
            etag = '"%s"' % os.path.getmtime(path)
            client_etag = environ.get('HTTP_IF_NONE_MATCH')
            self.send_header('ETag', etag)
            if etag == client_etag:
                self.send_response(304, "Not Modified")
                self.start_response(self.status, self.headers)
                raise StopIteration
        except OSError:
            pass # Probably a 404

        f = self.send_head()
        self.start_response(self.status, self.headers)

        if f:
            block_size = 16 * 1024
            while True:
                buf = f.read(block_size)
                if not buf:
                    break
                yield buf
            f.close()
        else:
            value = self.wfile.getvalue()
            yield value

class StaticMiddleware:
    def __init__(self, app, index=False, prefix=('/static/','/media/','/favicon.ico')):
        self.app = app
        self.index = index
        self.prefix = prefix
        self.deploy_path = conf.settings.DEPLOY_PATH.strip()

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = self.normpath(path)
        b_static = False
        for fix in self.prefix:
            if self.chk_deploy_path(path, fix):
                b_static = True
                break

        if b_static:
            return StaticApp(environ, start_response, index=self.index)
        else:
            return self.app(environ, start_response)

    def chk_deploy_path(self, path, fix):
        if path.startswith(fix): 
            return True
        if self.deploy_path != '/':
            if path.startswith(self.deploy_path):
                dpath = path[len(self.deploy_path):]
                if dpath.startswith(fix):
                    return True           
        return False

    def normpath(self, path):
        path2 = posixpath.normpath(urllib.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2
