#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from pweb.utils import listget
from pweb.utils.net import validaddr, validip
import wsgiserver

def runfcgi(func, addr=('localhost', 8000)):
    """Runs a WSGI function as a FastCGI server."""
    import flup.server.fcgi as flups
    return flups.WSGIServer(func, multiplexed=True, bindAddress=addr, debug=False).run()

def runscgi(func, addr=('localhost', 4000)):
    """Runs a WSGI function as an SCGI server."""
    import flup.server.scgi as flups
    return flups.WSGIServer(func, bindAddress=addr, debug=False).run()

def runwsgi(func):
    if os.environ.has_key('SERVER_SOFTWARE'): # cgi
        os.environ['FCGI_FORCE_CGI'] = 'Y'

    if (os.environ.has_key('PHP_FCGI_CHILDREN') #lighttpd fastcgi
      or os.environ.has_key('SERVER_SOFTWARE')):
        return runfcgi(func, None)

    if 'fcgi' in sys.argv or 'fastcgi' in sys.argv:
        args = sys.argv[1:]

        if 'fastcgi' in args:
            args.remove('fastcgi')
        elif 'fcgi' in args: 
            args.remove('fcgi')

        if args:
            return runfcgi(func, validaddr(args[0]))
        else:
            return runfcgi(func, None)

    if 'scgi' in sys.argv:
        args = sys.argv[1:]
        args.remove('scgi')
        if args:
            return runscgi(func, validaddr(args[0]))
        else:
            return runscgi(func)

    return wsgiserver.runsimple(func, validip(listget(sys.argv, 1, '')))