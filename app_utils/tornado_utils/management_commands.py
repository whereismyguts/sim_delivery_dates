# -*- coding: utf-8 -*-
import csv
import os
import os.path
import shutil
import traceback
import xlwt

from app_utils.db_utils import get_dbsession


class BaseManagementCommand(object):

    is_db_session_created = False
    is_redis_created = False

    def __init__(self, db_session=None, *args, **kwargs):
        if db_session is None:
            self.db_session = get_dbsession()
            self.is_db_session_created = True
        else:
            self.db_session = db_session
        self.db_session.db__repeat = True

    def __del__(self):
        if (
                self.db_session is not None and
                self.is_db_session_created
        ):
            self.db_session.close()
            self.db_session = None

    def handler(self, *args, **kwargs):
        try:
            response = self._handler(*args, **kwargs)
        except Exception as err:
            self.alarm.error(str(err))
            print(err)
            print(traceback.format_exc())
            raise
        return response

    def _handler(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _check_or_create_path(path):
        directory = os.path.split(path)[0]
        if not os.path.isdir(directory):
            os.makedirs(directory)
        return path

    @staticmethod
    def rmfile(path):
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as err:
            print("can't delete file: {}".format(path))
            print(err)
            return None
        return True

    @staticmethod
    def rmdir(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as err:
            print ("can't delete dir: {}".format(path))
            print (err)
            return None
        return True

    @staticmethod
    def get_dirs(path):
        dirs = []
        for item in os.listdir(path):
            if os.path.isdir(os.path.join(path, item)):
                dirs.append(item)
        return dirs

    @staticmethod
    def get_files(path, available_extensions=None):
        files = []

        if available_extensions is None:
            available_extensions = []
        elif isinstance(available_extensions, str):
            available_extensions = [available_extensions]

        for item in os.listdir(path):
            if os.path.isfile(os.path.join(path, item)):
                if available_extensions:
                    extension = item.rsplit('.')[-1]
                    if extension not in available_extensions:
                        continue
                files.append(item)
        return files

    @classmethod
    def _write_csv(cls, xls_file_path, xls_data, encoding='cp1251'):
        for sheet_name, rows in xls_data.items():

            if len(xls_data.items()) > 1:
                print('Sheets count is more than 1 ({})! Will use {} sheet for generating csv-report'.format(
                    xls_data.keys(),
                    sheet_name,
                ))
                # xls_file_path = xls_file_path.replace('.csv', '_{}.csv'.format(sheet_name))

            with open(xls_file_path, mode='w', encoding=encoding, errors='ignore') as csv_file:
                for row in rows:
                    csv_file.write(';'.join(map(lambda c: c and str(c) or '', row)) + '\n')
            break

    @classmethod
    def _write_xls(cls, xls_file_path, data):  # data = [ [ [], ... ], ... ]  xls, sheets, rows or { "sheet name": [ [], ... ], ... }
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
