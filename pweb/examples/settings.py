#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import path
HERE                = path.dirname(path.abspath(__file__))

DEBUG               = True
DEBUG_SQL           = True

#部署路径 如http://127.0.0.1/test, 则填写"/test"
DEPLOY_PATH         = "/"

DEFAULT_CHARSET     = "utf-8"
DEF_CONTENT_TYPES   = "text/html; charset=utf-8"

STATIC_INDEX        = True
STATIC_DIRS         = ("/media/",)

#数据库配置-可以同时配置多个
DATABASE            = {
                        'default': {
                                    "ENGINE"    : "mssql",          # mssql, mysql, oracle
                                    "NAME"      : "test",           # database name
                                    "USER"      : "sa",             # uid
                                    "PASSWORD"  : "123",            # password
                                    "HOST"      : "127.0.0.1",      # database host
                                    "PORT"      : 1433,             # port
                                   },
                        'mysql': {
                                    "ENGINE"    : "mysql",          # mssql, mysql, oracle
                                    "NAME"      : "mysql",          # database name
                                    "USER"      : "root",           # uid
                                    "PASSWORD"  : "123",            # password
                                    "HOST"      : "127.0.0.1",      # database host
                                    "PORT"      : 3306,             # port
                                   }
                       }

TEMPLATE_DIRS       = ("templates",)

SESSION_COOKIE_NAME             = 'pweb_session_id'
SESSION_COOKIE_DOMAIN           = None
SESSION_COOKIE_PATH             = None
SESSION_COOKIE_TIMEOUT          = 86400         # 24 * 60 * 60 -- 24 hours in seconds
SESSION_COOKIE_IGNORE_EXPIRY    = True,
SESSION_COOKIE_IGNORE_CHANGE_IP = True,
SESSION_COOKIE_SECRET_KEY       = '466e740f065811e49a310021cccc1d0c',
SESSION_COOKIE_EXPIRED_MESSAGE  = 'Session expired',
SESSION_STORE                   = 'DiskStore'   # The module to store session data, can use DiskStore, DBStore, ShelfStore
SESSION_STORE_CONFIG            = {'path':path.join(HERE, "sessiondir")}  # DiskStore or ShelfStore path for session
SESSION_COOKIE_HTTPONLY         = True
SESSION_COOKIE_SECURE           = False
