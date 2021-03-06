# -*- coding: utf-8 -*-

import os

from base.settings.base import *  # noqa


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return 'notmigrations'


TEST_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

MEDIA_ROOT = os.path.join(TEST_ROOT, '_testdata/media/')

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.remove('raven.contrib.django.raven_compat')

MIGRATION_MODULES = DisableMigrations()

USE_DEBUG_EMAIL = False

METRICS_ACTIVATED = True
TRACKING_INFLUXDB_HOST = 'localhost'
TRACKING_INFLUXDB_PORT = 8086
TRACKING_INFLUXDB_DBNAME = 'erudit-metrics'
TRACKING_INFLUXDB_USER = 'root'
TRACKING_INFLUXDB_PASSWORD = 'root'

FEDORA_ROOT = 'http://example.com'
SOLR_ROOT = 'http://example.com'
