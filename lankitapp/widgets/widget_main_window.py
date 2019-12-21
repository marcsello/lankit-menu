#!/usr/bin/env python3
from PySide2 import QtWidgets, QtCore, QtGui
from ui import Ui_MainForm

from utils import GameIndex, IndexVersionError
import json
import requests
import logging


class DictionaryModel(QtCore.QAbstractListModel):

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


class IndexThread(QtCore.QThread):
    load_success = QtCore.Signal(GameIndex)
    load_fail = QtCore.Signal(str)

    def run(self):

        index = GameIndex("https://luna.sch.bme.hu:8443/lankit")

        try:
            index.load()
            self.load_success.emit(index)

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logging.exception(e)
            self.load_fail.emit("Could not parse the response")

        except requests.exceptions.HTTPError as e:
            logging.exception(e)
            self.load_fail.emit(str(e))

        except IndexVersionError:
            logging.error("Index version mismatch")
            self.load_fail.emit("Index version is not supported")

        except Exception as e:
            logging.exception(e)
            self.load_fail.emit("Some magic error happened")

        return  # a kurva anyádat


class WidgetMainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)

        self.ui = Ui_MainForm()
        self.ui.setupUi(widget)

        self.ui.buttonLoadGame.setEnabled(False)
        self.ui.buttonLoadGame.clicked.connect(self.on_load_game_clicked)

        self.ui.listAviliableGames.doubleClicked.connect(self.on_load_game_clicked)

        self.statusBar().showMessage('Welcome to Lankit client!')

        indexMenu = self.menuBar().addMenu("Index")
        indexMenu.addAction("Reload index")
        indexMenu.triggered.connect(self.update_Index)

        self.index_thread = None
        self.update_Index()

    @QtCore.Slot()
    def update_Index(self):

        if self.index_thread:
            if not self.index_thread.isFinished:
                return

        self.statusBar().showMessage('Loading index...')
        self.index_thread = IndexThread(self)
        self.index_thread.load_success.connect(self.on_index_update_success)
        self.index_thread.load_fail.connect(self.on_index_update_fail)
        self.index_thread.start()

    @QtCore.Slot(GameIndex)
    def on_index_update_success(self, index: GameIndex):
        self.statusBar().showMessage('Index loaded!')

        self.ui.labelMaintainerValue.setText(index.maintainer)
        self.ui.labelHostNameValue.setText(index.host_friendlyname)

        model = DictionaryModel(index.getGameList())
        self.ui.listAviliableGames.setModel(model)

        self.ui.listAviliableGames.selectionModel().selectionChanged.connect(self.on_list_selection_changed)

        self.ui.buttonLoadGame.setEnabled(False)

    @QtCore.Slot(str)
    def on_index_update_fail(self, text: str):
        self.statusBar().showMessage('Index load failed')

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Failed to load index!")
        msg.setInformativeText(text)
        msg.setWindowTitle("Error")

        msg.exec()

    @QtCore.Slot()
    def on_list_selection_changed(self):
        self.ui.buttonLoadGame.setEnabled(True)

    @QtCore.Slot()
    def on_load_game_clicked(self):

        indexes = self.ui.listAviliableGames.selectedIndexes()

        if not indexes:
            return

        index = indexes[0]

        gameid = index.model().data(index, QtCore.Qt.ItemDataRole)  # kibaszott szaros buzi Qt hogy kurvára szarul van implementálva és nem lehet a kibaszos gecis item datát normálisan kiszopni abból a telibebaszott indexből mert különben azzal a szarrágó displaydata-val tér vissza, hoyg basszam szájba...

        logging.info("Loading game {}...".format(gameid))
