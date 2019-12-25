#!/usr/bin/env python3
from PySide2 import QtCore


class DictModel(QtCore.QAbstractListModel):

    def __init__(self, source: dict):
        super().__init__()
        self._source = source
        self._ordered_items = list(self._source.items())

    def rowCount(self, parent):
        return len(self._ordered_items)

    def data(self, index, role):
        rownum = index.row()

        if role == QtCore.Qt.ItemDataRole:
            return self._ordered_items[rownum][0]

        if role == QtCore.Qt.DisplayRole:
            return self._ordered_items[rownum][1]
