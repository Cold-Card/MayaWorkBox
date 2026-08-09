# uncompyle6 version 3.8.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 3.10.2 (tags/v3.10.2:a58ebcc, Jan 17 2022, 14:12:15) [MSC v.1929 64 bit (AMD64)]
# Embedded file name: F:/Maya_Projects\sat\__init__.py
# Compiled at: 2016-11-26 20:41:47
from . import main
try:
    sat_win.close()
    sat_win.deleteLater()
except:
    pass

sat_win = main.MainWindow()
sat_win.show()
sat_win.connectSignals()
sat_win.start()
# global sat_win ## Warning: Unused global