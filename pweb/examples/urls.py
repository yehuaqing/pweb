#!/usr/bin/env python
# -*- coding: utf-8 -*-

urlpatterns = {
                '/imgcode.png'  : 'index.rndcode.ImgCode',

                '/'             : 'index.actions.Index',
                '/msglist'      : 'index.actions.MsgList',
                '/msg_(.*)'     : 'index.actions.MsgDetail',
              }