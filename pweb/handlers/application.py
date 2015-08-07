#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, traceback
import types, itertools
from pweb import utils, conf, http
from pweb.handlers import wsgi, wsgiserver
from pweb.utils.datastructs import storage
from pweb.middleware import session
from pweb.db import database

class application:
    def __init__(self, fvars={}, autoreload=None):
        conf.settings.configure(fvars)

        if autoreload is None:
            autoreload = conf.settings.DEBUG
        self.init_mapping()
        self.fvars = fvars
        self.processors = []
        self.deploy_path = conf.settings.DEPLOY_PATH.strip()

        if autoreload:
            self.add_processor(loadhook(Reloader()))
            self.add_processor(loadhook(self.init_mapping))

        http.session = self.make_session()

    def _cleanup(self):
        utils.datastructs.ThreadedDict.clear_all()

    def init_mapping(self):
        mod = utils.importlib.import_module(".urls", conf.settings.APP_NAME)
        if hasattr(mod, "urlpatterns"):
            mapping = mod.urlpatterns
        else:
            mapping = ()
        if type(mapping) is dict:
            mapping = list(sum(mapping.items(),())) 
        self.mapping = list(utils.group(mapping, 2))

    def make_session(self):
        name = conf.settings.SESSION_STORE
        cfg = conf.settings.SESSION_STORE_CONFIG
        if name is None:
            return None
        elif name in ['DiskStore', 'ShelfStore']:
            store = getattr(session, name)(cfg.get('path', '/temp'))
        elif name in ['DBStore']:
            params = dict(dbn='ENGINE', pw='PASSWORD', user='USER', db='NAME', host='HOST', port='PORT')
            db = database(**dict([(k, cfg.get(v)) for k, v in params.iteritems() if not cfg.get(v) is None]))
            store = getattr(session, name)(db, cfg.get('TABLE_NAME','session'))
        else:
            raise AttributeError, "SESSION_STORE `%s` is in vaild"% name
        return session.Session(self, store)

    def add_mapping(self, pattern, classname):
        self.mapping.append((pattern, classname))

    def add_processor(self, processor):
        self.processors.append(processor)

    def handle_with_processors(self):
        def process(processors):
            try:
                if processors:
                    p, processors = processors[0], processors[1:]
                    return p(lambda: process(processors))
                else:
                    return self.handle()
            except http.HTTPError:
                raise
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                print >> http.debug, traceback.format_exc()
                raise self.internalerror()

        return process(self.processors)

    def is_class(self, o):
        return isinstance(o, (types.ClassType, type))

    def is_function(self, o):
        return isinstance(o, (types.FunctionType, type))

    def wsgifunc(self, *middleware):
        """Returns a WSGI-compatible function for this application."""
        def peep(iterator):
            try: firstchunk = iterator.next()
            except StopIteration: firstchunk = ''
            return itertools.chain([firstchunk], iterator)

        def is_generator(x): return x and hasattr(x, 'next')

        def wsgi(env, start_resp):
            # clear threadlocal to avoid inteference of previous requests
            self._cleanup()

            self.load(env)

            try:
                # allow uppercase methods only
                if http.request.method.upper() != http.request.method:
                    raise http.nomethod()

                result = self.handle_with_processors()
                if isinstance(result, tuple) and len(result)==2:
                    content_type, result = result[0], [result[1]]
                    http.header("Content-type", content_type, unique=True)
                elif is_generator(result):
                    result = peep(result)
                else:
                    result = [result]
            except http.HTTPError, e:
                result = [e.data]

            result = utils.safestr(iter(result))

            status, headers = http.request.status, http.request.headers
            start_resp(status, headers)

            def cleanup():
                self._cleanup()
                yield '' # force this function to be a generator

            return itertools.chain(result, cleanup())

        for m in middleware:
            wsgi = m(wsgi)

        return wsgi

    def load(self, env):
        """Initializes request using env."""
        request = http.request
        request.clear()
        request.headers = []
        request.output = ''
        request.environ = request.env = request.META = storage(**env)
        request.host = env.get('HTTP_HOST')

        if env.get('wsgi.url_scheme') in ['http', 'https']:
            request.protocol = env['wsgi.url_scheme']
        elif env.get('HTTPS', '').lower() in ['on', 'true', '1']:
            request.protocol = 'https'
        else:
            request.protocol = 'http'
        request.homedomain = request.protocol + '://' + env.get('HTTP_HOST', '[unknown]')
        request.homepath = env.get('REAL_SCRIPT_NAME', env.get('SCRIPT_NAME', ''))
        request.home = request.homedomain + request.homepath
        request.realhome = request.home
        request.ip = env.get('HTTP_X_REAL_IP', env.get('REMOTE_ADDR'))
        request.method = env.get('REQUEST_METHOD')
        request.path = env.get('PATH_INFO')
        if env.get('SERVER_SOFTWARE', '').startswith('lighttpd/'):
            request.path = lstrips(env.get('REQUEST_URI').split('?')[0], request.homepath)
            request.path = urllib.unquote(request.path)

        if env.get('QUERY_STRING'):
            request.query = '?' + env.get('QUERY_STRING', '')
        else:
            request.query = ''

        request.fullpath = request.path + request.query
        
        for k, v in request.iteritems():
            if isinstance(v, str):
                request[k] = v.decode('utf-8', 'replace') 

        request.status = '200 OK'

    def handle(self):
        fn, args = self._match(self.mapping, http.request.path)
        return self._delegate(fn, self.fvars, args)

    def _match(self, mapping, value):
        for pat, what in mapping:
            if pat.startswith('^'): pat = pat[1:]
            if pat.endswith('$'): pat = pat[:-1]
            if self.deploy_path != '/':
                if self.deploy_path.endswith('/'):
                    if pat.startswith('/'):
                        pat = "%s%s"% (self.deploy_path, pat[1:])
                    else:
                        pat = "%s%s"% (self.deploy_path, pat)
                else:
                    if pat.startswith('/'):
                        pat = "%s%s"% (self.deploy_path, pat)
                    else:
                        pat = "%s/%s"% (self.deploy_path, pat)

            if isinstance(what, basestring):
                what, result = utils.re_subm('^' + pat + '$', what, value)
            else:
                result = utils.re_compile('^' + pat + '$').match(value)

            if result: # it's a match
                return what, [x for x in result.groups()]

        return None, None

    def _delegate(self, f, fvars, args=[]):
        def handle_class(cls):
            meth = http.request.method
            if meth == 'HEAD' and not hasattr(cls, meth):
                meth = 'GET'
            if not hasattr(cls, meth):
                raise http.nomethod(cls)
            tocall = getattr(cls(), meth)
            c = tocall.func_code.co_argcount
            if (c - len(args)) > 1:
                return tocall(http.request, *args)
            else:
                return tocall(*args)

        def handle_function(tocall):
            c = tocall.func_code.co_argcount
            if (c - len(args)) > 0:
                return tocall(http.request, *args)
            else:
                return tocall(*args)

        def handle_object(o):
            if self.is_function(o):
                return handle_function(o)
            if self.is_class(o):
                return handle_class(o)
            return http._InternalError("Not Support Object Type:%s"% type(o))

        if f is None:
            raise self.notfound()
        elif self.is_function(f):
            return handle_function(f)
        elif self.is_class(f):
            return handle_class(f)
        elif isinstance(f, basestring):
            if f.startswith('redirect '):
                url = f.split(' ', 1)[1]
                if http.request.method == "GET":
                    x = http.request.env.get('QUERY_STRING', '')
                    if x: url += '?' + x
                raise http.redirect(url)
            elif '.' in f:
                mod, cls = f.rsplit('.', 1)
                mod = utils.importlib.import_module(mod,conf.settings.APP_NAME)
                cls = getattr(mod, cls)
            else:
                cls = fvars[f]
            return handle_object(cls)
        elif hasattr(f, '__call__'):
            return f()
        else:
            return self.notfound()

    def run(self, *middleware):
        return wsgi.runwsgi(self.wsgifunc(*middleware))

    def stop(self):
        return wsgiserver.stop()

    def notfound(self):
        return http._NotFound()

    def internalerror(self):
        if conf.settings.DEBUG:
            from pweb.http import debugerror
            return debugerror.debugerrorRsp()
        else:
            return http._InternalError()


def loadhook(h):
    """
    Converts a load hook into an application processor.
    
        >>> app = auto_application()
        >>> def f(): "something done before handling request"
        ...
        >>> app.add_processor(loadhook(f))
    """
    def processor(handler):
        h()
        return handler()
        
    return processor
    
def unloadhook(h):
    """
    Converts an unload hook into an application processor.
    
        >>> app = auto_application()
        >>> def f(): "something done after handling request"
        ...
        >>> app.add_processor(unloadhook(f))
    """
    def processor(handler):
        try:
            result = handler()
            is_generator = result and hasattr(result, 'next')
        except:
            # run the hook even when handler raises some exception
            h()
            raise

        if is_generator:
            return wrap(result)
        else:
            h()
            return result
            
    def wrap(result):
        def next():
            try:
                return result.next()
            except:
                # call the hook at the and of iterator
                h()
                raise

        result = iter(result)
        while True:
            yield next()
            
    return processor

def autodelegate(prefix=''):
    def internal(self, *arg):
        if len(arg) > 0:
            fixact, args = arg[0], list(arg[1:])
        else:
            fixact, args = "", []

        if '/' in fixact:
            first, rest = fixact.split('/',1)
            func = prefix + first
            args.insert(0, '/'+rest)
        else:
            func = prefix + fixact

        if hasattr(self, func):
            try:
                return getattr(self, func)(*args)
            except TypeError:
                raise http.notfound()
        else:
            raise http.notfound()
    return internal

class Reloader:
    if sys.platform.startswith('java'):
        SUFFIX = '$py.class'
    else:
        SUFFIX = '.pyc'
    
    def __init__(self):
        self.mtimes = {}

    def __call__(self):
        for mod in sys.modules.values():
            self.check(mod)

    def check(self, mod):
        # jython registers java packages as modules but they either
        # don't have a __file__ attribute or its value is None
        if not (mod and hasattr(mod, '__file__') and mod.__file__):
            return

        try: 
            mtime = os.stat(mod.__file__).st_mtime
        except (OSError, IOError):
            return
        if mod.__file__.endswith(self.__class__.SUFFIX) and os.path.exists(mod.__file__[:-1]):
            mtime = max(os.stat(mod.__file__[:-1]).st_mtime, mtime)
            
        if mod not in self.mtimes:
            self.mtimes[mod] = mtime
        elif self.mtimes[mod] < mtime:
            try: 
                reload(mod)
                self.mtimes[mod] = mtime
            except ImportError: 
                pass
