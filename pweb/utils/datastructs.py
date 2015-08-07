#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = [
    "Storage", "storage",
    "JsonDict", "AttrDict"
    "threadeddict", "ThreadedDict"
]

import encoding

try: from threading import local as threadlocal
except ImportError: from python23 import threadlocal

class SQLRow:
    """
    A SQLRow object is like list and dict except `obj.foo` and `obj['foo']` can be used.
    
        >>> o = sqlrow([('a',1),('b',2)])
        >>> o.a
        1
        >>> o[0]
        1
        >>> o['a']
        1
        >>> o.b
        2
        >>> o[1]
        2
        >>> o['b']
        2
    """
    def __init__(self, zips):
        if not isinstance(zips, (list, tuple)): 
            raise TypeError, "SQLRow Argv must a zip list!"
        self.cursor_description = [x[0] for x in zips]
        self._vars = dict(zips)

    def __getitem__(self, i):
        if isinstance(i, int): 
            return self._vars[self.cursor_description[i]]
        if isinstance(i, str):
            return self._vars[i]
        raise TypeError, "sequence must be integer or 'str'"

    def __getattr__(self, name):
        if self._vars.has_key(name):
            return self._vars[name]
        return None

    def __len__(self):
        return len(self.cursor_description)

    def __repr__(self):
        return '<SQLRow '+ [self._vars[x] for x in self.cursor_description].__repr__() +'>'

    def __str__(self):
        return '<SQLRow '+ [self._vars[x] for x in self.cursor_description].__repr__() +'>'

    def __getstate__(self):
        _desc = self.cursor_description
        _vars = [self._vars[x] for x in _desc]
        return dict(cursor_description=_desc, vars=_vars)

    def __setstate__(self, state):
        self.__init__(zip(state['cursor_description'], state['vars']))

    def __nonzero__(self):
        return len(self.cursor_description) > 0

sqlrow = SQLRow

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
    
        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'
    
    """
    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __repr__(self):     
        return '<Storage ' + dict.__repr__(self) + '>'

storage = Storage

class JsonDict(Storage):
    def __repr__(self):
        return '<JsonDict ' + dict.__repr__(self) + '>'

jsondict = JsonDict

class AttrDict(Storage):
    def __getattr__(self, key): 
        if self.has_key(key):
            return self[key]
        return None

    def __repr__(self):
        return '<AttrDict ' + dict.__repr__(self) + '>'

attrdict = AttrDict

def storify(mapping, *requireds, **defaults):
    """
    Creates a `storage` object from dictionary `mapping`, raising `KeyError` if
    d doesn't have all of the keys in `requireds` and using the default 
    values for keys found in `defaults`.

    For example, `storify({'a':1, 'c':3}, b=2, c=0)` will return the equivalent of
    `storage({'a':1, 'b':2, 'c':3})`.
    
    If a `storify` value is a list (e.g. multiple values in a form submission), 
    `storify` returns the last element of the list, unless the key appears in 
    `defaults` as a list. Thus:
    
        >>> storify({'a':[1, 2]}).a
        2
        >>> storify({'a':[1, 2]}, a=[]).a
        [1, 2]
        >>> storify({'a':1}, a=[]).a
        [1]
        >>> storify({}, a=[]).a
        []
    
    Similarly, if the value has a `value` attribute, `storify will return _its_
    value, unless the key appears in `defaults` as a dictionary.
    
        >>> storify({'a':storage(value=1)}).a
        1
        >>> storify({'a':storage(value=1)}, a={}).a
        <Storage {'value': 1}>
        >>> storify({}, a={}).a
        {}
        
    Optionally, keyword parameter `_unicode` can be passed to convert all values to unicode.
    
        >>> storify({'x': 'a'}, _unicode=True)
        <Storage {'x': u'a'}>
        >>> storify({'x': storage(value='a')}, x={}, _unicode=True)
        <Storage {'x': <Storage {'value': 'a'}>}>
        >>> storify({'x': storage(value='a')}, _unicode=True)
        <Storage {'x': u'a'}>
    """
    _unicode = defaults.pop('_unicode', False)

    # if _unicode is callable object, use it convert a string to unicode.
    to_unicode = encoding.safeunicode
    if _unicode is not False and hasattr(_unicode, "__call__"):
        to_unicode = _unicode
    
    def unicodify(s):
        if _unicode and isinstance(s, str): 
            return to_unicode(s)
        else: 
            return s

    def getvalue(x):
        if hasattr(x, 'file') and hasattr(x, 'value'):
            if hasattr(x, 'filename'): # if the field is an upload file then return x
                if not x.filename is None:
                    return x
            return x.value
        elif hasattr(x, 'value'):
            return unicodify(x.value)
        else:
            return unicodify(x)

    def intget(integer, default=None):
        try:
            return int(integer)
        except (TypeError, ValueError):
            return default or integer

    stor = Storage()

    for key in requireds + tuple(mapping.keys()):
        value = mapping[key]
        if isinstance(value, list):
            if isinstance(defaults.get(key), list):
                value = [getvalue(x) for x in value]
            else:
                value = value[-1]
        if not isinstance(defaults.get(key), dict):
            value = getvalue(value)
            if isinstance(defaults.get(key), int):
                value = intget(value)
        if isinstance(defaults.get(key), list) and not isinstance(value, list):
            value = [value]
        setattr(stor, key, value)

    for (key, value) in defaults.iteritems():
        result = value
        if hasattr(stor, key): 
            result = stor[key]
        if value == () and not isinstance(result, tuple): 
            result = (result,)
        setattr(stor, key, result)
    
    return stor

class ThreadedDict(threadlocal):
    """
    Thread local storage.
    
        >>> d = ThreadedDict()
        >>> d.x = 1
        >>> d.x
        1
        >>> import threading
        >>> def f(): d.x = 2
        ...
        >>> t = threading.Thread(target=f)
        >>> t.start()
        >>> t.join()
        >>> d.x
        1
    """
    _instances = set()
    
    def __init__(self):
        ThreadedDict._instances.add(self)
        
    def __del__(self):
        ThreadedDict._instances.remove(self)
        
    def __hash__(self):
        return id(self)
    
    def clear_all():
        """Clears all ThreadedDict instances.
        """
        for t in list(ThreadedDict._instances):
            t.clear()
    clear_all = staticmethod(clear_all)
    
    # Define all these methods to more or less fully emulate dict -- attribute access
    # is built into threading.local.

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __contains__(self, key):
        return key in self.__dict__

    has_key = __contains__
        
    def clear(self):
        self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def items(self):
        return self.__dict__.items()

    def iteritems(self):
        return self.__dict__.iteritems()

    def keys(self):
        return self.__dict__.keys()

    def iterkeys(self):
        return self.__dict__.iterkeys()

    iter = iterkeys

    def values(self):
        return self.__dict__.values()

    def itervalues(self):
        return self.__dict__.itervalues()

    def pop(self, key, *args):
        return self.__dict__.pop(key, *args)

    def popitem(self):
        return self.__dict__.popitem()

    def setdefault(self, key, default=None):
        return self.__dict__.setdefault(key, default)

    def update(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __repr__(self):
        return '<ThreadedDict %r>' % self.__dict__

    __str__ = __repr__

threadeddict = ThreadedDict