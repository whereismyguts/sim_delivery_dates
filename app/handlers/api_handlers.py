# -*- encoding: utf-8 -*-

import datetime
import random
import sys
import time
import traceback

from app.models.models import BaseModel
# from app.texts import _text
# from app.exceptions import (
#     AppError, AuthError, GeoError,
#     ApiError, ApiDataError,
#     ServerError, ServerDataError,
# )
import json
from app_utils.tornado_utils.handlers import AbsHandler


class ApiHandler(AbsHandler):

    def __init__(self, *args, **kwargs):
        super(ApiHandler, self).__init__(*args, **kwargs)
        self.local_data_cache = {}

    req_id = None
    req_start = None
    token_data = None

    default_status_code = 200

    SET_ERROR_STATUS_CODE = False

    # def raise_api_error(self, **kwargs):
    #     raise ApiError(**kwargs)
    #
    # def raise_api_data_error(self, **kwargs):
    #     raise ApiDataError(**kwargs)
    #
    # def raise_server_error(self, **kwargs):
    #     raise ServerError(**kwargs)
    #
    # def raise_server_data_error(self, **kwargs):
    #     raise ServerDataError(**kwargs)

    def _print(self, *strings):
        try:
            sys.stderr.write(u'{}\n'.format(strings))
        except:
            pass

    _prev_time = 0

    @property
    def _current_time(self):
        self._prev_time = time.time()
        return self._prev_time

    @property
    def _et(self):
        return round(-1 * (self._prev_time - self._current_time), 3)

    def _start_request(self):
        try:
            self.db_session.execute("select 1")
        except:
            self.db_session.rollback()

        self._current_time
        return

        self.req_id = random.randint(0, 1000)
        self.req_start = datetime.datetime.utcnow()

        try:
            self.debug(
                u'REQUEST {}: {}'.format(self.req_id, self.request.uri),
                self.request.body
            )
        except:
            pass

    def _end_request(self, response_data):
        # print(response_data)
        return

    def send_response(self, response_data):
        if isinstance(response_data, (dict, list)):
            self.set_header('Content-type', 'application/json')
            self.write(json.dumps(response_data, indent=2))
            # try:
            #     print(json.dumps(response_data, indent=2))
            # except:
            #     pass
        elif response_data:
            self.write(response_data)

    NEED_SERVER_ERROR_ALERT = True

    def handle_request(self, handler, args, kwargs):
        status_code = self.default_status_code
        try:
            self._start_request()
            response_data = handler(*args, **kwargs)
        # except (AuthError, GeoError, ApiDataError) as err:
        #     response_data = err.response_data
        #     if self.SET_ERROR_STATUS_CODE:
        #         status_code = err.status_code
        #     self.debug(
        #         u'{} {}:\n{}\n{}\n{}'.format(
        #             err.__class__.__name__,
        #             self.__class__.__name__,
        #             self.token_data, self.data,
        #             err
        #         )
        #     )
        # except AppError as err:
        #     response_data = err.response_data
        #     if self.SET_ERROR_STATUS_CODE:
        #         status_code = err.status_code
        #     try:
        #         print(self.data)
        #     except:
        #         pass
        #     self.error(
        #         u'{} {}:\n{}\n{}'.format(
        #             err.__class__.__name__,
        #             self.__class__.__name__,
        #             self.token_data, self.data,
        #         ), error=err, trace=False
        #     )
        except Exception as err:
            response_data = {}
            print('REQUEST {} ERROR:'.format(self.request.uri))
            print('DATA: ', self.data)
            print('TRACE:')
            print(err, traceback.format_exc())
            if self.SET_ERROR_STATUS_CODE:
                status_code = 500

            response_data['result'] = 0
            response_data['error'] = 1
            response_data['reply'] = 'something_wrong'

            self.error(
                u'{} {}:\n{}\n{}'.format(
                    err.__class__.__name__,
                    self.__class__.__name__,
                    self.token_data, self.data,
                ), error=err
            )

            self.db_session.rollback()
            BaseModel.db_session.rollback()

        self.set_status(status_code)
        self.send_response(response_data)
        self._end_request(response_data)
        self.finish()

    def get(self, *args, **kwargs):
        self.handle_request(self._get, args, kwargs)

    def _get(self, *args, **kwargs):
        raise Exception('not valid method', uri=self.request.uri)

    def post(self, *args, **kwargs):
        self.handle_request(self._post, args, kwargs)

    def _post(self, *args, **kwargs):
        raise Exception('not valid method', uri=self.request.uri)