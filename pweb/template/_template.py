#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, cgi
import mimetypes
import __builtin__
from pweb.conf import settings
from pweb.utils import encoding, net

from _compiler import Compiler

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

class IncludePageError(Exception):
    pass

class Out(object):
    def __init__(self, template):
        self._template = template
        self._buf = StringIO()
        self._encoding = settings.DEFAULT_CHARSET

    def _str(self, text):
        if text is None:
            return ""
        elif isinstance(text, unicode):
            return text.encode(self._encoding)
        elif isinstance(text, str):
            return encoding.safeunicode(text).encode(self._encoding)
        else:
            return str(text)

    def write(self, *args, **kwargs):
        text = " ".join(args)
        escape = kwargs.get("escape", True)
        s = self._str(text)
        if escape:
            self._buf.write(cgi.escape(s))
        else:
            self._buf.write(s)

    def escape(self, txt):
        return net.websafe(txt)

    def str2hex(self, txt, slen=0):
        return encoding.str2hex(txt, slen)

    def safeutf8(self, txt, slen=0):
        return encoding.safeutf8(txt, slen)

    def include(self, path, *args, **kwargs):
        escape = kwargs.pop("escape", False)
        path = os.path.join(os.path.dirname(os.path.abspath(self._template.filename)), path)
        _template = Template(open(path).read(), filename=path, \
                             env =self._template.env, fvars=self._template.fvars)
        self.write(_template(*args, **kwargs), escape=escape)

    def getvalue(self):
        return self._buf.getvalue()

class Template:
    CONTENT_TYPES = {
        '.html'     : 'text/html; charset=utf-8',
        '.xhtml'    : 'application/xhtml+xml; charset=utf-8',
        '.txt'      : 'text/plain',
    }
    fvars           = {}
    env             = {}

    def __init__(self, text, filename='<template>', env=None, fvars=None):
        self._compile_class  = Compiler(not settings.DEBUG)
        self.filename = filename

        if isinstance(env, dict):
            self.env = dict(self.env, **env)
        if isinstance(fvars, dict): 
            self.fvars = dict(self.fvars, **fvars)

        text = Template.normalize_text(text)
        self.source_code = self._compile_class(text)

        _, ext = os.path.splitext(filename)
        self.content_type = self.CONTENT_TYPES.get(ext, settings.DEF_CONTENT_TYPES)

    def normalize_text(text):
        """Normalizes template text by correcting \r\n, tabs and BOM chars."""
        text = text.replace('\r\n', '\n').replace('\r', '\n').expandtabs()
        if not text.endswith('\n'):
            text += '\n'

        # ignore BOM chars at the begining of template
        BOM = '\xef\xbb\xbf'
        if isinstance(text, str) and text.startswith(BOM):
            text = text[len(BOM):]

        return text
    normalize_text = staticmethod(normalize_text)

    def _f(self, env, fvars):
        def defined(v):
            return (v in env) or (v in fvars)
        return defined

    def _unf(self, env, fvars):
        def undefined(v):
            return not ((v in env) or (v in fvars))
        return undefined

    def make_env(self, out, *args, **kwargs):
        env = dict(self.env, **kwargs)
        return dict(env,
                        out         = out,
                        str2hex     = out.str2hex,
                        safeutf8    = out.safeutf8,
                        utf8        = out.safeutf8,
                        include     = out.include,
                        escape      = out.escape,
                        defined     = self._f(self.env, self.fvars),
                        undefined   = self._unf(self.env, self.fvars)
                      )

    def __call__(self, *args, **kwargs):
        out = Out(self)

        args = args[:2]
        if len(args) == 2:
            if isinstance(args[0], (str, unicode)):
                self.content_type = args[0].strip()
            if isinstance(args[1], dict):
                kwargs.update(args[1])

        if len(args) == 1:
            if isinstance(args[0], (str, unicode)):
                self.content_type = args[0].strip()
            if isinstance(args[0], dict):
                kwargs.update(args[0])

        self.content_type = kwargs.pop("Content_Type", None) or self.content_type

        self.fvars = dict(self.fvars, **kwargs)

        from pweb import http
        if 'headers' in http.request and self.content_type:
            http.header("Content-type", self.content_type, unique=True)

        env = self.make_env(out, *args, **self.fvars)
        if isinstance(self.source_code, (str, unicode)):
            code = compile(self.source_code, self.filename, 'exec')
        exec(code, env)
        return out.getvalue()