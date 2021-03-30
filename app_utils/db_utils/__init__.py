# -*- coding: utf8 -*-
from __future__ import print_function

from app_utils.db_utils.db_utils import (
    get_dbengine as _get_dbengine,
    create_dbsession as _create_dbsession,
    get_dbsession as _get_dbsession
)

try:
    import settings
    settings.DB_PATH
except Exception as e:
    print (e)
    print('''add settings.py with:

DB_PATH = "postgresql://{{ user }}:{{ password }}@127.0.0.1:{{ port }}/{{ db_name }}"
''')
    import sys
    sys.exit()


__all__ = (
    'get_current_dbengine',
    'get_current_dbsession',
    'create_new_dbsession',
    'get_dbengine',
    'get_dbsession',
    'create_dbsession',
)


def get_dbengine(db_path=None):
    return _get_dbengine(db_path=db_path or settings.DB_PATH)


def get_dbsession(db_path=None):
    return _get_dbsession(db_path=db_path or settings.DB_PATH)


def create_dbsession(db_path=None):
    return _create_dbsession(db_path=db_path or settings.DB_PATH)


get_current_dbengine = get_dbengine
get_current_dbsession = get_dbsession
create_new_dbsession = create_dbsession
