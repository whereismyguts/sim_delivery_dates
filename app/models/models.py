import datetime
import json
import re

from app.models.mock import MockModel

__all__ = ('RegionDeliverySchedule',)

TEST = False

from app.models import *

if TEST:
    DerriveClass = MockModel
else:
    DerriveClass = RealModel


class RegionDeliverySchedule(DerriveClass):

    WORKDAYS = [0, 1, 2, 3, 4]

    def __init__(self, *args, **kwargs):
        super(RegionDeliverySchedule, self).__init__(*args, **kwargs)
        self.validate_raw_data()

    def validate_raw_data(self):
        self.parsed_holidays
        self.parsed_special_time_slots
        map(self.parse_slot, self.time_slots_workdays.split(','))
        map(self.parse_slot, self.time_slots_weekend.split(','))

    @staticmethod
    def parse_date(dt_string: str):
        return datetime.datetime.strptime(dt_string.strip(), '%d.%m.%Y').date()

    @staticmethod
    def parse_slot(slot_string: str):
        slot_string = slot_string.strip().replace(' ', '')
        if re.match('\d\d:\d\d-\d\d:\d\d', slot_string):
            return slot_string
        raise Exception('string "{}" is not matches slot pattern! (HH:MM-HH:MM)'.format(slot_string))

    @property
    def parsed_holidays(self):
        try:
            day_strings = self.holidays.split(',')
            print('day_strings')
            print(day_strings)
            if day_strings and all(day_strings):
                return list(map(self.parse_date, day_strings))
            else:
                return []
        except Exception as e:
            # TODO DataParseError
            raise


    @property
    def parsed_special_time_slots(self) -> dict:
        slots_by_day = dict()
        try:
            for line in self.special_time_slots.split(';'):
                dt_str, slots_str = line.split('/')
                slots_by_day[self.parse_date(dt_str)] = list(map(self.parse_slot, slots_str.split(',')))
        except Exception as e:
            # TODO DATAPArseError
            raise

        return slots_by_day

    def get_timeslots(self, dt: datetime) -> list:
        date = dt.date()

        if date in self.parsed_holidays:
            return []

        if date in self.parsed_special_time_slots:
            return self.parsed_special_time_slots[date]

        if date.weekday() in self.WORKDAYS:
            return list(map(self.parse_slot, self.time_slots_workdays.split(',')))
        else:
            return list(map(self.parse_slot, self.time_slots_weekend.split(',')))


if __name__ == '__main__':

    sh = RegionDeliverySchedule(
        region_id='МСК+МО',
        subject_name='Москва',
        holidays='01.04.2021, 02.04.2021',
        time_slots_weekend='10:00-12:00, 13:00-17:00',
        time_slots_workdays='08:00-19:00',
        special_time_slots='30.03.2021 / 11:00-14:00, 15:00-17:00; 31.03.2021 / 17:00-19:00',
    )
    dates = [
        (datetime.datetime(2021, 3, 29), ['08:00-19:00']),
        (datetime.datetime(2021, 3, 30), ['11:00-14:00', '15:00-17:00']),
        (datetime.datetime(2021, 3, 31), ['17:00-19:00']),
        (datetime.datetime(2021, 4, 1), []),
        (datetime.datetime(2021, 4, 2), []),
        (datetime.datetime(2021, 4, 3), ['10:00-12:00', '13:00-17:00']),
        (datetime.datetime(2021, 4, 4), ['10:00-12:00', '13:00-17:00']),
    ]
    for date, result in dates:

        print(date, sh.get_timeslots(date), result)
        assert(sh.get_timeslots(date) == result)
