# -*- coding: utf-8 -*-

from app.models import AppDecBase
from app_utils.db_utils import create_dbsession, get_dbengine

class SyncDB(object):

    def __init__(self, db_engine=None, db_session=None):
        self.db_engine = db_engine or get_dbengine()
        self.db_session = db_session or create_dbsession()

    def handler(self):
        self.create_all_models()

    def create_all_models(self):
        AppDecBase.metadata.create_all(self.db_engine)
        self.db_session.commit()


def tables_report():
    dec_bases = [
        ('AppDecBase', AppDecBase),
    ]

    def write(a, f):
        f.write(str(a) + '\n')

    with open('/home/voloshchukan6_acc/tables.txt', 'w') as f:
        for dec_name, b in dec_bases:
            write(dec_name, f)
            for table in b.metadata.tables.keys():
                write(table, f)
                columns = b.metadata.tables[table].columns
                for c in columns:
                    write("{}:   # {}".format(c.name, c.type), f)
                write('------', f)


if __name__ == '__main__':
    SyncDB().handler()
