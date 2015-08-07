#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pweb import http
#from pweb.db import sql as dbn
from pweb.utils.datastructs import AttrDict

class Index:
    def GET(self):
        #ret = dbn.mysql.select("select * from user")
        #if len(ret)==2 and ret[0]==True:
        #    print ret[1].list()
        return http.TemplateResponse("main.html")

    def POST(self):
        return self.GET()

class MsgList:
    def GET(self):
        req = http.input(type=0, page=1, pagesize=10)
        msglist = []
        rndcode = http.session.get('rndcode')
        """
        ret = dbn.select("select id, subject, author, indate from tbl_msg")
        if len(ret)==2 and ret[0]==True:
            msglist = len(ret[1].list())
        """
        return http.TemplateResponse("msglist.html", msglist=msglist, rndcode=rndcode)

class MsgDetail:
    def GET(self, id=0):
        try: 
            id = int(id)
        except:
            raise http.seeother('./msglist')

        args = AttrDict(subject="", content="", author="", indate="")

        """
        ret = dbn.selectone("select subject, content, author, indate from tbl_msg where id=?", id)
        if len(ret)==2 and ret[0]==True and len(ret[1])>0:
            args.subject = ret[1].subject
            args.content = ret[1].content
            args.author = ret[1].author
            args.indate = ret[1].indate.strftime("%Y-%m-%d %H:%M:%S")
        """
        
        return http.TemplateResponse("msgdetail.html", args=args)