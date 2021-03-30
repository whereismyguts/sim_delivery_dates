# -*- coding: utf-8 -*-
from __future__ import print_function

import copy

from functools import wraps


def login_required():
    redirect = '/login/'

    def actual(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.current_user:
                return self.redirect(redirect)
            return func(self, *args, **kwargs)
        return wrapper
    return actual


def ajax_required(redirect='/'):
    def actual(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.is_ajax_request:
                return self.redirect(redirect)
            return func(self, *args, **kwargs)
        return wrapper
    return actual


def need_confirmed_email(redirect='/'):
    def actual(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if (
                    not self.current_user or
                    not self.current_user.email_is_confirmed
            ):
                return self.redirect(redirect)
            return func(self, *args, **kwargs)
        return wrapper
    return actual


def public_method(redirect='/logout/'):
    def actual(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.current_user:
                return self.redirect(redirect)
            return func(self, *args, **kwargs)
        return wrapper
    return actual


def private_method(redirect='/'):
    def actual(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.current_user:
                return self.redirect(redirect)
            return func(self, *args, **kwargs)
        return wrapper
    return actual


def method_for(redirect='/', user_types=None):
    user_types = user_types or []

    def actual(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.current_user or\
                    self.current_user.user_type not in user_types:
                return self.redirect(redirect)
            return func(self, *args, **kwargs)
        return wrapper
    return actual


def admin_method(redirect='/'):
    def actual(func):
        @wraps(func)
        def wrapper(self):
            if not self.current_user or not self.current_user.is_admin:
                return self.redirect(redirect)
            return func(self)
        return wrapper
    return actual


class DecoratorChainingMixin(object):
    """добавление любых декораторов к prepare
    class MyHandler(DecoratorChainingMixin, UpdateItem):
        decorators = [
            login_required, need_confirmed_email,
            admin_method(redirect='/')
        ]
    """
    def prepare(self):
        decorators = getattr(self, 'decorators', [])
        base = super(DecoratorChainingMixin, self).prepare

        for decorator in decorators:
            base = decorator(base)
            print('base', base)

        return base()


# --- memo ---


# --levels --
APP = 1
CONTROLLER = 0
# --


def memo(func, level=CONTROLLER):
    name = '___' + func.__name__

    @wraps(func)
    def decorator(self, *args, **kwargs):
        need_reload = kwargs.get('reload')
        save_to = self.application if level == APP else self
        if need_reload or not hasattr(save_to, name):
            setattr(save_to, name, func(self, *args, **kwargs))
        return getattr(save_to, name)
    return decorator


def memorizing(func):
    return memo(func, level=CONTROLLER)


def app_level_memorizing(func):
    return memo(func, level=APP)


def data_level_memorizing(func):
    memo_name = '__memo_' + func.__name__

    @wraps(func)
    def decorator(self, *args, **kwargs):
        need_reload = kwargs.get('reload')
        if need_reload or not (self.data or {}).get(memo_name):
            self.data = copy.copy(self.data or {})
            self.data[memo_name] = func(self, *args, **kwargs)
        return self.data[memo_name]
    return decorator

# ---
