import datetime

from app.models.models import ParseLogicMixin, DataParseError, TimeSlotParseError


class MockRegionDeliverySchedule(ParseLogicMixin):

    def __init__(self, *a, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def tear_up():
    return MockRegionDeliverySchedule(
        region_id='МСК+МО',
        subject_name='Москва',
        holidays='01.04.2021, 02.04.2021',
        time_slots_weekend='10:00-12:00, 13:00-17:00',
        time_slots_workdays='08:00-19:00',
        special_time_slots='30.03.2021 / 11:00-14:00, 15:00-17:00; 31.03.2021 / 17:00-19:00',
    )

class TestSuit():

    @staticmethod
    def test_0():
        print('ALL CORRECT TEST')

        sh = tear_up()
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

    @staticmethod
    def test_1():
        print('INVALID MARKUP TEST 1')

        sh = tear_up()
        sh.special_time_slots = '30.03.2021 \ 11:00-14:00, 15:00-17:00; 31.03.2021 / 17:00-19:00'
        passed = False
        try:
            sh.get_timeslots(datetime.datetime(2021, 3, 29))
        except DataParseError as e:
            print(e)
            passed = True
        assert(passed)

    @staticmethod
    def test_2():
        print('INVALID MARKUP TEST 2')

        sh = tear_up()
        sh.time_slots_workdays = '8:00-9:00'
        passed = False
        try:
            sh.get_timeslots(datetime.datetime(2021, 3, 29))
        except TimeSlotParseError as e:
            print(e)
            passed = True
        assert(passed)

    @staticmethod
    def test_3():
        print('EMPTY MARKUP TEST 1')

        sh = tear_up()
        sh.special_time_slots = ''
        sh.holidays = ''
        sh.time_slots_weekend = ''
        sh.time_slots_workdays = ''
        passed = True
        try:
            sh.get_timeslots(datetime.datetime(2021, 3, 29))
        except TimeSlotParseError as e:
            print(e)
            passed = False
        assert(passed)

if __name__ == '__main__':

    for test in filter(lambda method: 'test' in method, dir(TestSuit)):
        getattr(TestSuit, test)()