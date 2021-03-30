# -*- encoding: utf-8 -*-

import datetime

import sqlalchemy


import json
from app_utils.db_utils.models import BaseModel as _BaseModel


__all__ = ('BaseModel',)


class BaseModel(_BaseModel):

    @staticmethod
    def dt_to_json(dt):
        return dt and dt.strftime('%Y-%m-%dT%H:%M:%S.%f')

    MIN_UNIX_DT = datetime.datetime(1970, 1, 1, tzinfo=None)

    @classmethod
    def utc_datetime_to_timestamp(cls, utc_dt):
        return int((utc_dt - cls.MIN_UNIX_DT).total_seconds())

    @staticmethod
    def utc_timestamp_to_datetime(utc_timestamp):
        return datetime.datetime.utcfromtimestamp(utc_timestamp)

    @property
    def created_timestamp(self):
        return self.utc_datetime_to_timestamp(self.created)

    def get_stored_attributes(self):
        result = {}
        for n, a in self.__class__.__dict__.items():
            if type(a) == sqlalchemy.orm.attributes.InstrumentedAttribute:
                # print(a)
                if n == '_sdata':
                    n = 'sdata'
                val = getattr(self, n)

                if type(val) is datetime.datetime:
                    val = self.dt_to_json(val)
                result[n] = val
        return result

