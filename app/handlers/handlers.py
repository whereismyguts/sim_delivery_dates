import datetime
import os
from collections import OrderedDict

from app.handlers.api_handlers import ApiHandler
from app.models.models import RegionDeliverySchedule
from app_utils.xls_utils import load_delivery_slots, export_delivery_slots


class UploadDeliveryDatetimesXlsHandler(ApiHandler):

    def _get(self, *args, **kwargs):
        with open(self.XLS_TEMPLATE_PATH, 'rb') as fd:
            xls_template_data = fd.read()

        self.set_header("Content-Type", "application/octet-stream")
        return xls_template_data

    def _post(self, *args, **kwargs):
        utcnow = datetime.datetime.utcnow()

        file_name = 'delivery_dates_{}.xlsx'.format(utcnow.strftime('%Y-%m-%dT%H:%M:%S'))
        if 'xls' not in self.request.files:
            return dict(
                error=1,
                result=0,
                reply='need xls'
            )

        file_body = self.request.files['xls'][0]['body']
        file_path = os.path.join('data/files/', file_name)

        with open(file_path, 'wb') as f:
            f.write(file_body)

        load_delivery_slots(file_path)

        response = dict(
        )
        return response


class DeliveryDatetimesXlsHandler(ApiHandler):

    def _post(self, *args, **kwargs):
        filename = export_delivery_slots()
        with open(filename) as f:
            out_template_data = f.read()
            self.set_header("Content-Type", "application/octet-stream")
            return out_template_data


class DeliveryDatetimesHandler(ApiHandler):

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




