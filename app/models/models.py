# -*- encoding: utf-8 -*-

import datetime
import json
import re
import traceback

__all__ = ('RegionDeliverySchedule',)

from app.models import *


class TimeSlotParseError(Exception):
    pass


class DataParseError(Exception):
    pass


class ParseLogicMixin:

    WORKDAYS = [0, 1, 2, 3, 4]

    # def __init__(self, *args, **kwargs):
    #     super(RegionDeliverySchedule, self).__init__(*args, **kwargs)
    #     self.validate_raw_data()

    def validate_raw_data(self):
        # print('validate:', self.subject_name, self.region_id)
        self.parsed_holidays
        self.parsed_special_time_slots
        self.get_timeslots_from_raw(self.time_slots_workdays)
        self.get_timeslots_from_raw(self.time_slots_weekend)

    @staticmethod
    def parse_date(dt_string: str):
        return datetime.datetime.strptime(dt_string.strip(), '%d.%m.%Y').date()

    @staticmethod
    def parse_slot(slot_string: str):
        slot_string = slot_string.strip().replace(' ', '')
        if re.match('\d\d:\d\d-\d\d:\d\d', slot_string):
            return slot_string
        raise TimeSlotParseError('string "{}" is not matches slot pattern! (HH:MM-HH:MM)'.format(slot_string))

    @property
    def parsed_holidays(self):
        try:
            day_strings = self.holidays.split(',')
            if day_strings and all(day_strings):
                return list(map(self.parse_date, day_strings))
            else:
                return []
        except Exception as e:
            raise DataParseError('{}\n{}'.format(str(e), traceback.format_exc()))


    @property
    def parsed_special_time_slots(self) -> dict:
        slots_by_day = dict()
        if not (self.special_time_slots or '').strip():
            return {}
        try:
            for line in self.special_time_slots.split(';'):
                dt_str, slots_str = line.split('/')
                slots_by_day[self.parse_date(dt_str)] = list(map(self.parse_slot, slots_str.split(',')))
        except Exception as e:
            raise DataParseError('{}\n{}'.format(
                e, traceback.format_exc()
            ))

        return slots_by_day

    @classmethod
    def get_timeslots_from_raw(cls, raw):
        if str(raw or '').strip() == '':
            return []
        return list(map(cls.parse_slot, raw.split(',')))

    def get_timeslots(self, dt: datetime) -> list:

        date = dt.date()

        print(date)

        if date in self.parsed_holidays:
            return []

        if date in self.parsed_special_time_slots:
            return self.parsed_special_time_slots[date]

        if date.weekday() in self.WORKDAYS:
            return self.get_timeslots_from_raw(self.time_slots_workdays)
        else:
            return self.get_timeslots_from_raw(self.time_slots_weekend)


class RegionDeliverySchedule(ParseLogicMixin, RegionDeliveryScheduleDbModel):
    pass

