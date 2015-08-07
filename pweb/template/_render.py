#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob,itertools
from pweb import conf
from _template import Template

class BaseRender:
    def __init__(self, loc = "templates", cache=None, base=None, **kwargs):
        self._init_loc(loc)
        self._kwargs = kwargs

        if not cache:
            cache = not conf.settings.DEBUG

        if cache:
            self._cache = {}
        else:
            self._cache = None

        if base and not hasattr(base, "__call__"):
            self._base = lambda page: self._template(base)(page)
        else:
            self._base = base

    def _init_loc(self, loc):
        if len(loc)>0 and loc[0]=='/':
            self._loc = os.path.join(self.settings.APP_PATH, loc)
        elif len(loc)>1 and loc[1]==':':
            self._loc = os.path.join(self.settings.APP_PATH, loc)
        else:
            self._loc = loc

    def _lookup(self, name):
        path = os.path.join(self._loc, name)
        if os.path.isdir(path):
            return 'dir', path
        else:
            path = self._findfile(path)
            if path:
                return 'file', path
            else:
                return 'none', None

    def _load_template(self, name):
        kind, path = self._lookup(name)
        if kind == 'dir':
            return BaseRender(path, cache=self._cache is not None, **self._kwargs)
        elif kind == 'file':
            return Template(open(path).read(), filename=path, **self._kwargs)
        else:
            raise AttributeError, "No template named " + name

    def _endswith(self, v, *args):
        for arg in args:
            if v.endswith(arg): return True
        return False

    def _findfile(self, path_prefix): 
        p = [f for f in glob.glob(path_prefix + '.*') if not self._endswith(f, '~', '.bak', '.back')] # skip backup files
        p.sort() # sort the matches for deterministic order
        return p and p[0]

    def _template(self, name):
        if self._cache is not None:
            if name not in self._cache:
                self._cache[name] = self._load_template(name)
            return self._cache[name]
        else:
            return self._load_template(name)

    def __getattr__(self, name):
        t = self._template(name)
        if self._base and isinstance(t, Template):
            def template(*a, **kw):
                return self._base(t(*a, **kw))
            return template
        else:
            return self._template(name)

class Render:
    def __init__(self, locs = ("templates",), cache=None, base=None, render_handle=BaseRender, **kwargs):
        self._renders = []
        if isinstance(locs, basestring): locs = (locs,)

        for loc in locs:
            self._renders.append(render_handle(loc, cache, base, **kwargs))

    def __getattr__(self, name):
        for render in self._renders:
            try: return getattr(render, name)
            except: pass
        raise AttributeError, "No template named " + name

render = Render

def frender(filepath, **kwargs):
    templates = tuple(set((conf.settings.TEMPLATE_DIRS + conf.settings.TEMPLATE_PATH)))
    t_files = []
    for tmp in templates:
        _path = os.path.join(conf.settings.APP_PATH, tmp, filepath)
        if os.path.isfile(_path): t_files.append(_path)

    path = t_files and t_files[0]
    if not path:
        raise NameError, "No template named " + filepath

    return Template(open(path).read(), filename=path, **kwargs)