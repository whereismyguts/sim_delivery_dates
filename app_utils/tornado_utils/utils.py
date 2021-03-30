    # -*- coding: utf-8 -*-
from tornado import httpserver, ioloop, options, web
from app_utils.db_utils import create_dbsession, get_dbsession


def create_server(
        port,
        app_handlers,
        app_settings=None,
        db_settings=None,
        debug=False,
        process=None,
        ssl_options=None,
        BaseModel=None,
):
    app_settings = app_settings or {}
    db_settings = db_settings or {}

    app_settings.update(dict(
        debug=debug,
    ))

    options.parse_command_line()

    app = web.Application(app_handlers, **app_settings)

    # app.db_session = create_dbsession(**db_settings)
    # app.db_session.rollback()
    if BaseModel is not None:
        app.db_session = BaseModel.db_session
    else:
        app.db_session = get_dbsession(**db_settings)
    app.port = port

    http_server = httpserver.HTTPServer(
        app, xheaders=True,
        ssl_options=ssl_options,
        no_keep_alive=True,
    )
    # if process is not None:
    #     http_server.bind(port)
    #     http_server.start(process)
    # else:
    #     http_server.listen(port)
    http_server.listen(port)

    ioloop_instance = ioloop.IOLoop.instance()
    ioloop_instance.start()
