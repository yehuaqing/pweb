#!/usr/bin/env python
# -*- coding: utf-8 -*-

DEBUG               = False
DEBUG_SQL           = False

#部署路径 如http://127.0.0.1/test, 则填写"/test"
DEPLOY_PATH         = "/"

DEFAULT_CHARSET     = "utf-8"
DEF_CONTENT_TYPES   = "text/html; charset=utf-8"

STATIC_INDEX        = False
STATIC_PATH         = ("/static/","/meida/","/favicon.ico","/robots.txt")
STATIC_DIRS         = ()

TEMPLATE_PATH       = ('templates',)
TEMPLATE_DIRS       = ()

DATABASE            = {"default":{},}

SESSION_COOKIE_NAME             = 'pweb_session_id'
SESSION_COOKIE_DOMAIN           = None
SESSION_COOKIE_PATH             = None
SESSION_COOKIE_TIMEOUT          = 86400         # 24 * 60 * 60 -- 24 hours in seconds
SESSION_COOKIE_IGNORE_EXPIRY    = True,
SESSION_COOKIE_IGNORE_CHANGE_IP = True,
SESSION_COOKIE_SECRET_KEY       = '9a515b80e7ca11e3a626',
SESSION_COOKIE_EXPIRED_MESSAGE  = 'Session expired',

SESSION_STORE                   = 'DiskStore'       # The module to store session data, can use DiskStore, DBStore, ShelfStore
SESSION_STORE_CONFIG            = {'path':'/temp'}  # DiskStore or ShelfStore path for session
"""
SESSION_STORE                   = 'DBStore'
SESSION_STORE_CONFIG            = { "ENGINE" : "mysql", "NAME" : "session", "USER" : "root", "PASSWORD"  : "123456", 
                                    "HOST" : "127.0.0.1", "PORT" : None, "TABLE_NAME": "session"}
"""
SESSION_COOKIE_HTTPONLY         = True
SESSION_COOKIE_SECURE           = False