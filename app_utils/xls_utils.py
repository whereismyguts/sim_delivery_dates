from collections import defaultdict
import xlrd

from app.models.models import RegionDeliverySchedule
from app_utils.db_utils import create_dbsession


def okato_by_regname(regname):
    return {'МСК+МО': '46000000000'}[regname]


def load_delivery_slots(filepath):
    xls_data = _load_xlsx(filepath)[:2]
    # TODO CHECK data for uniq, regname
    subects_by_reg = defaultdict(set)
    RegionDeliverySchedule.db_session.rollback()
    for reg, subject, holidays, weekend, workdays, special in xls_data:
        if reg in subects_by_reg and subject in subects_by_reg[reg]:
            raise Exception('В одном регионе не должно быть одинаковых городов ({} - {})'.format(reg, subject))
        sh = RegionDeliverySchedule.query().get(
            region_id=okato_by_regname(reg),
            subject_name=subject,
        ) or RegionDeliverySchedule(
            region_id=okato_by_regname(reg),
            subject_name=subject,
        )
        sh.deleted = None
        sh.holidays = holidays
        sh.time_slots_weekend = weekend
        sh.time_slots_workdays = workdays
        sh.special_time_slots = special

        sh.validate_raw_data()

        RegionDeliverySchedule.db_session.add(sh)

    RegionDeliverySchedule.db_session.commit()


def _load_xlsx(filepath):
    results = []
    wb = xlrd.open_workbook(filepath)
    sheet = wb.sheet_by_index(0)

    for rownum in range(1, sheet.nrows):
        row_data = list(map(
            lambda r: str(r).strip(),
            sheet.row_values(rownum)
        ))
        results.append(row_data)
    return results


if __name__ == '__main__':
    load_delivery_slots('data/files/datetime_courder_slots_example.xlsx')