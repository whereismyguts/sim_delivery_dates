# -*- coding: utf-8 -*-
from __future__ import print_function

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool


__all__ = (
    'get_dbengine',
    'get_dbsession',
    'create_dbsession',
)


ENGINES = {}
DBSESSIONS = {}


def get_dbengine(db_path, **kwargs):
    if db_path not in ENGINES:
        ENGINES[db_path] = create_engine(
            db_path,
            poolclass=NullPool,
            # pool_size=16,
            # max_overflow=100,
            # pool_pre_ping=True,
            **kwargs
        )
    return ENGINES[db_path]


def create_dbsession(db_path, **kwargs):
    engine = get_dbengine(db_path=db_path, **kwargs)
    SessionClass = sessionmaker(bind=engine)
    SessionClass = scoped_session(sessionmaker(bind=engine))
    session = SessionClass()
    session.SessionClass = SessionClass
    session.engine = engine
    # session.DBSESSIONS = DBSESSIONS
    if db_path not in DBSESSIONS:
        DBSESSIONS[db_path] = session
    return session


def get_dbsession(db_path, **kwargs):
    if db_path not in DBSESSIONS:
        DBSESSIONS[db_path] = create_dbsession(db_path, **kwargs)
    return DBSESSIONS[db_path]
