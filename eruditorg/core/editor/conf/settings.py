# -*- coding: utf-8 -*-

from django.conf import settings


MAIN_PRODUCTION_TEAM_IDENTIFIER = getattr(
    settings, 'EDITOR_MAIN_PRODUCTION_TEAM_IDENTIFIER', 'main')


# This is the number of days after which the files of an issue submission that has been valided
# will be deleted.
ARCHIVE_DAY_OFFSET = 30
