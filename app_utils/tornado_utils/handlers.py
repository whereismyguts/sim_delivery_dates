# -*- coding: utf-8 -*-

import copy
import threading
import traceback

from tornado import web, ioloop
from tornado.escape import utf8

from app_utils.db_utils import create_dbsession
import json
from app_utils.tornado_utils.wrappers import (
    memorizing, app_level_memorizing,
)
from settings import (SERVER_URL, DEBUG)


__all__ = (
    'AbsHandler',
    'BaseView', 'NotFoundHandler', 'BaseHtmlHandler',
)


class AbsHandler(web.RequestHandler):

    @property
    def db_session(self):
        return self.application.db_session

    # ---

    @property
    @memorizing
    def data(self):
        data = {}
        for field, values in self.request.arguments.items():
            if isinstance(values, (list, tuple)):
                values = list(map(lambda val: val.decode('utf-8'), values))
                if len(values) == 1:
                    values = values[0]
            else:
                values = values.decode('utf-8')
            data[field] = values

        data.update(self.get_json())
        return data

    @memorizing
    def get_json(self):
        try:
            return self.request.body and json.loads(
                self.request.body.decode('utf8')
            ) or {}
        except Exception as err:
            return {}

    # ---

    @classmethod
    def run_in_thread(cls, worker):
        def target():
            try:
                db_session = create_dbsession()
                worker(db_session)
            finally:
                try:
                    db_session.commit()
                except:
                    pass
                try:
                    db_session.close()
                except:
                    pass

        threading.Thread(target=target).start()

    def worker(self, db_session):
        raise NotImplementedError()

    def start_worker(self, callback=None):
        def worker(db_session):
            self.worker(db_session)
            if callback is not None:
                self.add_callback(callback)
        self.run_in_thread(worker)

    @property
    def current_ioloop(self):
        return ioloop.IOLoop.current()

    def add_callback(self, callback):
        self.current_ioloop.add_callback(callback)

    def info(self, *texts):
        text = ''
        try:
            for _text in texts:
                text += _text + '\n'
        except Exception as err:
            # self.error('send info', error=err)
            pass

    def debug(self, *texts):
        text = ''
        try:
            for _text in texts:
                text += _text + '\n'
        except Exception as err:
            # self.error('send debug', error=e)
            pass

    def error(self, texts, error=None, traceback_text='', trace=True):
        try:
            traceback_text = (
                traceback_text or
                trace and traceback.format_exc()
            ) or ''
        except Exception as err:
            print(err)
            traceback_text = u'Can\'t get traceback_text'

        if isinstance(texts, (str, bytes)):
            texts = [texts, ]

        text = ''
        try:
            try:
                for _text in texts:
                    text += _text + u'\n'
            except:
                pass

            try:
                error_text = (
                    'error' if error is None else str(error)
                )
            except Exception as err:
                print(err)
                error_text = u'Can\'t get error_text'

            text += u'\n{}: {}'.format(error_text, traceback_text)
        except Exception as err:
            self.error('send error', error=err)

    def redirect(self, url, permanent=False, status=None):
        """Sends a redirect to the given (optionally relative) URL.

        If the ``status`` argument is specified, that value is used as the
        HTTP status code; otherwise either 301 (permanent) or 302
        (temporary) is chosen based on the ``permanent`` argument.
        The default is 302 (temporary).
        """
        if self._headers_written:
            raise Exception("Cannot redirect after headers have been written")
        if status is None:
            status = 301 if permanent else 302
        else:
            assert isinstance(status, int) and 300 <= status <= 399
        self.set_status(status)
        self.set_header("Location", utf8(url))
        self.finish()


class BaseHtmlHandler(AbsHandler):

    ModelForm = None
    template = ''

    default_context = None
    default_ajax_context = None

    def __init__(self, application, request, **kwargs):
        super(BaseHtmlHandler, self).__init__(application, request, **kwargs)

        self.context = copy.deepcopy(self.default_context or {})
        self.context.update(dict(
            DEBUG=DEBUG,

            site_url=SERVER_URL,
            current_url=SERVER_URL + self.request.uri,

            form=(
                self.ModelForm()
                if self.ModelForm is not None else None
            ),
            error=None,
        ))

        self.ajax_context = copy.deepcopy(self.default_ajax_context or {})
        self.ajax_context.update(dict(
            error=None,
        ))

    @property
    @memorizing
    def form(self):
        if self.ModelForm is None:
            return None

        form = self.ModelForm(data=self.data)
        form.validate()

        self.context['form'] = form

        if form.errors:
            self.ajax_context['error'] = form.errors

        return form

    @property
    def form_is_valid(self):
        return self.form is None or not bool(self.form.errors)


    def render(self, template=None, **context):
        if self.is_ajax_request:
            return self.render_ajax_response(**context)
        template = template or self.template
        self.context.update(context)
        super(BaseHtmlHandler, self).render(template, **self.context)

    def render_with_status_404(self, template=None, **context):
        self.set_status(404)
        return self.render(template=template, **context)

    def redirect(self, path):
        if self.is_ajax_request:
            context = {
                'location': '{server_url}{path}'.format(
                    server_url=self.context['site_url'],
                    path=path
                )
            }
            return self.render_ajax_response(**context)
        return super(BaseHtmlHandler, self).redirect(path)

    @property
    def is_ajax_request(self):
        return self.request.headers.get('X-Requested-With') == "XMLHttpRequest"

    def render_ajax_response(self, **context):
        self.ajax_context.update(context)
        self.write(json.dumps(self.ajax_context))

    def write_error(self, status_code, **kwargs):
        """Override to implement custom error pages.

        ``write_error`` may call `write`, `render`, `set_header`, etc
        to produce output as usual.

        If this error was caused by an uncaught exception (including
        HTTPError), an ``exc_info`` triple will be available as
        ``kwargs["exc_info"]``.  Note that this exception may not be
        the "current" exception for purposes of methods like
        ``sys.exc_info()`` or ``traceback.format_exc``.

        For historical reasons, if a method ``get_error_html`` exists,
        it will be used instead of the default ``write_error`` implementation.
        ``get_error_html`` returned a string instead of producing output
        normally, and had different semantics for exception handling.
        Users of ``get_error_html`` are encouraged to convert their code
        to override ``write_error`` instead.
        """
        # print 'status_code', status_code
        if status_code == 404:
            return self.render(template='404.html')

        if self.settings.get("debug") and "exc_info" in kwargs:
            msg = ''
            for line in traceback.format_exception(*kwargs["exc_info"]):
                msg += line + '<br>'
        else:
            if status_code == 500:
                msg = u'Что-то пошло не так.<br>Скоро всё исправим!'
            else:
                msg = self._reason

        self.render(template='error.html', **dict(
            code=status_code,
            title_msg=self._reason,
            message=msg,
        ))

    def on_finish(self):
        if self.get_status() == 500 and self.db_session is not None:
            self.db_session.rollback()


class BaseView(BaseHtmlHandler):

    def get(self):
        return self.render()


class NotFoundHandler(BaseHtmlHandler):

    def get(self):
        raise web.HTTPError(404)
