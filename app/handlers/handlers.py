import datetime
import os
from collections import OrderedDict
from functools import wraps

from app.exceptions import ApiError
from app.handlers.api_handlers import ApiHandler
from app.models.models import RegionDeliverySchedule
from app_utils.xls_utils import save_delivery_slots_from_file, generate_delivery_slots_file
from settings import SERVER_AUTH_TOKENS


def validate_token_access(need_write=False):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            auth_header = self.request.headers.get(
                'ServerAuthorization', ''
            ).strip()
            # print(auth_header, method)
            # print(SERVER_AUTH_TOKENS)
            if auth_header in SERVER_AUTH_TOKENS:
                granted_mode = SERVER_AUTH_TOKENS[auth_header]
                if granted_mode != 'write' and need_write:
                    return dict(
                        reply='permission denied',
                        error=1,
                    )
            else:
                return dict(
                    reply='bad_token',
                    error=1,
                )
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class UploadDeliveryDatetimesXlsHandler(ApiHandler):

    @validate_token_access(need_write=True)
    def _post(self, *args, **kwargs):

        utcnow = datetime.datetime.utcnow()
        _file, data = list(self.request.files.items())[0]

        if _file not in ['xls', 'xlsx']:
            return dict(
                error=1,
                result=0,
                reply='need xls or xlsx'
            )

        file_name = 'uploaded_delivery_dates_{}.{}'.format(utcnow.strftime('%Y-%m-%dT%H:%M:%S'), _file)
        file_body = self.request.files[_file][0]['body']
        file_path = os.path.join('data/files/', file_name)

        with open(file_path, 'wb') as f:
            f.write(file_body)

        response = save_delivery_slots_from_file(file_path)
        return response


class DeliveryDatetimesXlsHandler(ApiHandler):

    @validate_token_access()
    def _post(self, *args, **kwargs):
        filename = generate_delivery_slots_file()
        with open(filename, 'rb') as f:
            out_template_data = f.read()
            self.write(out_template_data)


class DeliveryDatetimesHandler(ApiHandler):

    @validate_token_access()
    def _post(self, *args, **kwargs):
        region_id = self.data.get('region_id')  # '41000000000'
        local_time = self.data.get('local_time')  # '2021.02.14T16:10:00'
        subject = self.data.get('subject')

        okato_name_data = RegionDeliverySchedule.query(entities=(
            RegionDeliverySchedule.region_id,
            RegionDeliverySchedule.subject_name,
        )).all(
            RegionDeliverySchedule.deleted == None,
        )
        delivery_regions = [{'id': u'{}:{}'.format(okato, name), 'name': name, } for okato, name in okato_name_data]
        delivery_regions.sort(key=lambda r: (
            r['name'] not in ['Москва', 'Санкт-Петербург'], r['name'][0].isdigit(), r['name']
        ))

        if not (region_id and subject):
            subject_prices = RegionDeliverySchedule.query(entities=(
                RegionDeliverySchedule.region_id,
                RegionDeliverySchedule.default_delivery_price,
            )).all(
                RegionDeliverySchedule.deleted == None,
            )

            return {
                "delivery_dates": {},
                "delivery_times": {},

                "result": 1,
                "error": 0,

                "delivery_info_text":  {s[0]: u"Автоматически подключится выбранный тариф" for s in subject_prices},
                "delivery_prices": dict(subject_prices),
                "default_region": "46000000000",
                "delivery_regions": delivery_regions,
            }

        schedule = RegionDeliverySchedule.query().get(
            RegionDeliverySchedule.region_id == region_id,
            RegionDeliverySchedule.subject_name == subject,
            RegionDeliverySchedule.deleted == None,
        )
        if not schedule:
            return dict(
                error=1,
                result=0,
                reply='Не найдено расписания с указанными данными: ОКАТО {}, город {}'.format(region_id, subject)
            )

        delivery_times = OrderedDict()
        today = datetime.datetime.strptime(local_time, '%Y.%m.%dT%H:%M:%S')
        for i in range(1, 30):
            day = today + datetime.timedelta(days=i)
            slots = schedule.get_timeslots(day)
            if slots:
                delivery_times[day.strftime('%d.%m.%Y')] = slots
            if len(delivery_times) > 5:
                break
        delivery_times = {k: delivery_times[k] for k in sorted(
            delivery_times.keys(),
            key=lambda d: datetime.datetime.strptime(d, '%d.%m.%Y')
        )}
        return {
            "delivery_times": delivery_times,
            "delivery_regions": delivery_regions,
            'price': schedule.default_delivery_price,
            "result": 1,
            "error": 0,
        }




