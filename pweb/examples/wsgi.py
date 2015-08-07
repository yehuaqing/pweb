#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pweb
app = pweb.application(globals())

application = app.wsgifunc()

#如果使用spawn-fcgi方式运行，必须将以下一行代码取消注释
#pweb.wsgi.runwsgi = lambda func, addr=None: pweb.wsgi.runfcgi(func, addr)

if __name__ == "__main__":
    app.run()