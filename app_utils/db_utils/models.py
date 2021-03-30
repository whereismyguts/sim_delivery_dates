# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import datetime
import lazy_object_proxy
import re

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy import (
    or_ as sql_or,
    and_ as sql_and
)

from app_utils.db_utils import get_current_dbsession


__all__ = (
    'BaseModel', 'ClassPropertyDescriptor',
    'jsonb_property',
)


class ClassPropertyDescriptor(object):

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def jsonb_property(
        storage_name, property_name,
        default=None, doc='', **kwargs
):
    doc = doc or 'Property: {}'.format(property_name)
    if 'default_value' in kwargs:
        default = kwargs['default_value']

    def get_property(self):
        storage = getattr(self, storage_name) or {}
        if property_name not in storage:
            default_value = (
                default()
                if callable(default) else default
            )
            if default_value is not None:
                set_property(self, default_value)
            return default_value
        return storage.get(property_name, None)

    def set_property(self, value):
        storage = (getattr(self, storage_name) or {}).copy()
        storage[property_name] = value
        setattr(self, storage_name, storage)

    def del_property(self):
        storage = (getattr(self, storage_name) or {}).copy()
        if property_name in storage:
            del storage[property_name]
            setattr(self, storage_name, storage)

    return property(
        get_property,
        set_property,
        del_property,
        doc=doc
    )


def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


def repeat_db_request(func, db_session, repeat=False):
    while 1:
        try:
            return func()
        except Exception as err:
            str_err = str(err)
            if (
                    (
                        'SSL SYSCALL error: EOF detected' in str_err or
                        'the database system is in recovery mode' in str_err or
                        'server closed the connection unexpectedly' in str_err or
                        'current transaction is aborted, commands ignored until end of transaction block' in str_err
                    ) and (
                        repeat or
                        getattr(db_session, 'db__repeat', None)
                    )
            ):
                print(str_err)
                db_session.rollback()
                continue
            raise


class DjangoQuery(Query):

    def __init__(
            self,
            session,
            model,
            entities=None,
            redis=None,
            base_filters=None
    ):
        if not (
                entities is None or
                isinstance(entities, (list, tuple))
        ):
            self.db__flat = True
        else:
            self.db__flat = False

        if entities is None:
            entities = model

        super(self.__class__, self).__init__(entities, session)
        self.model = model
        self.redis = redis
        self.base_filters = base_filters or {}

        self.entities = entities

    def _query(self, *entities):
        return self.__class__(
            self.session,
            self.model,
            entities=entities,
            redis=self.redis,
            base_filters=self.base_filters,
        )

    def get(self, *filters, **filters_by):
        db__flat = self.__get_db_flat(filters_by)
        db__repeat = filters_by.pop("db__repeat", None)

        query = self.__use_filters(*filters, **filters_by)
        result = repeat_db_request(
            lambda: query.first(),
            self.session, db__repeat
        )

        if result and db__flat:
            result = result[0]
        return result

    def last(self, *filters, **filters_by):
        order_by = self.__get_db_order_by(filters_by)
        db__flat = self.__get_db_flat(filters_by)
        db__repeat = filters_by.pop("db__repeat", None)

        query = self.__use_filters(*filters, **filters_by)

        if order_by is None:
            order_by = self.model.id.desc()

        query = query.order_by(None).order_by(order_by)
        result = repeat_db_request(
            lambda: query.first(),
            self.session, db__repeat
        )

        if result and db__flat:
            result = result[0]
        return result

    def all(self, *filters, **filters_by):
        db__flat = self.__get_db_flat(filters_by)
        db__repeat = filters_by.pop("db__repeat", None)

        query = self.__use_filters(*filters, **filters_by)

        results = repeat_db_request(
            lambda: super(query.__class__, query).all(),
            self.session, db__repeat
        )

        if db__flat:
            results = results and list(next(zip(*results)))

        return results

    def exists(self, *filters, **filters_by):
        return bool(
            self._query(self.model.id).get(*filters, **filters_by)
        )

    def __get_db_flat(self, filters_by):
        db__flat = self.db__flat
        if 'db__flat' in filters_by:
            db__flat = filters_by['db__flat']
            del filters_by['db__flat']
        return db__flat

    def __get_db_order_by(self, filters_by):
        db__order_by = None
        if 'db__order_by' in filters_by:
            db__order_by = filters_by['db__order_by']
            del filters_by['db__order_by']
            if not hasattr(db__order_by, '__iter__'):
                db__order_by = [db__order_by]
        return db__order_by

    def __get_db_limit(self, filters_by):
        db__limit = None
        if 'db__limit' in filters_by:
            db__limit = filters_by['db__limit']
            del filters_by['db__limit']
        return db__limit

    def __get_db_offset(self, filters_by):
        db__offset = filters_by.pop('db__offset', None)
        return db__offset

    def __use_filters(self, *filters, **filters_by):
        query = self
        filters = [f for f in filters if f is not None]
        if filters:
            if isinstance(filters[0], int):
                query = query.filter(
                    self.model.id == filters[0],
                    *filters[1:]
                )
            else:
                query = query.filter(*filters)

        filters_by = self.__update_filters(filters_by)
        db__order_by = self.__get_db_order_by(filters_by)
        db__limit = self.__get_db_limit(filters_by)
        db__offset = self.__get_db_offset(filters_by)

        if filters_by:
            query = query.filter_by(**filters_by)

        if db__order_by:
            query = query.order_by(*db__order_by)

        if db__offset:
            query = query.offset(db__offset)

        if db__limit:
            query = query.limit(db__limit)

        return query

    def use_filters(self, *filters, **filters_by):
        return self.__use_filters(*filters, **filters_by)

    def upd_query(self, handler, *args, **kwargs):
        query = handler(self, *args, **kwargs)
        return query

    def __update_filters(self, filters):
        updated_filters = self.base_filters.copy()
        updated_filters.update(filters or {})
        return updated_filters


class BaseModel:

    db_session = lazy_object_proxy.Proxy(get_current_dbsession)

    id = None
    BASE_MODEL_FILTERS = None

    @classproperty
    @classmethod
    def db_query(cls):
        return cls.db__query

    @classproperty
    @classmethod
    def db__query(cls):
        return cls.query()

    @classmethod
    def db__ids(cls, *filters, **filters_by):
        filters_by['db__flat'] = True
        db_session = filters_by.pop('db_session', None)
        return cls.query(
            db_session=db_session,
            entities=cls.id
        ).all(*filters, **filters_by)

    @classmethod
    def db__id(cls, *filters, **filters_by):
        filters_by['db__flat'] = True
        db_session = filters_by.pop('db_session', None)
        return cls.query(
            db_session=db_session,
            entities=cls.id
        ).get(*filters, **filters_by)

    WORD_EXP = re.compile(u'([\dA-Za-zА-ЯЁа-яё]+)', re.U)

    @classmethod
    def db__search_words(cls, search, limit=3):
        search = search.lower().strip()
        if ":" in search:
            words = search.split(':')
            words = list(filter(bool, words))
            if not words:
                return []
            elif len(words) == 1:
                return cls.db__search_words(words[-1], limit=limit)
            return words[:-1] + cls.db__search_words(words[-1], limit=limit)

        if search.startswith('"') and search.endswith('"'):
            if len(search) > 2:
                return [search]
            return []
        elif search.startswith('"'):
            if len(search) > 1:
                return [search]
            return []
        elif search.endswith('"'):
            if len(search) > 1:
                return [search]
            return []

        words = cls.WORD_EXP.findall(search.lower())
        words = list(filter(bool, words))[:limit]
        return words

    @classmethod
    def __sql_search_filters(cls, model_field, search_words):
        filters = []
        for word_obj in search_words:
            if isinstance(word_obj, list):
                filters.append(sql_or(*cls.__sql_search_filters(
                    model_field, word_obj
                )))
            elif word_obj.startswith('"') and word_obj.endswith('"'):
                filters.append(
                    model_field.ilike(word_obj[1:-1])
                )
            elif word_obj.startswith('"'):
                filters.append(
                    model_field.ilike(word_obj[1:] + '%')
                )
            elif word_obj.endswith('"'):
                filters.append(
                    model_field.ilike('%' + word_obj[:-1])
                )
            else:
                filters.append(model_field.op('~*')(word_obj))
        return filters

    @classmethod
    def db__search(cls, model_field, search):
        if not search:
            return None

        if isinstance(search, (list, tuple)):
            search_words = search
        else:
            search_words = BaseModel.db__search_words(search)

        if not search_words:
            return []

        return sql_and(*cls.__sql_search_filters(model_field, search_words))

    @classmethod
    def query(cls, db_session=None, redis=None, entities=None, base_filters=None):
        if base_filters is None:
            base_filters = cls.BASE_MODEL_FILTERS

        if db_session is None:
            db_session = cls.db_session

        if redis is None:
            redis = cls.redis

        query = DjangoQuery(
            db_session,
            cls,
            entities=entities,
            redis=redis,
            base_filters=base_filters
        )
        return query

    @property
    def _db_session(self):
        if self._sa_instance_state.session is None:
            return self.db_session
        return self._sa_instance_state.session

    is_added = False
    __is_modified = None

    @property
    def is_modified(self):
        if self.__is_modified is not None:
            return self.__is_modified
        return self._db_session.is_modified(self)

    @is_modified.setter
    def is_modified(self, value):
        self.__is_modified = value

    def save(self, db_session=None, commit=True, flush=True, **kwargs):
        if db_session is None:
            db_session = self._db_session

        if self.id is None:
            self.is_modified = True
            self.is_added = True
            db_session.add(self)
            # flush and db_session.flush()

        if commit:
            self.is_modified = self.is_modified
            db_session.commit()
        return self

    @classmethod
    def get_or_create(cls, db_session=None, commit=True, **kwargs):
        if db_session is None:
            db_session = cls.db_session

        return cls.query(
            db_session=db_session
        ).get(**kwargs) or cls(**kwargs).save(
            db_session=db_session, commit=commit
        )

    def create(self, db_session=None, **kwargs):
        if db_session is None:
            db_session = self.db_session
        if self.id is None:
            db_session.add(self)
            self.is_modified = True
            self.is_added = True
        db_session.flush()
        return self

    def delete(self, db_session=None, commit=True, **kwargs):
        if db_session is None:
            db_session = self._db_session

        if hasattr(self, 'deleted'):
            if getattr(self, 'deleted') is None:
                setattr(self, 'deleted', datetime.datetime.utcnow())
                self.save(db_session=db_session, commit=commit, **kwargs)
                return 1
            return 0
        else:
            db_session.query(self.__class__).filter_by(
                id=self.id
            ).delete()
            commit and db_session.commit()
            return 1

    @classmethod
    def commit(cls):
        cls.db_session.commit()

    @classmethod
    def db__commit(cls):
        cls.db_session.commit()

    _TABLE_FIELDS = None

    @classmethod
    def _get_table_fields(cls):
        if not cls._TABLE_FIELDS:
            fields = []
            for attr in dir(cls):
                if isinstance(getattr(cls, attr), InstrumentedAttribute):
                    fields.append(attr)
            cls._TABLE_FIELDS = fields
        return cls._TABLE_FIELDS

    def copy(self, **new_values):
        new_item = self.__class__()
        for field in self._get_table_fields():
            if field == 'id':
                continue

            if field in new_values:
                value = new_values[field]
            else:
                value = getattr(self, field)

            setattr(new_item, field, value)
        return new_item

