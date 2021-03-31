import datetime
import os

from app.handlers.api_handlers import ApiHandler
from app.models.models import RegionDeliverySchedule
from app_utils.xls_utils import load_delivery_slots


class UploadDeliveryDatetimesHandler(ApiHandler):

    def _get(self, *args, **kwargs):
        with open(self.XLS_TEMPLATE_PATH, 'rb') as fd:
            xls_template_data = fd.read()

        self.set_header("Content-Type", "application/octet-stream")
        return xls_template_data

    def _post(self, *args, **kwargs):
        utcnow = datetime.datetime.utcnow()

        file_name = 'delivery_dates{}.xlsx'.format(utcnow.strftime('%Y-%m-%dT%H:%M:%S'))
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


class DeliveryDatetimesHandler(ApiHandler):

    def _post(self, *args, **kwargs):
        region_id = self.data.get('region_id')  # '41000000000'
        local_time = self.data.get('local_time')  # '2021.02.14T16:10:00'
        subject = self.data.get('subject')
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

        delivery_times = dict()
        today = datetime.datetime.strptime(local_time, '%Y.%m.%dT%H:%M:%S')
        for i in range(1, 30):
            day = today + datetime.timedelta(days=i)
            slots = schedule.get_timeslots(day)
            if slots:
                delivery_times[day.strftime('%d.%m.%Y')] = slots
            if len(delivery_times) > 5:
                break
        return {
            "delivery_times": delivery_times,
            "result": 1,
            "error": 0,
        }




