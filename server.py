# -*- encoding: utf-8 -*-
from __future__ import print_function

from app.handlers import DeliveryDatetimesHandler, UploadDeliveryDatetimesHandler
from app.models.models import BaseModel
from app_utils.tornado_utils import create_server
from settings import (
    APP_SETTINGS,
    DEBUG, PORT, DB_PATH,
    PROCESSES_NUM,
)

EXTERNAL_HANDLERS = [
    (r'/api/v1/delivery_date_times', DeliveryDatetimesHandler),
    (r'/api/v1/upload_delivery_date_times', UploadDeliveryDatetimesHandler),
]


if __name__ == "__main__":
    print('server started (port: {}; process: {})'.format(
        PORT, PROCESSES_NUM
    ))
    HANDLERS = EXTERNAL_HANDLERS

    create_server(
        PORT, HANDLERS, APP_SETTINGS,
        db_settings=dict(db_path=DB_PATH),
        debug=DEBUG, process=PROCESSES_NUM,
        BaseModel=BaseModel,
    )
