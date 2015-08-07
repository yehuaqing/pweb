#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pweb import http
from pweb.utils import imgcode

class ImgCode:
    def GET(self):
        c = imgcode.picChecker( foregroundColor=(0,0,255), 
                                outputType="png", 
                                length=5, 
                                size = (110, 27) )
        code, imgdata = c.out()
        http.session['rndcode']=code
        return ("image/png", imgdata)