#!/usr/bin/env python3
from PySide2 import QtWidgets, QtCore, QtGui
from ui import Ui_MainForm

from utils import GameIndex, IndexVersionError, kernel_parse, DictModel, DealerThread

from . import WidgetProgressWindow

import os
import json
import requests
import logging


class IndexThread(QtCore.QThread):
    load_success = QtCore.Signal(GameIndex)
    load_fail = QtCore.Signal(str)

    banner_downloaded = QtCore.Signal(bytes)

    def _get_index_url(self):

        kernel_cmdline = kernel_parse()

        if 'lankit_index' in kernel_cmdline.keys():
            return kernel_cmdline['lankit_index']

        if 'LANKIT_INDEX' in os.environ:
            return os.environ['LANKIT_INDEX']

        return None

    def run(self):

        index = GameIndex(self._get_index_url())

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

        # Load picture

        if index.banner_url:
            try:
                r = requests.get(index.banner_url)
                r.raise_for_status()

                self.banner_downloaded.emit(r.content)

            except Exception as e:
                logging.exception(e)

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

        dealerMenu = self.menuBar().addMenu("Dealer")  # TODO
        dealerMenu.addAction("Re-discover dealers")
        dealerMenu.triggered.connect(self.clear_dealer)

        self.center()
        self.setWindowTitle("Lankit menu")

        self.index_thread = None
        self.dealer_thread = None

        self.update_Index()

    def center(self):
        qRect = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qRect.moveCenter(centerPoint)
        self.move(qRect.topLeft())

    def update_load_button(self):

        self.ui.buttonLoadGame.setEnabled(
            bool(self.dealer_thread and self.dealer_thread.last_dealer) and
            bool(self.ui.listAviliableGames.selectedIndexes())
        )

    @QtCore.Slot()
    def clear_dealer(self):

        if self.dealer_thread:
            self.dealer_thread.clear()

        self.ui.labelDealerNameValue.setText('')
        self.update_load_button()

    @QtCore.Slot()
    def update_Index(self):

        if self.index_thread:
            if not self.index_thread.isFinished:
                return

            del self.index_thread

        if self.dealer_thread:  # cleanup dealer thing
            self.dealer_thread.stop()
            self.dealer_thread.wait()

            del self.dealer_thread
            self.dealer_thread = None

        self.ui.listAviliableGames.setModel(None)

        self.clear_dealer()

        self.statusBar().showMessage('Loading index...')
        self.index_thread = IndexThread(self)

        self.index_thread.load_success.connect(self.on_index_update_success)
        self.index_thread.load_fail.connect(self.on_index_update_fail)
        self.index_thread.banner_downloaded.connect(self.on_banner_downloaded)

        self.index_thread.start()

    @QtCore.Slot(GameIndex)
    def on_index_update_success(self, index: GameIndex):
        self.statusBar().showMessage('Index loaded!')

        self.ui.labelMaintainerValue.setText(index.maintainer)
        self.ui.labelHostNameValue.setText(index.host_friendlyname)

        model = DictModel(index.get_game_list())
        self.ui.listAviliableGames.setModel(model)

        self.ui.listAviliableGames.selectionModel().selectionChanged.connect(self.on_list_selection_changed)

        self.update_load_button()

        self.dealer_thread = DealerThread(self)
        self.dealer_thread.dealer_discovered.connect(self.on_dealer_discovered)
        self.dealer_thread.start()

    @QtCore.Slot(str)
    def on_index_update_fail(self, text: str):
        self.statusBar().showMessage('Index load failed')

        self.ui.listAviliableGames.setModel(None)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Failed to load index!")
        msg.setInformativeText(text)
        msg.setWindowTitle("Error")

        msg.exec()

    @QtCore.Slot(bytes)
    def on_banner_downloaded(self, data: bytes):

        if not data:
            return

        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)

        self.ui.labelBannerImage.height = self.ui.labelBannerImage.width() * (pixmap.width() / pixmap.height())
        self.ui.labelBannerImage.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))

    @QtCore.Slot(dict)
    def on_dealer_discovered(self, dealer: dict):
        self.ui.labelDealerNameValue.setText(dealer['fnm'])
        self.statusBar().showMessage('Dealer discovered!')

        self.update_load_button()

    @QtCore.Slot()
    def on_list_selection_changed(self):

        self.update_load_button()

    @QtCore.Slot()
    def on_load_game_clicked(self):

        indexes = self.ui.listAviliableGames.selectedIndexes()

        if not indexes:
            return

        index = indexes[0]

        gameid = index.model().data(index, QtCore.Qt.ItemDataRole)  # kibaszott szaros buzi Qt hogy kurvára szarul van implementálva és nem lehet a kibaszos gecis item datát normálisan kiszopni abból a telibebaszott indexből mert különben azzal a szarrágó displaydata-val tér vissza, hoyg basszam szájba...

        logging.info("Loading game {}...".format(gameid))
