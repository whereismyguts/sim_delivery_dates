# -*- encoding: utf-8 -*-

import json


__all__ = (
    'AppError',
    'AuthError', 'GeoError',
    'ApiError', 'ApiDataError',
    'ServerError', 'ServerDataError',
)


class AppError(Exception):
    ERROR = 'server_error'
    status_code = 200

    def __init__(self, error=None, status_code=None, **response_data):
        self.alert_text = response_data.get('alert_text')
        self.status_code = status_code or self.status_code

        self.response_data = response_data
        self.response_data['error'] = error or self.ERROR

        super(AppError, self).__init__(
            self.response_data['error']
        )

    def __str__(self):
        return json.dumps(self.response_data, ensure_ascii=False, indent=2)


class AuthError(AppError):
    ERROR = 'auth_error'
    status_code = 200


class AuthRefreshError(AuthError):
    ERROR = 'auth_refresh'
    status_code = 200


class GeoError(AppError):
    ERROR = 'geo_access_denied'
    status_code = 200


class ApiError(AppError):
    ERROR = 'api_error'
    status_code = 400


class ApiDataError(ApiError):
    ERROR = 'not_valid_input'
    status_code = 200


class ServerError(AppError):
    ERROR = 'server_error'
    status_code = 500


class ServerDataError(ServerError):
    ERROR = 'server_data_error'
    status_code = 404
