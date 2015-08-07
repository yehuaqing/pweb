#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = [
    "desstr", "uniunknowstr", "safeunicode", "force_unicode",
    "uni2hex", "hex2uni", "str2hex",
    "safe_utf8chinese", "safeutf8","ischinese"
]

def desstr(s, encods=[]):
    if not encods: return s

    encoding = encods.pop()
    try: 
        return s.decode(encoding)
    except: 
        return desstr(s, encods)
    
def uniunknowstr(s):
    t = type(s)
    if t is unicode: 
        return s
    elif t in [int, float, bool]: 
        return unicode(s)
    elif hasattr(s, '__unicode__') or isinstance(s, unicode): 
        return unicode(s)
    else:
        return desstr(str(s), ['gbk', 'gb2312', 'mbcs', 'utf-8'])
        

def safeunicode(obj, encoding='utf-8'):
    """
    Converts any given object to unicode string.
    
        >>> safeunicode('hello')
        u'hello'
        >>> safeunicode(2)
        u'2'
        >>> safeunicode('\xe1\x88\xb4')
        u'\u1234'
    """
    t = type(obj)
    if t is unicode:
        return obj
    elif t is str:
        try: return obj.decode(encoding)
        except: return uniunknowstr(obj)
    elif t in [int, float, bool]:
        return unicode(obj)
    elif hasattr(obj, '__unicode__') or isinstance(obj, unicode):
        return unicode(obj)
    else:
        try: return str(obj).decode(encoding)
        except: return uniunknowstr(obj)

force_unicode = safeunicode

def uni2hex(c):
    hexchr = hex(ord(c))
    hexchr = "&#%s;"% hexchr[1:]
    return hexchr

def hex2uni(c):
    hexchr = "0%s"% c[2:-1]
    try: uchr = unichr(eval(hexchr))
    except: return u'Er!'
    return uchr

def str2hex(s, slen=0):
    us = safeunicode(s)

    if slen > 0 and len(us) > slen:
        us = us[:slen-3] + u'...'

    h=list()
    for c in us:
        h.append(uni2hex(c))

    hstr = "".join(h)
    if hstr.startswith('&#xa;'): 
        hstr = hstr[5:]
    return hstr.replace('&#xa;','\n')

def safe_utf8chinese(s, slen=0):
    us = force_unicode(s)
    if slen > 0 and len(us) > slen:
        us = us[:slen-3] + u'...'

    h=list()
    try: 
        h.append(us.encode('utf-8'))
    except:
        for c in us:
            if ischinese(c):
                h.append(uni2hex(c))
            else:
                h.append(c.encode('utf-8'))
    return "".join(h)

safeutf8 = safe_utf8chinese

def ischinese(s):
    try:
        scode = ord(s)
        if scode >= 0x4E00 and scode <= 0x9FBF: return True
    except:
        pass

    return False