#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import global_settings
from pweb.utils import importlib

empty = object()

class LazyObject(object):
    def __init__(self):
        self._settings = empty

    def __setattr__(self, name, value):
        if name == "_settings":
            self.__dict__["_settings"] = value
        else:
            if self._settings == empty:
                self._setup()
            setattr(self._settings, name, value)

    def __getattr__(self, name):
        if self._settings is empty:
            self._setup()
        #if hasattr(self._settings, name):
        return getattr(self._settings, name)
        #return None

    def __delattr__(self, name):
        if name == "_settings":
            raise TypeError("can't delete _settings.")
        if self._settings is empty:
            self._setup()
        delattr(self._settings, name)

    def _setup(self):
        raise NotImplementedError

    def __dir__(self):
        if self._settings is empty:
            self._setup()
        return dir(self._settings)

    __members__ = property(lambda self: self.__dir__())


class LazySettings(LazyObject):
    def _setup(self):
        self._settings = GlobalSettingHolder(global_settings)

    def configure(self, fvars):
        self.APP_PATH = self.HERE = os.path.dirname(os.path.abspath(fvars.get("__file__","")))
        self.APP_ROOT, self.APP_NAME = os.path.split(self.APP_PATH)

        if self.APP_ROOT not in sys.path:
            sys.path.append(self.APP_ROOT)

        init_file = os.path.join(self.APP_PATH, "__init__.py")
        if not os.path.isfile(init_file):
            try: 
                os.mknod(init_file)         #for linux, unix
            except:
                f = open(init_file, "w")    #for windows
                f.close()

        self._settings = Settings("settings", self)


class BaseSettings(object):
    def __init__(self):
        self.HERE = "/"
        self.APP_PATH = "/"
        self.APP_ROOT = "/"
        self.APP_NAME = None

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)


class Settings(BaseSettings):
    def __init__(self, settings_module, base_settings=None):
        for setting in dir(base_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(base_settings, setting))

        if settings_module is None:
            return

        try:
            settings = importlib.import_module(settings_module, self.APP_NAME)
        except ImportError, e:
            raise ImportError("Could not import settings: %s" % e)

        for setting in dir(settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(settings, setting))

class GlobalSettingHolder(BaseSettings):
    def __init__(self, default_settings):
        self.default_settings = default_settings

    def __getattr__(self, name):
        return getattr(self.default_settings, name)

    def __dir__(self):
        return self.__dict__.keys() + dir(self.default_settings)

    # For Python < 2.6:
    __members__ = property(lambda self: self.__dir__())

settings = LazySettings()