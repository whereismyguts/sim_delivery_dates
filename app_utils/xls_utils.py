import datetime
from collections import defaultdict
import xlrd
import xlwt

from app.models.models import RegionDeliverySchedule
from app_utils.db_utils import create_dbsession


def okato_by_regname(regname):
    return {'МСК+МО': '46000000000'}[regname]


def load_delivery_slots(filepath):
    xls_data = _load_xlsx(filepath)
    # TODO CHECK data for uniq, regname
    subects_by_okato = defaultdict(set)
    RegionDeliverySchedule.db_session.rollback()
    for okato, subject, holidays, weekend, workdays, special in xls_data:
        if '.' in okato:
            okato = okato.split('.')[0]
        if okato in subects_by_okato and subject in subects_by_okato[okato]:
            raise Exception('В одном регионе не должно быть одинаковых городов ({} - {})'.format(reg, subject))
        sh = RegionDeliverySchedule.query().get(
            region_id=okato,
            subject_name=subject,
        ) or RegionDeliverySchedule(
            region_id=okato,
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


def export_delivery_slots():
    delivery_data = RegionDeliverySchedule.query().filter(
        RegionDeliverySchedule.deleted == None
    ).order_by(
        RegionDeliverySchedule.region_id, RegionDeliverySchedule.subject_name
    ).all()

    rows = [
        [
            "Код ОКАТО (различается для Москвы и МО, Спб и ЛО)",
            "Название нас.пункта, должно быть уникально для региона",
            "Список дат через запятую, в которые доставка будет отключена: \"ДД.ММ.ГГ, ДД.ММ.ГГ, ...\"",
            "Список слотов через запятую которые будут доступны в сб и вс: \"ЧЧ:ММ-ЧЧ:ММ, ЧЧ:ММ-ЧЧ:ММ, ...\"",
            "Список слотов через запятую которые будут доступны с пн по пт: \"ЧЧ:ММ-ЧЧ:ММ, ЧЧ:ММ-ЧЧ:ММ, ...\"",
            "Указание особых еденичных дней с особым расписанием: Список в формате \"ДАТА_1 / СЛОТ_1, СЛОТ_2, ... , СЛОТ_X ; ДАТА_2/ СЛОТ_3, ... , СЛОТ_X; ... ; ДАТА_Х/ СЛОТ_X,...\""
        ],
        [
            "Окато",
            "Населенный пункт",
            "Нерабочие дни",
            "Расписание в выходные (сб, вс)",
            "Расписание в будние (пн-пт)",
            "Особые дни/часы"
        ],
    ]

    for sh in delivery_data:
        rows.append([
            sh.region_id,
            sh.subject_name,
            sh.holidays or '',
            sh.time_slots_weekend or '',
            sh.time_slots_workdays or '',
            sh.special_time_slots or '',
        ])
    filename = 'data/files/delivery_datetimes_{}.xlsx'.format(datetime.datetime.utcnow().timestamp())
    _write_xls(filename, [rows])
    print(filename)
    return filename


def _write_xls(xls_file_path, data):  # data = [ [ [], ... ], ... ]  xls, sheets, rows or { "sheet name": [ [], ... ], ... }
    wb = xlwt.Workbook()

    for sheet_num, sheet_data in enumerate(data):
        if isinstance(sheet_data, str):
            sheet_name = sheet_data
            sheet_data = data[sheet_name]
        else:
            sheet_name = str(sheet_num)

        ws = wb.add_sheet(sheet_name)

        for row_num, row in enumerate(sheet_data):
            for column_num, row_item in enumerate(row):
                ws.write(row_num, column_num, row_item)

    wb.save(xls_file_path)


def _load_xlsx(filepath):
    results = []
    wb = xlrd.open_workbook(filepath)
    sheet = wb.sheet_by_index(0)

    for rownum in range(2, sheet.nrows):
        row_data = list(map(
            lambda r: str(r).strip(),
            sheet.row_values(rownum)
        ))
        print(row_data)
        results.append(row_data)
    return results


if __name__ == '__main__':
    # load_delivery_slots('data/files/delivery_data.xls')
    export_delivery_slots()
    # load_delivery_slots('data/files/datetime_courder_slots_example.xlsx')